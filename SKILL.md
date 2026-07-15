---
name: tourmind-booking
description: 酒店预订技能。**仅当**用户明确表达要预订酒店、查询房价、或确认已有订单时才触发（例如"帮我订酒店"、"查一下北京的酒店"、"我要预定房间"）。纯粹的旅游计划、问路、景点推荐等不触发此skill。进入工作流后，调用工具前必须先确认地点、入住日期、离店日期、人数这四项信息，缺少任何一项则先向用户询问补齐。在调用接口过程中如遇到任何错误，如实告知用户遇到了具体错误信息，不要自行推荐替代方案或编造信息。
metadata.openclaw: {"emoji": "🏨", "primaryEnv": "skill_token.txt"}
---

# TourMind Booking Skill

> **⚠️ 关键规则（必须遵守）**
>
> 1. **严禁从训练数据或记忆中编造酒店、房型、价格等信息。** 所有酒店相关数据必须且只能来自 HTTP 接口的实时返回结果。如果接口调用失败且重试后仍无法成功，如实告知用户遇到的错误，绝对不要凭记忆回答或自行推荐。
> 2. **接口返回 HTTP 401 或 `{"ok": false, "error": "unauthorized: ..."}` 时，说明 `token` 无效、已过期或已被删除，必须停止流程：删除 `{baseDir}/skill_token.txt`，提示用户在客户后台 `/user/home` 重新生成 Skill Token 后再继续。**
> 3. **正确解读取消政策字段。** `query_room_rates` 返回的是 `cancellation_policy`：`type=non_refundable` 或 `effective_non_refundable=true` 才能视为不可免费取消；`type=free_cancel_before_deadline` 时，`free_cancel_deadline` 是免费取消截止时间。`check_room_availability` 仍可能返回 `cancelPolicyInfos`，其中 `refundable: true` 表示该房型可退款/可取消，不得解释为“不可取消”。
> 4. **选择 Stripe 支付前必须告知用户手续费。** Stripe 平台会按订单金额收取 3.5% 支付处理手续费；这是 Stripe 平台处理信用卡/支付网络产生的费用，不是酒店房费、税费，也不是 TourMind 针对订单额外收取的费用。接口会返回 `stripe_payment_fee` 供展示。
> 5. **附近搜索必须严格遵守用户指定的距离。** 不得擅自扩大 `radius_km`，不得凭模型记忆编造地标坐标。`search_hotels` 返回的是带缓存最低价的候选酒店；必须继续调用 `query_room_rates`，才能向用户展示符合入住人数和房间数的真实可订产品。
> 6. **不得向终端用户展示内部接口字段或枚举值。** 介绍支付能力时只说明支持 Stripe、微信支付和支付宝，不得展示 `payment_type`、支付类型代码或 `4`、`11`、`12` 等内部值。仅当用户明确询问 API 接入、参数定义或调试信息时，才可解释技术字段；工具调用仍须在内部使用正确映射。

## API

**Base URL:** `http://39.108.114.224:9028`

所有接口均为 `POST`。请求体必须包含 `token` 鉴权字段，token 从 `{baseDir}/skill_token.txt` 读取。

### 接口列表

| 功能 | Path |
|------|------|
| 搜索地区/酒店 | `/skill/search_location` |
| 搜索酒店列表 | `/skill/search_hotels` |
| 查询酒店静态详情 | `/skill/get_hotel_detail` |
| 查询房型和价格 | `/skill/query_room_rates` |
| 验价锁房 | `/skill/check_room_availability` |
| 创建预订 | `/skill/create_booking` |
| 查询预订 | `/skill/query_booking` |
| 取消预订 | `/skill/cancel_booking` |
| 发起支付 | `/skill/pay_order` |

### 响应格式

成功：`{"ok": true, "data": {...}}`  
失败：`{"ok": false, "error": "错误描述"}`

### 调用方式（curl 示例）

