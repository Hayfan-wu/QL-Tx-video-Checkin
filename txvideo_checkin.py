# -*- coding: utf-8 -*-
"""
腾讯视频V力值自动签到脚本
支持青龙面板、多账号、消息通知
环境变量: TXVIDEO_COOKIE (多账号用#或&分隔)

更新说明:
- 2026-06-26: 更新为最新tRPC接口 (trpc.new_task_system)
- 支持图形验证码处理 (需配合打码平台或手动获取ticket)
"""

import os
import re
import sys
import json
import time
import random
import requests
from urllib.parse import quote

# 配置信息
APP_VERSION = "v2.0.1"
APP_NAME = "腾讯视频V力值签到"

# 通知配置 - 从环境变量读取
SERVERCHAN_KEY = os.getenv("SERVERCHAN_KEY", "")  # Server酱推送key
PUSHPLUS_TOKEN = os.getenv("PUSHPLUS_TOKEN", "")  # PushPlus推送token
BARK_PUSH = os.getenv("BARK_PUSH", "")  # BARK推送

# 打码平台配置 (可选)
RROCR_KEY = os.getenv("RROCR_KEY", "")  # 人人打码key
TIANXING_KEY = os.getenv("TIANXING_KEY", "")  # 天行打码key

# 重试次数
MAX_RETRY = 3

# 接口配置
SIGN_API = "https://vip.video.qq.com/rpc/trpc.new_task_system.task_system.TaskSystem/CheckIn?rpc_data={}"
TASK_LIST_API = "https://vip.video.qq.com/rpc/trpc.new_task_system.task_system.TaskSystem/ReadTaskList?rpc_data={}"
AUTH_REFRESH_API = "https://access.video.qq.com/user/auth_refresh"


def clean_cookie(cookie_str):
    """
    清理Cookie字符串，移除换行符、多余空格等无效字符
    解决 InvalidHeaderError 报错问题
    """
    if not cookie_str:
        return ""
    
    # 移除换行符和回车符
    cookie_str = cookie_str.replace("\n", "").replace("\r", "")
    # 移除制表符
    cookie_str = cookie_str.replace("\t", "")
    # 移除首尾空格
    cookie_str = cookie_str.strip()
    # 将多个连续空格替换为单个空格
    cookie_str = re.sub(r' +', ' ', cookie_str)
    # 清理分号前后的多余空格
    cookie_str = re.sub(r'\s*;\s*', '; ', cookie_str)
    # 移除首尾的分号和空格
    cookie_str = cookie_str.strip('; ')
    # 确保每个key=value对之间用 "; " 分隔
    parts = [p.strip() for p in cookie_str.split(';') if p.strip()]
    cookie_str = '; '.join(parts)
    
    return cookie_str


