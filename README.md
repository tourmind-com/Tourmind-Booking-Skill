# TourMind Booking Skill

TourMind ToB 酒店预订 Skill，支持搜索酒店、查询房型、验价锁房、创建预订、发起支付的完整工作流。

## 功能

- **搜索地区/酒店**：按城市名、地标、酒店名模糊搜索
- **搜索酒店列表**：按地区或指定坐标半径查询带距离的最低价候选酒店
- **查询酒店详情**：获取地址、星级、设施、政策、图片分类和静态房型信息
- **查询房型价格**：获取指定酒店的全部房型和实时价格
- **验价锁房**：锁定房价，确保预订前价格有效
- **创建预订**：提交订单，支持中英文姓名自动解析
- **查询预订**：随时查看订单状态和确认号
- **发起支付**：支持 Stripe、微信支付和支付宝；选择 Stripe 时会展示 Stripe 平台 3.5% 支付处理手续费说明

## 目录结构

```
├── SKILL.md              # Skill 主文件
├── README.md             # 本文档
├── EVAL_GUIDE.md         # 测试评估指南
├── TEST_REPORT.md        # 测试报告
├── evals/
│   └── evals.json        # 测试用例
├── references/
│   └── parameter_guide.md  # 参数参考（region_id、货币代码等）
└── scripts/
    └── validate_booking.py # 接口测试脚本
```

## 快速部署

### 1. 启动 Skill HTTP Server

```bash
go build -o chls-skill ./mcp/cmd/
nohup ./chls-skill -port :9061 > chls-skill.log 2>&1 &
```

所需环境变量与主业务服务相同（数据库、RPC 地址等）。

### 2. 安装 Skill

从 ToB Skill 仓库安装到 AI 客户端的技能目录，重启客户端或网关：

```bash
mkdir -p ~/.codex/skills/tourmind-booking
git clone git@github.com:tourmind-com/Tourmind-Booking-Skill.git ~/.codex/skills/tourmind-booking
```

无需额外配置 MCP server，Skill 直接通过 HTTP 调用 TourMind Skill API。

## API

**Base URL:** `http://39.108.114.224:9028`

| 接口 | 说明 |
|------|------|
| `POST /tob/skill/search_location` | 搜索地区或酒店 |
| `POST /tob/skill/search_hotels` | 搜索酒店列表 |
| `POST /tob/skill/get_hotel_detail` | 查询酒店静态详情 |
| `POST /tob/skill/query_room_rates` | 查询房型和价格 |
| `POST /tob/skill/check_room_availability` | 验价锁房 |
| `POST /tob/skill/create_booking` | 创建预订 |
| `POST /tob/skill/query_booking` | 查询预订 |
| `POST /tob/skill/cancel_booking` | 取消预订 |
| `POST /tob/skill/pay_order` | 发起支付 |

所有请求体需包含客户后台 `/user/home` 生成的 `token`。

## 使用示例

```
用户：帮我订一下东京的酒店，4月28日入住，4月30日离店，2人

机器人：好的，我来帮您搜索东京的酒店。
       找到以下 3 家酒店：
       1. 东京希尔顿酒店 — ¥1,280/晚
       2. 新宿华盛顿酒店 — ¥850/晚
       3. 东京皇家公园酒店 — ¥720/晚
       请问您选择哪家？

用户：第2家，标准间

机器人：已验价，标准大床房 ¥850/晚，2晚共 ¥1,700。
       请提供入住人姓名。

用户：张三

机器人：订单创建成功！订单号：TM20260428001
       请选择支付方式：Stripe、微信支付 或 支付宝

用户：Stripe

机器人：已发起 Stripe 支付，请点击链接完成支付：https://...
       Stripe 平台会按订单金额收取 3.5% 支付处理手续费；这是 Stripe 平台费用，不是酒店订单房费或 TourMind 额外订单费用。
```

## 参数参考

常用 region_id 见 [references/parameter_guide.md](references/parameter_guide.md)。

常用地区：北京=569，上海=2862，杭州=1328，深圳=3045，大阪=2446，东京=3263，曼谷=575