```bash
# 搜索地区
curl -s -X POST -H "Content-Type: application/json" \
  "http://39.108.114.224:9028/skill/search_location" \
  -d '{"token": "<skill_token>", "keyword": "东京"}'

# 搜索酒店
curl -s -X POST -H "Content-Type: application/json" \
  "http://39.108.114.224:9028/skill/search_hotels" \
  -d '{"token": "<skill_token>", "region_id": "3263", "check_in_date": "2026-05-01", "check_out_date": "2026-05-03", "adults": 2, "room_count": 1}'

# 搜索指定坐标 2km 内的酒店
curl -s -X POST -H "Content-Type: application/json" \
  "http://39.108.114.224:9028/skill/search_hotels" \
  -d '{"token": "<skill_token>", "latitude": 22.518, "longitude": 113.943, "radius_km": 2, "check_in_date": "2026-05-01", "check_out_date": "2026-05-03", "adults": 2, "room_count": 1}'

# 查询酒店静态详情
curl -s -X POST -H "Content-Type: application/json" \
  "http://39.108.114.224:9028/skill/get_hotel_detail" \
  -d '{"token": "<skill_token>", "hotel_id": "12345"}'

# 查询房型
curl -s -X POST -H "Content-Type: application/json" \
  "http://39.108.114.224:9028/skill/query_room_rates" \
  -d '{"token": "<skill_token>", "hotel_id": "12345", "check_in_date": "2026-05-01", "check_out_date": "2026-05-03", "adults": 2, "room_count": 1}'

# 验价
curl -s -X POST -H "Content-Type: application/json" \
  "http://39.108.114.224:9028/skill/check_room_availability" \
  -d '{"token": "<skill_token>", "hotel_id": "12345", "rate_code": "xxx", "check_in_date": "2026-05-01", "check_out_date": "2026-05-03", "adults": 2, "room_count": 1}'

# 创建预订
curl -s -X POST -H "Content-Type: application/json" \
  "http://39.108.114.224:9028/skill/create_booking" \
  -d '{"token": "<skill_token>", "hotel_id": "12345", "rate_code": "xxx", "check_in_date": "2026-05-01", "check_out_date": "2026-05-03", "guest_name": "张三", "adults": 2, "room_count": 1, "total_price": 1260.00}'

# 查询预订
curl -s -X POST -H "Content-Type: application/json" \
  "http://39.108.114.224:9028/skill/query_booking" \
  -d '{"token": "<skill_token>", "agent_ref_id": "TM20260501001"}'

# 取消预订
curl -s -X POST -H "Content-Type: application/json" \
  "http://39.108.114.224:9028/skill/cancel_booking" \
  -d '{"token": "<skill_token>", "agent_ref_id": "TM20260501001"}'

# 支付
curl -s -X POST -H "Content-Type: application/json" \
  "http://39.108.114.224:9028/skill/pay_order" \
  -d '{"token": "<skill_token>", "agent_ref_id": "TM20260501001", "payment_type": 4}'
```

---

## Setup

调用任何接口前，必须先完成用户身份验证。

### Step 1 — Skill Token

1. 优先读取 `{baseDir}/skill_token.txt`。
2. 如果文件**不存在或为空** — 不要调用任何接口，告知用户：
   > "在开始之前，需要先验证你的身份。请在客户后台 `/user/home` 生成一个 Skill Token，并把 token 提供给我。Token 只在生成时可复制。"
   用户提供后保存到 `{baseDir}/skill_token.txt`，然后继续。
3. 如果文件**存在且有内容** — 请求体使用 `token` 字段，不再询问用户。
4. 如果接口返回 401 或 error 包含 `unauthorized` — 删除 `{baseDir}/skill_token.txt`，重新执行第 2 步。

---

## 接口参数说明

### /skill/search_location

| 参数 | 类型 | 说明 |
|------|------|------|
| token | string | 从 `{baseDir}/skill_token.txt` 读取 |
| keyword | string | 搜索关键词（城市名、地标、酒店名等） |

返回 `data.regions`（地区列表，含 `region_id`、`latitude`、`longitude`）和 `data.hotels`（酒店列表，含 `hotel_id`）。酒店名称模糊搜索可调用 `/skill/search_hotels` 的 `keyword` 模式，该模式返回酒店的 `latitude`、`longitude`，但不查询价格。

### /skill/search_hotels

| 参数 | 类型 | 说明 |
|------|------|------|
| token | string | 从 `{baseDir}/skill_token.txt` 读取 |
| region_id | string | 城市/地区搜索使用的地区 ID（如 `"3263"`）；与坐标模式二选一 |
| latitude | float | 附近搜索中心纬度；必须与 `longitude`、`radius_km` 一起传入 |
| longitude | float | 附近搜索中心经度；必须与 `latitude`、`radius_km` 一起传入 |
| radius_km | float | 搜索半径（公里），必须大于 0，属于不可擅自放宽的硬约束 |
| check_in_date | string | 入住日期 YYYY-MM-DD |
| check_out_date | string | 离店日期 YYYY-MM-DD |
| adults | int | 每间客房成人数 |
| room_count | int | 房间数（默认 1） |
| lowest_price | int | 最低价格（CNY，可选） |
| highest_price | int | 最高价格（CNY，可选） |