class TxVideoCheckin:
    """腾讯视频签到类"""

    def __init__(self, cookie_str, user_index=1):
        # 清理Cookie，移除换行符等无效字符
        self.cookie_str = clean_cookie(cookie_str)
        self.user_index = user_index
        self.session = requests.Session()
        self.msg_list = []
        self.user_name = ""
        self.total_score = 0
        self.checkin_score = 0

        # 设置默认请求头 - iPad端（成功率最高）
        self.headers = {
            "User-Agent": "Mozilla/5.0 (iPad; CPU OS 16_2 like Mac OS X) AppleWebKit/537.51.1 (KHTML, like Gecko) Mobile/11A465 QQLiveBrowser/8.8.10 AppType/HD WebKitCore/WKWebView iOS GDTTangramMobSDK/4.370.6 GDTMobSDK/4.370.6 cellPhone/Unknown iPad AppBuild/25828",
            "Referer": "https://film.video.qq.com/x/grade/?ovscroll=0&ptag=Vgrade.card",
            "Origin": "https://film.video.qq.com",
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Cookie": self.cookie_str
        }

    def log(self, msg):
        """记录日志"""
        print(msg)
        self.msg_list.append(msg)

    def get_cookie_value(self, key):
        """从cookie字符串中获取指定key的值"""
        pattern = rf'{key}=([^;]+)'
        match = re.search(pattern, self.cookie_str)
        if match:
            return match.group(1)
        return ""

    def calc_g_tk(self, skey):
        """计算g_tk值"""
        hash_val = 5381
        for char in skey:
            hash_val += (hash_val << 5) + ord(char)
        return hash_val & 2147483647

    def refresh_session(self):
        """刷新vqq_vusession，延长cookie有效期"""
        self.log(f"【账号{self.user_index}】正在刷新Session...")

        try:
            # 尝试多个vappid
            vappid_list = [
                ("11059694", "5a05da2e836c42a59dc42b7d5c2f8b1d"),
                ("101483052", ""),
            ]

            vqq_access_token = self.get_cookie_value("vqq_access_token")
            vqq_openid = self.get_cookie_value("vqq_openid")

            if not vqq_access_token or not vqq_openid:
                self.log(f"【账号{self.user_index}】Cookie中缺少必要参数，跳过Session刷新")
                return False

            for vappid, vsecret in vappid_list:
                timestamp = int(round(time.time() * 1000))
                callback_id = random.randint(1000000, 9999999)

                refresh_url = (
                    f"{AUTH_REFRESH_API}?"
                    f"vappid={vappid}"
                )
                if vsecret:
                    refresh_url += f"&vsecret={vsecret}"
                refresh_url += (
                    f"&type=qq&g_tk=&g_vstk=&g_actk="
                    f"&callback=jQuery{callback_id}_{timestamp}"
                    f"&_={timestamp}"
                )

                # 使用网页端UA刷新
                refresh_headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Referer": "https://v.qq.com",
                    "Cookie": self.cookie_str
                }

                response = self.session.get(refresh_url, headers=refresh_headers, timeout=15)

                # 从响应的Set-Cookie中获取新的vqq_vusession
                new_cookies = requests.utils.dict_from_cookiejar(response.cookies)

                if "vqq_vusession" in new_cookies:
                    new_vusession = new_cookies["vqq_vusession"]
                    self.log(f"【账号{self.user_index}】Session刷新成功！")

                    # 更新cookie中的vqq_vusession
                    if "vqq_vusession=" in self.cookie_str:
                        self.cookie_str = re.sub(
                            r'vqq_vusession=[^;]+',
                            f'vqq_vusession={new_vusession}',
                            self.cookie_str
                        )
                    else:
                        self.cookie_str += f"; vqq_vusession={new_vusession}"

                    self.headers["Cookie"] = self.cookie_str
                    return True

            self.log(f"【账号{self.user_index}】Session刷新失败，继续使用原有Cookie")
            return False

        except Exception as e:
            self.log(f"【账号{self.user_index}】Session刷新异常: {str(e)}")
            return False

    def get_user_info(self):
        """获取用户信息"""
        try:
            vqq_vuserid = self.get_cookie_value("vqq_vuserid")
            qq_nick = self.get_cookie_value("qq_nick")
            if qq_nick:
                from urllib.parse import unquote
                self.user_name = unquote(qq_nick)
            elif vqq_vuserid:
                self.user_name = f"用户{vqq_vuserid[-4:]}"
                return True
            return bool(vqq_vuserid)
        except:
            return False

    def solve_captcha(self, appid, business_id):
        """
        解决图形验证码
        返回: (ticket, randstr) 或 (None, None)
        """
        # TODO: 可集成第三方打码平台
        # 目前返回None，需要用户手动获取验证码ticket
        self.log(f"【账号{self.user_index}】需要图形验证，请手动获取验证码ticket")
        self.log(f"【账号{self.user_index}】AppID: {appid}, 业务: {business_id}")
        return None, None

    def daily_checkin(self):
        """每日签到获取V力值（新tRPC接口）"""
        self.log(f"【账号{self.user_index}】正在执行每日签到...")

        for retry in range(MAX_RETRY):
            try:
                response = self.session.get(SIGN_API, headers=self.headers, timeout=15)
                data = response.json()

                ret = data.get("ret", -1)
                msg = data.get("msg", "未知错误")

                if ret == 0:
                    # 签到成功
                    self.checkin_score = data.get("check_in_score", 0)
                    self.total_score = data.get("total_score", data.get("score", 0))

                    self.log(f"【账号{self.user_index}】✅ 签到成功！")
                    self.log(f"【账号{self.user_index}】获得V力值: +{self.checkin_score}")
                    if self.total_score:
                        self.log(f"【账号{self.user_index}】当前总V力值: {self.total_score}")
                    return True

                elif ret == -110009:
                    # 需要安全验证
                    security_verify = data.get("security_verify", {})
                    s_user_msg = security_verify.get("sUserMsg", "需要验证")
                    s_appid = security_verify.get("sAppId", "")
                    s_business_id = security_verify.get("sBusinessId", "")

                    self.log(f"【账号{self.user_index}】⚠️  {s_user_msg}")

                    # 尝试解决验证码
                    ticket, randstr = self.solve_captcha(s_appid, s_business_id)
                    if ticket and randstr:
                        # 使用验证码ticket重试
                        self.log(f"【账号{self.user_index}】使用验证码重试...")
                        # TODO: 将ticket加入请求头或参数
                        continue
                    else:
                        self.log(f"【账号{self.user_index}】❌ 无法自动完成验证，请手动签到一次后Cookie将恢复正常")
                        return False

                elif ret == -2004 or "already" in msg.lower():
                    # 已签到
                    self.log(f"【账号{self.user_index}】ℹ️  今日已签到，无需重复签到")
                    self.total_score = data.get("total_score", data.get("score", 0))
                    if self.total_score:
                        self.log(f"【账号{self.user_index}】当前总V力值: {self.total_score}")
                    return True

                elif ret == -10006 or "Account Verify Error" in msg:
                    # Cookie失效
                    self.log(f"【账号{self.user_index}】❌ Cookie失效，请重新获取！")
                    return False

                else:
                    self.log(f"【账号{self.user_index}】签到返回: ret={ret}, msg={msg}")
                    if retry < MAX_RETRY - 1:
                        self.log(f"【账号{self.user_index}】第{retry + 1}次重试...")
                        time.sleep(2)
                        continue
                    return False

            except Exception as e:
                self.log(f"【账号{self.user_index}】签到异常: {str(e)}")
                if retry < MAX_RETRY - 1:
                    self.log(f"【账号{self.user_index}】第{retry + 1}次重试...")
                    time.sleep(2)
                    continue
                return False

        return False

    def get_task_list(self):
        """获取任务列表"""
        try:
            response = self.session.get(TASK_LIST_API, headers=self.headers, timeout=15)
            data = response.json()
            if data.get("ret") == 0:
                return data.get("task_list", [])
            return []
        except:
            return []

    def run(self):
        """执行完整签到流程"""
        self.log(f"\n{'='*50}")
        self.log(f"【账号{self.user_index}】开始执行签到任务")
        self.log(f"{'='*50}")

        # 获取用户信息
        self.get_user_info()
        if self.user_name:
            self.log(f"【账号{self.user_index}】用户: {self.user_name}")

        # 刷新Session
        self.refresh_session()

        # 随机等待几秒，模拟真实用户行为
        time.sleep(random.uniform(1, 3))

        # 执行签到
        result = self.daily_checkin()

        self.log(f"{'='*50}")
        self.log(f"【账号{self.user_index}】签到任务结束")
        self.log(f"{'='*50}\n")

        return result

    def get_result_msg(self):
        """获取结果消息用于推送"""
        return "\n".join(self.msg_list)


