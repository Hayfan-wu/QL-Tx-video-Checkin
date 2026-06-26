# 腾讯视频V力值自动签到脚本

支持青龙面板的腾讯视频V力值每日自动签到脚本，支持多账号、Session自动刷新、消息推送通知。

## 功能特性

- ✅ **每日签到**：自动获取V力值（新tRPC接口）
- 🔄 **Session刷新**：自动刷新 `vqq_vusession`，延长Cookie有效期
- 👥 **多账号支持**：支持多账号批量签到
- 📱 **消息推送**：支持Server酱、PushPlus、BARK等多种推送方式
- 🔁 **失败重试**：签到失败自动重试3次
- ⏰ **随机延迟**：模拟真实用户行为，降低风控风险
- 🎯 **多端模拟**：自动尝试iPad/PC/iPhone三种模式，提高成功率
- 🧹 **Cookie清理**：自动清理Cookie中的换行符和无效字符

## ⚠️ 重要说明

**2024年后腾讯视频加强了签到风控，新用户或异地登录可能需要图形验证码验证。**

### 解决方案

1. **手动签到一次（推荐）**：在手机APP或网页端手动签到一次，之后Cookie有效期内脚本可正常自动签到
2. **打码平台**：配置第三方打码平台自动识别验证码（需额外付费）
3. **常用IP**：使用常用登录地的IP运行脚本，降低触发验证的概率

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

### 可选变量（打码平台）

| 变量名 | 说明 |
|--------|------|
| `RROCR_KEY` | 人人打码Key |
| `TIANXING_KEY` | 天行打码Key |

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
- `vqq_refresh_token` - 刷新令牌

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

## 常见问题

### Q: 报错 InvalidHeaderError / Invalid leading whitespace 怎么办？

A: 这是因为Cookie中包含了换行符或特殊字符。
- v2.0.1+版本已自动修复此问题，脚本会自动清理Cookie
- 如仍有问题，请确保粘贴Cookie时是一行完整的字符串

### Q: 提示"您还未通过图形验证"怎么办？

A: 这是腾讯视频的风控机制。**请按以下步骤操作：**

1. **在腾讯视频APP或网页端手动签到一次**
   - 打开腾讯视频APP → 个人中心 → V力值 → 签到
   - 或网页端访问 https://film.video.qq.com/x/grade/ 签到

2. **重新获取Cookie（重要！）**
   - 手动签到后，不要关闭浏览器
   - 按F12 → Network → 刷新页面 → 复制新的Cookie
   - 将新Cookie更新到青龙面板的环境变量中

3. **确保IP一致**
   - 青龙服务器的IP最好是你常用的登录地IP
   - 异地IP更容易触发风控

4. **等待一段时间**
   - 有时候手动签到后需要等待几小时才会解除验证
   - 建议第二天再运行脚本

**注意：** 如果仍然需要验证，说明你的账号或IP被风控标记较严重，建议每天手动签到。

### Q: Cookie有效期多久？

A: 普通Cookie约3-7天失效。脚本会自动尝试刷新Session，成功的话可延长至数月。

### Q: 支持哪些签到任务？

A: 目前支持每日签到任务。观看视频、弹幕等任务需要真实用户行为，脚本无法模拟。

### Q: 会被封号吗？

A: 正常使用风险较低，但不保证绝对安全。建议每天只签到一次，不要频繁调用。

## 注意事项

1. **Cookie安全**：Cookie等同于账号凭证，请勿泄露给他人
2. **有效期**：普通Cookie约3-7天失效；脚本会自动刷新Session，可延长至半年左右
3. **风控提示**：建议每天仅签到1次，避免频繁请求触发风控
4. **规则变更**：腾讯视频可能随时更改接口，脚本可能失效
5. **使用风险**：自动签到可能违反腾讯视频用户协议，请谨慎使用

## 技术说明

- 接口：`trpc.new_task_system.task_system.TaskSystem/CheckIn`
- 协议：tRPC over HTTP
- 模拟端：iPad HD版（成功率最高）
- 语言：Python 3.6+

## 免责声明

本脚本仅供学习交流使用，请勿用于商业用途。使用本脚本所产生的一切后果由使用者自行承担。

## 更新日志

### v2.1.0 (2026-06-26)
- 新增多端模拟（iPad/PC/iPhone三种模式自动尝试）
- 新增设备指纹自动生成，提高通过率
- 优化错误提示，提供更详细的解决方案
- 增强Cookie清理功能
- 优化Session刷新逻辑

### v2.0.1 (2026-06-26)
- 修复Cookie中包含换行符导致的 InvalidHeaderError 报错
- 新增 clean_cookie 函数自动清理Cookie中的无效字符
- 优化青龙面板兼容性

### v2.0.0 (2026-06-26)
- 更新为最新tRPC接口架构
- 优化iPad端请求头模拟
- 增加图形验证码处理逻辑
- 支持用户昵称显示
- 修复中文编码问题

### v1.0.0 (2026-06-26)
- 初始版本发布
- 支持每日签到获取V力值
- 支持Session自动刷新
- 支持多账号
- 支持多种消息推送方式