返回 `data.hotels`，最多 3 家价格最低的候选酒店。附近搜索结果包含 `distance_km`。`min_price` 来自近期酒店最低价缓存，只用于候选排序，不保证适用于指定人数、房间数或同一连续入住产品；必须对候选酒店调用 `query_room_rates` 后再向用户展示真实可订房型与价格。

### /skill/get_hotel_detail

| 参数 | 类型 | 说明 |
|------|------|------|
| token | string | 从 `{baseDir}/skill_token.txt` 读取 |
| hotel_id | string | 酒店 ID |

返回 `data.hotel` 和 `data.rooms` 静态信息：

- `hotel`：`hotel_id`、`name`、`name_cn`、`address`、`address_cn`、`telephone`、`country_code`、`country`、`region_id`、`region_name_long`、`region_name_long_cn`、`star_rating`、`latitude`、`longitude`
- 酒店图片：`hotel_image`、`hotel_images`、`image_groups`
- 酒店描述与设施：`amenities`、`location_desc`、`room_desc`、`policy_description`、`property_description`、`checkin`、`checkout`、`descriptions`、`amenities_hotel`、`amenities_room`、`policies`、`fees`
- `rooms`：`room_id`、`name`、`name_cn`、`area_range`、`occupancy`、`bed_type`、`bed_type_desc`、`bed_type_desc_cn`、`basic_room_image`

`image_groups` 按原始 `category + caption` 分组；每组的 `images` 包含 `hero_image` 和不同尺寸的 `links`，链接字段为 `method`、`href`、`local_href`。用户询问酒店地址、星级、设施、政策、入住时间、图片或静态房型信息，或者已选定酒店并希望进一步了解时调用本接口。不要对搜索结果中的每家候选酒店自动批量调用；不要把静态房型当作实时可售房型，库存和报价必须调用 `query_room_rates`。

### /skill/query_room_rates

| 参数 | 类型 | 说明 |
|------|------|------|
| token | string | 从 `{baseDir}/skill_token.txt` 读取 |
| hotel_id | string | 酒店 ID |
| check_in_date | string | 入住日期 |
| check_out_date | string | 离店日期 |
| adults | int | 每间客房成人数 |
| room_count | int | 房间数（默认 1） |

返回 `data.room_types`。每个房型包含 `room_type_code`、`name`、`name_cn`、`bed_type_desc` 和 `products`。每个 product 按「房型 + 最大入住人 + 餐食 + 取消政策」聚合，只返回该产品维度最低价 RP：`product.rate.rate_code`、`currency`、`total_price`、`per_night_price`、`payment_type`、`is_on_request`、`stripe_payment_fee`，以及 `cancellation_policy`。`stripe_payment_fee` 是用户选择 Stripe 支付时的预估手续费和预估支付总额，不改变房价本身。

### /skill/check_room_availability

| 参数 | 类型 | 说明 |
|------|------|------|
| token | string | 从 `{baseDir}/skill_token.txt` 读取 |
| hotel_id | string | 酒店 ID |
| rate_code | string | 来自 query_room_rates 的 rate_code |
| check_in_date | string | 入住日期 |
| check_out_date | string | 离店日期 |
| adults | int | 每间客房成人数 |
| room_count | int | 房间数（默认 1） |

返回 `data.room_types`，验价成功后的实时价格和 `rate_code`（可能与查询时不同），以及实时取消政策。创建订单必须使用验价返回的 `rate_code` 和价格。

### /skill/create_booking

| 参数 | 类型 | 说明 |
|------|------|------|
| token | string | 从 `{baseDir}/skill_token.txt` 读取 |
| hotel_id | string | 酒店 ID |
| rate_code | string | 来自 check_room_availability 的 rate_code |
| check_in_date | string | 入住日期 |
| check_out_date | string | 离店日期 |
| guest_name | string | 入住人姓名（系统自动解析中英文） |
| adults | int | 每间客房成人数 |
| room_count | int | 房间数（默认 1） |
| currency | string | 货币，默认 CNY |
| total_price | float | check_room_availability 返回的总价 |

返回 `data.agent_ref_id`（订单号）。

### /skill/query_booking

| 参数 | 类型 | 说明 |
|------|------|------|
| token | string | 从 `{baseDir}/skill_token.txt` 读取 |
| agent_ref_id | string | create_booking 返回的订单号 |

### /skill/cancel_booking