def send_notification(title, content):
    """发送消息通知"""
    success = False

    # Server酱推送
    if SERVERCHAN_KEY:
        try:
            url = f"https://sctapi.ftqq.com/{SERVERCHAN_KEY}.send"
            data = {
                "title": title[:32],
                "desp": content
            }
            response = requests.post(url, data=data, timeout=10)
            if response.json().get("code") == 0:
                print("📱 Server酱推送成功")
                success = True
            else:
                print(f"📱 Server酱推送失败: {response.text}")
        except Exception as e:
            print(f"📱 Server酱推送异常: {str(e)}")

    # PushPlus推送
    if PUSHPLUS_TOKEN:
        try:
            url = "http://www.pushplus.plus/send"
            data = {
                "token": PUSHPLUS_TOKEN,
                "title": title,
                "content": content.replace("\n", "<br>"),
                "template": "html"
            }
            response = requests.post(url, json=data, timeout=10)
            if response.json().get("code") == 200:
                print("📱 PushPlus推送成功")
                success = True
            else:
                print(f"📱 PushPlus推送失败: {response.text}")
        except Exception as e:
            print(f"📱 PushPlus推送异常: {str(e)}")

    # BARK推送
    if BARK_PUSH:
        try:
            url = f"https://api.day.app/{BARK_PUSH}/{quote(title)}/{quote(content)}"
            response = requests.get(url, timeout=10)
            if response.json().get("code") == 200:
                print("📱 BARK推送成功")
                success = True
            else:
                print(f"📱 BARK推送失败: {response.text}")
        except Exception as e:
            print(f"📱 BARK推送异常: {str(e)}")

    return success


