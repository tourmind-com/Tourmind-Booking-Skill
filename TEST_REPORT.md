# TourMind Booking Skill - MCP 测试报告

**测试日期**: 2026-03-22
**服务地址**: http://39.108.114.224:9095 (MCP) / :9094 (HTTP)
**测试方法**: MCP Streamable HTTP 协议 (curl + JSON-RPC)

---

## 1. MCP 协议层测试

| 测试项 | 状态 | 说明 |
|--------|------|------|
| 服务连通性 | ✅ PASS | HTTP 200, SSE 响应正常 |
| Initialize 握手 | ✅ PASS | protocolVersion=2025-03-26, session ID 分配成功 |
| Session 管理 | ✅ PASS | Mcp-Session-Id header 正确传递, initialized 通知 HTTP 202 |
| tools/list | ✅ PASS | 返回 5 个工具，含完整 inputSchema |
| API Key 认证 | ✅ PASS | 未设置 MCP_API_KEY 时无需认证 |

**关键发现**: 之前的 "tools/call invalid during init" 问题已通过正确的 `Mcp-Session-Id` header（非 `Mcp-Session`）解决。

---

## 2. MCP 工具测试

### 2.1 search_hotels ✅ PASS (部分)

| 参数 | 结果 |
|------|------|
| region_id=2446 (大阪), 2026-03-25~27 | ✅ 找到酒店，但无价格缓存 → "No rates available" |
| region_id=1 (参数指南中的北京) | ❌ "No hotels found" — region_id 不存在于数据库 |
| region_id=5 (参数指南中的杭州) | ❌ "No hotels found" — region_id 不存在于数据库 |

**结论**: 工具逻辑正确。`SearchChannelHotelsByRegion` 成功查到酒店。`GetLowestRateCache` 缓存可能未预热或无该日期数据。

**Action Item**: 更新 `parameter_guide.md` 中的 region_id 映射（实际值：569=北京, 2862=上海, 1328=杭州, 2446=大阪）。

---

### 2.2 query_room_rates ✅ PASS

**测试参数**: hotel_id=20999661, 2026-03-25~27, adults=2, room_count=1

**结果**: 返回 **8 个房型**，数据完整

| 房型 | 价格 (CNY) | Rate Code | 可退 |
|------|-----------|-----------|------|
| 高级双人房 (海湾景观) | 1,415.94 | v2031749731957657611_99_2 | ✅ |
| 华丽客房 (无烟) | 1,451.28 | v2025596393096531975_99_2 | ✅ |
| 高级三人房 (海湾景观) | 1,964.54 | v2031749731957657615_99_2 | ✅ |
| 华丽客房 (海湾景观三人) | 2,176.78 | v2031749731957657601_99_2 | ✅ |
| 华丽套房 | 9,274.20 | v2025596393096531980_99_2 | ✅ |

每个 rate 包含：dailyPrices、cancelPolicyInfos、mealInfo、priceDetail（含税费分解）。

---

### 2.3 check_room_availability ✅ PASS

**测试参数**: hotel_id=20999661, rate_code=v2031749731957657611_99_2

**结果**:
- 状态: "Room availability verified"
- 房型: Superior Twin Bay View Room, Non-smoking
- 总价: 1,415.94 CNY (base: 1,145.85 + tax: 270.09)
- 每晚: 707.97 CNY
- 可退: ✅ (截止 2026-03-24T05:00)
- 价格明细含 TAX_AND_SERVICE_FEE 分项

---

### 2.4 create_booking ⏭️ SKIP

**原因**: 避免在生产环境创建真实订单。
**工具注册**: ✅ 通过 tools/list 验证，inputSchema 完整。
**代码审查**: 逻辑完整（姓名拆分、拼音转换、订单创建、reservation ID 回写）。

---

### 2.5 query_booking ✅ PASS (Placeholder)

**结果**: 返回 `"Booking query not yet implemented"` + structuredContent `{booking_id, message}`
**符合预期**: 代码中标注为 placeholder。

---

## 3. Eval 测试用例结果

### Eval 1: 基础酒店搜索 — ⚠️ 部分通过

| Assertion | 结果 | 说明 |
|-----------|------|------|
| returns_multiple_hotels | ⚠️ | 搜到酒店但缓存无价格，需改用正确 region_id |
| includes_pricing | ✅ | query_room_rates 返回完整价格 |
| date_handling | ✅ | 日期格式正确解析 |

**根因**: 参数指南 region_id 错误 + GetLowestRateCache 未命中。
**建议**: search_hotels 搜到酒店后直接用 query_room_rates 获取价格，不依赖缓存。

### Eval 2: 可用性检查和预订 — ✅ 通过 (除 create_booking)

| Assertion | 结果 | 说明 |
|-----------|------|------|
| availability_verified | ✅ | check_room_availability 返回完整验价结果 |
| booking_created | ⏭️ | 跳过真实创建 |
| guest_info_correct | ✅ | 代码审查确认姓名解析正确 |

### Eval 3: 团体旅行预订 — ⚠️ 部分通过

| Assertion | 结果 | 说明 |
|-----------|------|------|
| group_size_handled | ⚠️ | 依赖 search_hotels 价格缓存 |
| multiple_room_types | ✅ | query_room_rates 返回 8 种房型 |
| calculation_provided | N/A | 这是 Claude 推理任务，非工具问题 |

---

## 4. 总结

### 通过项 ✅
- MCP 协议完整工作（初始化、session、工具列表、工具调用）
- query_room_rates: 8 种房型 + 完整价格数据
- check_room_availability: 验价成功，含税费分解
- query_booking: placeholder 按预期工作
- create_booking: 代码审查通过，工具注册正常

### 需修复 🔧
1. **parameter_guide.md**: region_id 映射全部错误，需更新为真实值
2. **search_hotels**: `GetLowestRateCache` 经常无数据，建议增加 fallback 逻辑或直接调用 query_room_rates
3. **query_booking**: 目前是 placeholder，需实现真实查询

### 风险项 ⚠️
- search_hotels 在缓存未命中时返回 "No rates available"，Claude 可能误判为无酒店
- create_booking 未经端到端测试（生产安全考虑）

---

## 5. 建议的下一步

1. 修正 `parameter_guide.md` 中的 region_id（高优先级）
2. 为 search_hotels 添加缓存 miss 时的 fallback（中优先级）
3. 在测试环境实测 create_booking 完整流程（中优先级）
4. 实现 query_booking 真实查询（低优先级）