| 参数 | 类型 | 说明 |
|------|------|------|
| token | string | 从 `{baseDir}/skill_token.txt` 读取 |
| agent_ref_id | string | create_booking 返回的订单号 |

返回 `data.status`、`data.cancel_fee`、`data.refund_amount`（如有）、`data.currency`。取消前必须向用户确认要取消的订单号。

### /skill/pay_order

| 参数 | 类型 | 说明 |
|------|------|------|
| token | string | 从 `{baseDir}/skill_token.txt` 读取 |
| agent_ref_id | string | 订单号 |
| payment_type | int | 内部工具参数：`4` = Stripe，`11` = 微信支付，`12` = 支付宝；不得默认向终端用户展示 |
| return_url | string | 支付完成跳转地址（可选） |

返回 `data.pay_url`、`data.request_id`、`data.third_party_order_no`，将 `pay_url` 分享给用户完成支付。Stripe 支付会额外返回 `data.order_amount` 和 `data.stripe_payment_fee`，其中 `fee_amount` 是 Stripe 平台 3.5% 支付处理手续费，`payable_amount` 是预计支付总额。

---

## 地点搜索路由

调用搜索接口前，先判断用户提供的地点类型：

1. **城市或行政区域**：调用 `search_location`，从 `data.regions` 选择用户意图一致的地区，再使用 `region_id` 调用 `search_hotels`。
2. **具体酒店名称**：使用 `keyword` 调用 `search_hotels` 获取酒店候选；用户询问酒店详情时调用 `get_hotel_detail`，需要报价时调用 `query_room_rates`。
3. **地标、商圈、地址或“附近 N km”**：先通过 TourMind 接口结果获得准确坐标，再使用 `latitude`、`longitude`、`radius_km` 调用 `search_hotels`。不得使用模型记忆中的坐标。
4. 如果接口未返回可确认的准确坐标，必须告知用户当前无法严格保证距离范围，并请用户提供更明确的可识别地点或坐标；不得退化为城市 50km 搜索后声称结果位于地标附近。
5. 用户指定的距离是硬约束。没有结果时先告知用户，再询问是否扩大范围；获得明确同意后才能修改 `radius_km`。

## 预订流程

```
0. 识别地点类型      → 城市 / 酒店名 / 地标或附近范围
1. 搜索酒店候选      → search_location + search_hotels
2. 查询酒店详情（按需）→ 用户询问或选定酒店后调用 get_hotel_detail
3. 查询候选真实房价  → 对需要比较的候选酒店调用 query_room_rates
4. 验价锁房         → check_room_availability
5. 创建预订         → create_booking（无需手机号和邮箱）
6. 发起支付         → 询问支付方式后调用 pay_order
7. 查询订单         → query_booking（随时可查）
8. 取消订单         → 用户明确要求取消且确认订单号后调用 cancel_booking
```

---

## 注意事项

- **所有日期格式必须是 `YYYY-MM-DD`**
- **`region_id`、`hotel_id` 必须以字符串传入**（如 `"3263"`，不是 `3263`）
- **不得将 `search_hotels.min_price` 描述为最终可订价**；入住人数、房间数、餐食和取消政策以 `query_room_rates` 返回为准
- **不得擅自扩大用户指定的 `radius_km`**；附近搜索没有结果时必须先征得用户同意
- **`total_price` 使用 `check_room_availability` 返回的价格**，不要使用 `query_room_rates` 的价格
- **不要主动收集手机号和邮箱** — 预订流程不需要
- **create_booking 后询问支付方式**，面向用户只展示 Stripe、微信支付和支付宝；用户选择后，再在内部映射为对应的 `payment_type` 并调用 pay_order，不得向终端用户展示字段名或枚举值。如果用户选择 Stripe，必须先说明 Stripe 平台会收取 3.5% 支付处理手续费，该费用不是酒店订单费用或 TourMind 额外订单费用
- **取消订单前必须向用户确认订单号**，再调用 cancel_booking
- **解读取消政策时：`query_room_rates` 以 `cancellation_policy.type` 和 `effective_non_refundable` 为准；`check_room_availability` 中 `refundable: true` = 可退款/可取消，`startDateTime` = 免费取消截止时间，`amount` = 超过免费取消截止时间后的取消费，不代表不可取消**
- 接口调用出错时如实告知错误信息，不要编造数据或推荐替代方案

> **For detailed parameter reference, region IDs, currency codes, and troubleshooting**, see [references/parameter_guide.md](references/parameter_guide.md)
