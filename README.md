# zaowuji-activator 造物集·官方激活工具

造物集公司官方桌面软件：**统一对接官网后端，为各类需要激活的软件/服务发送 RSA 激活请求**。
当官网产品线越来越多（coBrain 等），每个软件各自内置激活逻辑会重复且难维护——本工具统一负责：
机器码采集 → 创建订单 → 收款引导 → RSA 激活码签发/保存/核验。

> 授权闭环业务模式见官网仓库 `docs/激活码发售思路转变说明.md`：
> 官网只提供安装包下载，桌面端（本工具）驱动授权闭环。

## 激活闭环流程

```
用户选软件 → 采集机器码 → 创建订单 → 展示收款码引导转账
   → 管理员后台人工核验(collectionofcreations.uk/admin)
   → 本工具「立即激活」→ 后端 RSA 签发激活码 → 本地保存 + 在线核验
```

## 对接的后端接口（base = https://collectionofcreations.uk/api）

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
├── main.py          # tkinter 桌面端（入口：python main.py）
├── api_client.py    # 后端 API 封装（requests）
├── machine.py       # 机器码采集（v0.1 简化指纹，TODO 对齐 coBrain 算法）
├── requirements.txt # requests
└── README.md
```

## 开发计划（v0.1 → v1.0）

- [x] v0.1 基础页面：产品列表 / 机器码 / 订单创建 / 激活 / 本地保存
- [ ] 机器码升级为稳定硬件指纹（主板序列号 + 磁盘 ID，与 coBrain 对齐）
- [ ] 内置 RSA 公钥离线验签（不依赖网络核验）
- [ ] 激活码管理：本机已激活软件列表 / 手动输入激活码
- [ ] 自动更新检查
- [ ] 打包 exe（PyInstaller）
