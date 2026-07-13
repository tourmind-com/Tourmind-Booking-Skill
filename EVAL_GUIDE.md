# TourMind Booking Skill - Eval 运行指南

按照 skill-creator 的最佳实践运行评估。

## 完整 Eval 流程

### 1️⃣ 启动 MCP 服务

```bash
cd chls
go run . -p 9094 -mcp-port 9095 -c 801
```

输出应该包含：
```
MCP server listening on :9095
Available tools: search_hotels, query_room_rates, check_room_availability, create_booking, query_booking
```

### 2️⃣ 创建工作目录结构

```bash
# 创建工作空间目录
mkdir -p tourmind-booking-workspace/iteration-1/{eval-1-basic-search,eval-2-booking,eval-3-group-travel}/{with_skill,without_skill}/outputs
```

### 3️⃣ 准备 Eval 元数据

为每个测试用例创建 `eval_metadata.json`（参考下方）

### 4️⃣ 并行运行测试

**With Skill 版本（3 个测试用例）：**

```bash
# 这应该通过 subagent 或 claude CLI 来完成
# 对于每个 eval，运行类似的命令：

claude -p <<'PROMPT'
You have access to the TourMind Booking Skill at: /path/to/skill/
Task: [INSERT EVAL PROMPT HERE]
Save outputs to: tourmind-booking-workspace/iteration-1/eval-1-basic-search/with_skill/outputs/
PROMPT
```

**Without Skill 基线版本：**

```bash
# 相同的提示，但不使用 skill
claude -p <<'PROMPT'
Task: [INSERT EVAL PROMPT HERE]
Save outputs to: tourmind-booking-workspace/iteration-1/eval-1-basic-search/without_skill/outputs/
PROMPT
```

### 5️⃣ 收集并生成查看器

```bash
# 运行评估聚合
cd tourmind-booking-workspace/iteration-1
python3 /path/to/skill-creator/scripts/aggregate_benchmark.py . --skill-name tourmind-booking

# 生成 HTML 查看器
nohup python3 /path/to/skill-creator/eval-viewer/generate_review.py . \
  --skill-name "tourmind-booking" \
  --benchmark benchmark.json \
  > /dev/null 2>&1 &

# 在浏览器中打开并审查结果
```

---

## Eval 测试用例

### Eval 1: 基础酒店搜索

**目的**: 验证区域搜索和费率查询功能

**eval_metadata.json:**
```json
{
  "eval_id": 1,
  "eval_name": "basic-hotel-search",
  "prompt": "I need to find hotels in Beijing for a corporate team of 4 people traveling March 25-27, 2026. Show me the 3 most affordable options and their room rates for standard rooms.",
  "assertions": [
    {
      "name": "returns_multiple_hotels",
      "description": "Search returns at least 1 hotel with complete details (id, name, price)"
    },
    {
      "name": "includes_pricing",
      "description": "Response includes room rates and currency information"
    },
    {
      "name": "date_handling",
      "description": "Correct dates used in search (March 25-27, 2026)"
    }
  ]
}
```

**预期输出**:
- ✅ 返回 1 个或多个北京酒店
- ✅ 包含价格和货币信息
- ✅ 显示标准房价格

---

### Eval 2: 可用性检查和预订

**目的**: 验证完整的预订工作流

**eval_metadata.json:**
```json
{
  "eval_id": 2,
  "eval_name": "availability-check-and-booking",
  "prompt": "I found hotel ID 12345 in Shanghai. Can you check if deluxe rooms are available for April 10-12, 2026 for 2 adults at the lowest rate? If available, create a booking for John Smith (john.smith@company.com, +86-10-1234567) for 1 deluxe room.",
  "assertions": [
    {
      "name": "availability_verified",
      "description": "Response confirms room availability status before booking"
    },
    {
      "name": "booking_created",
      "description": "Booking successfully created with confirmation ID"
    },
    {
      "name": "guest_info_correct",
      "description": "Booking includes correct guest name and contact information"
    }
  ]
}
```

**预期输出**:
- ✅ 检查可用性
- ✅ 创建预订
- ✅ 返回确认订单 ID
- ✅ 包含客人信息

---

### Eval 3: 团体旅行预订

**目的**: 验证处理大型群组的能力

**eval_metadata.json:**
```json
{
  "eval_id": 3,
  "eval_name": "group-travel-booking",
  "prompt": "I need to book accommodations for a 20-person corporate retreat. Search for hotels in Hangzhou available June 15-18, 2026. Find the best value option and show me room rates for standard and deluxe rooms so we can book a mix. How many total rooms would we need if we put 2 people per room?",
  "assertions": [
    {
      "name": "group_size_handled",
      "description": "Search correctly handles 20-person group size"
    },
    {
      "name": "multiple_room_types",
      "description": "Response compares at least 2 room types (standard + deluxe)"
    },
    {
      "name": "calculation_provided",
      "description": "Response includes calculation for room quantity (20/2 = 10 rooms)"
    }
  ]
}
```

**预期输出**:
- ✅ 搜索杭州酒店
- ✅ 显示多种房型
- ✅ 计算房间数量

---

## 调试常见问题

### MCP 连接问题

**症状**: `method "tools/call" is invalid during session initialization`

**原因**: 每个 HTTP 请求创建新的会话。MCP SDK 需要持续的 SSE 连接。

**解决方案**:
- 使用 MCP 客户端库（如 `@anthropic-ai/sdk` 的 MCP 支持）
- 或在服务器端修复会话管理

### 工具响应错误

**症状**: "Invalid region ID" 或 "No hotels found"

**调试步骤**:
1. 验证区域 ID（见 references/parameter_guide.md）
2. 检查日期是否为未来日期
3. 查看服务器日志中是否有底层错误

### 预订失败

**常见原因**:
- 客人信息格式不正确
- 价格代码过期
- 库存问题

**调试**:
```bash
# 检查服务器日志
tail -f /tmp/mcp_server.log
```

---

## Skill-Creator Eval 最佳实践

### Assertions 设计

好的 assertions 应该是：
- ✅ **客观且可验证** — 不依赖意见判断
- ✅ **具体** — 明确说明检查什么
- ✅ **独立** — 不互相依赖

### 测试用例选择

3 个用例应该覆盖：
1. **基础功能** — 核心工作流
2. **完整流程** — 多步操作
3. **边界情况** — 大规模/复杂场景

### 迭代改进

运行完 eval 后：
1. 审查输出和定量指标
2. 识别改进机会
3. 更新 SKILL.md 或工具
4. 进行下一轮 eval

---

## 相关文件

- `SKILL.md` — 主要 Skill 定义
- `evals/evals.json` — Eval 提示列表
- `references/parameter_guide.md` — 参数参考
- `scripts/validate_booking.py` — 响应验证脚本
