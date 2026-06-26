# -*- coding: utf-8 -*-
"""
腾讯视频V力值自动签到脚本
支持青龙面板、多账号、消息通知
环境变量: TXVIDEO_COOKIE (多账号用#或&分隔)
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
APP_VERSION = "v1.0.0"
APP_NAME = "腾讯视频V力值签到"

# 通知配置 - 从环境变量读取
SERVERCHAN_KEY = os.getenv("SERVERCHAN_KEY", "")  # Server酱推送key
PUSHPLUS_TOKEN = os.getenv("PUSHPLUS_TOKEN", "")  # PushPlus推送token
BARK_PUSH = os.getenv("BARK_PUSH", "")  # BARK推送

# 重试次数
MAX_RETRY = 3


class TxVideoCheckin:
    """腾讯视频签到类"""

    def __init__(self, cookie_str, user_index=1):
        self.cookie_str = cookie_str.strip()
        self.user_index = user_index
        self.session = requests.Session()
        self.msg_list = []
        self.user_name = ""
        self.total_score = 0

        # 设置默认请求头
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://v.qq.com",
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
            vappid = "11059694"
            vsecret = "5a05da2e836c42a59dc42b7d5c2f8b1d"

            # 从cookie中获取必要参数
            vqq_access_token = self.get_cookie_value("vqq_access_token")
            vqq_openid = self.get_cookie_value("vqq_openid")
            vqq_vuserid = self.get_cookie_value("vqq_vuserid")
            skey = self.get_cookie_value("p_skey") or self.get_cookie_value("skey") or ""

            if not vqq_access_token or not vqq_openid:
                self.log(f"【账号{self.user_index}】Cookie中缺少必要参数，跳过Session刷新")
                return False

            g_tk = self.calc_g_tk(skey) if skey else ""

            timestamp = int(round(time.time() * 1000))
            callback_id = random.randint(1000000, 9999999)

            refresh_url = (
                f"https://access.video.qq.com/user/auth_refresh?"
                f"vappid={vappid}&vsecret={vsecret}&type=qq&g_tk={g_tk}"
                f"&g_vstk={g_tk}&g_actk={g_tk}"
                f"&callback=jQuery{callback_id}_{timestamp}"
                f"&_={timestamp}"
            )

            headers = self.headers.copy()
            headers["Referer"] = "https://v.qq.com"

            response = self.session.get(refresh_url, headers=headers, timeout=15)

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
            else:
                self.log(f"【账号{self.user_index}】Session刷新失败，未获取到新的vusession")
                return False

        except Exception as e:
            self.log(f"【账号{self.user_index}】Session刷新异常: {str(e)}")
            return False

    def get_user_info(self):
        """获取用户信息"""
        try:
            vqq_vuserid = self.get_cookie_value("vqq_vuserid")
            if vqq_vuserid:
                self.user_name = f"用户{vqq_vuserid[-4:]}"
                return True
            return False
        except:
            return False

    def daily_checkin(self):
        """每日签到获取V力值"""
        self.log(f"【账号{self.user_index}】正在执行每日签到...")

        for retry in range(MAX_RETRY):
            try:
                timestamp = int(round(time.time() * 1000))
                sign_url = (
                    f"https://vip.video.qq.com/fcgi-bin/comm_cgi?"
                    f"name=hierarchical_task_system&cmd=2&_={timestamp}"
                )

                response = self.session.get(sign_url, headers=self.headers, timeout=15)
                response_text = response.text

                # 尝试解析JSON响应
                try:
                    # 可能是JSONP格式，提取JSON部分
                    json_match = re.search(r'\{.*\}', response_text)
                    if json_match:
                        data = json.loads(json_match.group())
                    else:
                        data = json.loads(response_text)
                except json.JSONDecodeError:
                    data = {"raw": response_text}

                # 处理响应
                ret = data.get("ret", -1)
                msg = data.get("msg", "未知错误")

                if ret == 0:
                    checkin_score = data.get("checkin_score", 0)
                    total_score = data.get("total_score", 0)
                    self.total_score = total_score

                    self.log(f"【账号{self.user_index}】✅ 签到成功！")
                    self.log(f"【账号{self.user_index}】获得V力值: +{checkin_score}")
                    self.log(f"【账号{self.user_index}】当前总V力值: {total_score}")
                    return True

                elif ret == -10006 or "Account Verify Error" in msg:
                    self.log(f"【账号{self.user_index}】❌ Cookie失效，请重新获取！")
                    return False

                elif ret == -2004:
                    self.log(f"【账号{self.user_index}】ℹ️ 今日已签到，无需重复签到")
                    # 尝试获取当前积分
                    self.total_score = data.get("total_score", 0)
                    if self.total_score:
                        self.log(f"【账号{self.user_index}】当前总V力值: {self.total_score}")
                    return True

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

    def run(self):
        """执行完整签到流程"""
        self.log(f"\n{'='*50}")
        self.log(f"【账号{self.user_index}】开始执行签到任务")
        self.log(f"{'='*50}")

        # 获取用户信息
        self.get_user_info()

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
        return

    # 分割多账号Cookie (支持#或&分隔)
    cookie_list = []
    if "#" in cookie_env:
        cookie_list = [c.strip() for c in cookie_env.split("#") if c.strip()]
    elif "&" in cookie_env:
        cookie_list = [c.strip() for c in cookie_env.split("&") if c.strip()]
    else:
        cookie_list = [cookie_env.strip()]

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
