# zaowuji-activator 造物集·官方激活工具

> 电脑端造物集激活码统一发售平台（仓库别名：PC-application-of-COC）

造物集公司官方桌面软件：**统一对接官网后端，为各类需要激活的软件/服务发送 RSA 激活请求**。
当官网产品线越来越多（coBrain 等），每个软件各自内置激活逻辑会重复且难维护——本工具统一负责：
机器码采集 → 创建订单 → 收款引导 → RSA 激活码签发/保存/核验。

> 授权闭环业务模式见官网仓库 `docs/激活码发售思路转变说明.md`：
> 官网只提供安装包下载，桌面端（本工具）驱动授权闭环。

## 激活闭环流程

```
用户选软件 → 采集机器码 → 创建订单 → 展示收款码引导转账
   → 管理员后台人工核验(collectionofcreations.uk/admin)
   → 提交机器码激活 → RSA 签发激活码 → 本地保存/展示/验签
```

## 功能特性

- 产品列表拉取（官方在售软件，含安装包直链）
- 本机机器码采集（主板/磁盘序列号 → SHA-256，回退 MAC+主机名）
- 创建购买订单 + 订单状态轮询
- **收款码拉取展示**（走官方 `GET /api/products/{id}/pay-qr` 接口）
- 激活码签发（机器码绑定）→ 本地加密保存（`~/.zaowuji/licenses.json`）→ 在线核验
- 零 GUI 依赖：tkinter（Python 自带），仅需 `requests`

## 快速开始

```bash
pip install -r requirements.txt   # requests>=2.31
python main.py                    # 启动图形界面
```

## 技术要点

- 机器码规范：`SHA-256(主板序列号|磁盘序列号)`，64 位 hex
- 激活码 = 服务端 RSA 私钥签名（SHA256withRSA），客户端可用公钥验签
- 机器码算法与 coBrain 桌面端统一后才能用于正式授权（当前为 v0.1 简化指纹）

## 后端 API 对照

| 接口 | 用途 |
|---|---|
| `GET /products` | 上架产品列表（软件选择；含 `downloadUrl` 安装包直链 / `payQrUrl` 收款码） |
| `GET /products/{id}/pay-qr` | **产品收款码图片**（二进制流，创建订单后展示） |
| `GET /license-key/public-key` | RSA 公钥（本地验签） |
| `POST /orders` | 创建订单 `{productId, contact, remark}` |
| `GET /orders/{orderNo}` | 订单状态轮询 |
| `POST /activations` | 激活 `{productId, machineCode, orderNo}` → 返回激活码 |
| `GET /activations?machineCode=` | 本机激活记录 |
| `GET /license-key/verify?code=` | 在线核验激活码 |

> 完整接口文档见官网仓库 `docs/API接口文档.md`。

## 目录结构

```
zaowuji-activator/
├── main.py           # tkinter 桌面端入口
├── api_client.py     # 后端 API 封装（ZaowujiAPI / ZaowujiError）
├── machine.py        # 机器码采集（wmic → SHA-256，含回退）
├── requirements.txt  # requests>=2.31
└── .gitignore        # __pycache__ 等
```
