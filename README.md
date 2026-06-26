# 腾讯视频V力值自动签到脚本

支持青龙面板的腾讯视频V力值每日自动签到脚本，支持多账号、Session自动刷新、消息推送通知。

## 功能特性

- ✅ **每日签到**：自动获取V力值
- 🔄 **Session刷新**：自动刷新 `vqq_vusession`，延长Cookie有效期
- 👥 **多账号支持**：支持多账号批量签到
- 📱 **消息推送**：支持Server酱、PushPlus、BARK等多种推送方式
- 🔁 **失败重试**：签到失败自动重试3次
- ⏰ **随机延迟**：模拟真实用户行为，降低风控风险

## 环境变量配置

### 必填变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `TXVIDEO_COOKIE` | 腾讯视频Cookie（多账号用 `#` 或 `&` 分隔） | `vqq_vusession=xxx; vqq_access_token=xxx;` |

### 可选变量（消息推送）

| 变量名 | 说明 |
|--------|------|
| `SERVERCHAN_KEY` | Server酱推送Key |
| `PUSHPLUS_TOKEN` | PushPlus推送Token |
| `BARK_PUSH` | BARK推送Key |

## Cookie获取方法

1. 浏览器打开 [https://v.qq.com](https://v.qq.com)
2. 使用QQ扫码或账号密码登录
3. 按 `F12` 打开开发者工具，切换到 **Network（网络）** 面板
4. 刷新页面，找到任意一个 `v.qq.com` 或 `video.qq.com` 的请求
5. 在请求头中找到 `Cookie` 字段，复制完整的Cookie值
6. 将Cookie值设置为环境变量 `TXVIDEO_COOKIE`

### 重要Cookie字段

- `vqq_vusession` - 视频用户会话标识（核心）
- `vqq_access_token` - QQ登录访问令牌
- `vqq_openid` - QQ开放平台用户ID
- `vqq_vuserid` - 腾讯视频用户ID
- `p_skey` / `skey` - 用于计算g_tk

## 青龙面板部署

### 方法一：脚本管理

1. 进入青龙面板 → 脚本管理 → 新建脚本
2. 文件名：`txvideo_checkin.py`
3. 将脚本内容粘贴进去并保存
4. 进入环境变量，添加 `TXVIDEO_COOKIE` 变量
5. 进入定时任务，添加任务：
   - 命令/脚本：`task txvideo_checkin.py`
   - 定时规则：`0 0 8 * * *`（每天早上8点）

### 方法二：订阅拉取

1. 进入青龙面板 → 订阅管理 → 新建订阅
2. 名称：腾讯视频签到
3. 类型：公开仓库
4. 链接：`https://github.com/Hayfan-wu/QL-Tx-video-Checkin`
5. 白名单：`txvideo_checkin.py`
6. 定时规则：`0 0 8 * * *`

## 多账号配置

多个账号的Cookie用 `#` 或 `&` 分隔：

```
TXVIDEO_COOKIE=cookie1#cookie2#cookie3
```

或

```
TXVIDEO_COOKIE=cookie1&cookie2&cookie3
```

## 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 方式一：环境变量
export TXVIDEO_COOKIE="你的cookie"
python txvideo_checkin.py

# 方式二：命令行参数
python txvideo_checkin.py "你的cookie"
```

## 消息推送配置

### Server酱

1. 访问 [https://sct.ftqq.com/](https://sct.ftqq.com/)
2. 微信扫码登录
3. 复制SendKey
4. 设置环境变量 `SERVERCHAN_KEY=你的SendKey`

### PushPlus

1. 访问 [http://www.pushplus.plus/](http://www.pushplus.plus/)
2. 微信扫码登录
3. 复制Token
4. 设置环境变量 `PUSHPLUS_TOKEN=你的Token`

### BARK

1. App Store下载BARK APP
2. 复制APP中的推送链接Key
3. 设置环境变量 `BARK_PUSH=你的Key`

## 注意事项

1. **Cookie安全**：Cookie等同于账号凭证，请勿泄露给他人
2. **有效期**：普通Cookie约3-7天失效；脚本会自动刷新Session，可延长至半年左右
3. **风控提示**：建议每天仅签到1次，避免频繁请求触发风控
4. **规则变更**：腾讯视频可能随时更改接口，脚本可能失效
5. **使用风险**：自动签到可能违反腾讯视频用户协议，请谨慎使用

## 免责声明

本脚本仅供学习交流使用，请勿用于商业用途。使用本脚本所产生的一切后果由使用者自行承担。

## 更新日志

### v1.0.0 (2026-06-26)
- 初始版本发布
- 支持每日签到获取V力值
- 支持Session自动刷新
- 支持多账号
- 支持多种消息推送方式