def main():
    """主函数"""
    print(f"\n🎉 {APP_NAME} {APP_VERSION}")
    print(f"⏰ 执行时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}\n")

    # 从环境变量获取Cookie
    cookie_env = os.getenv("TXVIDEO_COOKIE", "")

    # 如果环境变量没有，尝试从命令行参数获取
    if not cookie_env and len(sys.argv) > 1:
        cookie_env = sys.argv[1]

    if not cookie_env:
        print("❌ 未找到Cookie配置！")
        print("请设置环境变量 TXVIDEO_COOKIE")
        print("或在命令行后跟上cookie参数")
        print("\n获取Cookie方法:")
        print("1. 浏览器打开 https://v.qq.com 并登录QQ")
        print("2. 按F12打开开发者工具 -> Network(网络)")
        print("3. 刷新页面，找到任意请求，复制请求头中的Cookie")
        print("\n⚠️  注意：腾讯视频签到目前需要图形验证")
        print("   - 首次使用请手动签到一次，后续Cookie有效期内可正常使用")
        print("   - 或配置第三方打码平台自动识别验证码")
        return

    # 分割多账号Cookie (支持#或&分隔)
    cookie_list = []
    if "#" in cookie_env:
        cookie_list = [clean_cookie(c) for c in cookie_env.split("#") if c.strip()]
    elif "&" in cookie_env:
        cookie_list = [clean_cookie(c) for c in cookie_env.split("&") if c.strip()]
    else:
        cookie_list = [clean_cookie(cookie_env)]

    print(f"📋 共检测到 {len(cookie_list)} 个账号\n")

    all_results = []
    success_count = 0
    fail_count = 0

    # 逐个执行签到
    for i, cookie in enumerate(cookie_list, 1):
        checkin = TxVideoCheckin(cookie, i)
        result = checkin.run()

        if result:
            success_count += 1
        else:
            fail_count += 1

        all_results.append(checkin.get_result_msg())

        # 账号之间随机延迟
        if i < len(cookie_list):
            delay = random.uniform(3, 8)
            print(f"⏳ 等待 {delay:.1f} 秒后执行下一个账号...\n")
            time.sleep(delay)

    # 汇总结果
    summary = f"\n{'='*50}"
    summary += f"\n📊 签到汇总"
    summary += f"\n{'='*50}"
    summary += f"\n✅ 成功: {success_count} 个账号"
    summary += f"\n❌ 失败: {fail_count} 个账号"
    summary += f"\n📅 时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}"
    summary += f"\n{'='*50}\n"

    print(summary)

    # 发送通知
    if SERVERCHAN_KEY or PUSHPLUS_TOKEN or BARK_PUSH:
        title = f"腾讯视频签到结果: 成功{success_count}/失败{fail_count}"
        content = "\n".join(all_results) + summary
        send_notification(title, content)


if __name__ == "__main__":
    main()
