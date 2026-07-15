# TourMind Booking Skill - Parameter Reference

## Region IDs (HTS Regions)

**China:**
- `569` - Beijing (北京)
- `2862` - Shanghai (上海)
- `765` - Zhengzhou (郑州)
- `794` - Chongqing (重庆)
- `3045` - Shenzhen (深圳)
- `1328` - Hangzhou (杭州)
- `3489` - Wuhan (武汉)

**Asia:**
- `174` - Singapore (新加坡)
- `575` - Bangkok (曼谷)
- `2446` - Osaka (大阪)
- `3263` - Tokyo (东京)
- `20994` - Bali (巴厘岛)

**Europe:**
- `1918` - London (伦敦)
- `2481` - Paris (巴黎)
- `2736` - Roma (罗马)
- `514` - Berlin (柏林)

*Note: Region IDs are HTS-specific identifiers. Use `/static/v2/region/fuzzy?keyword=xxx` API to search for more regions.*

---

## Date Format Rules

All date parameters must use ISO 8601 format: **YYYY-MM-DD**

Examples:
- ✅ `2026-03-25` (March 25, 2026)
- ✅ `2026-12-31` (December 31, 2026)
- ❌ `03/25/2026` (incorrect format)
- ❌ `2026-3-25` (missing leading zero on month)
- ❌ `25-03-2026` (day-first format)

Minimum lead time varies by property but typically:
- Search: Can query current date or future
- Booking: Recommend 24-48 hours in advance

---

## Currency Codes

Standard ISO 4217 currency codes:
- `CNY` - Chinese Yuan (default for China region)
- `USD` - US Dollar
- `EUR` - Euro
- `GBP` - British Pound
- `JPY` - Japanese Yen

*The system normalizes all quotes to the configured default currency.*

---

## Hotel Pricing Tiers

Typical room type hierarchy by price:
1. **Standard Room** - Base price, typically no view
2. **Deluxe Room** - Enhanced amenities, partial view
3. **Suite** - Large space, premium amenities
4. **Executive Suite** - Top tier, concierge included

Prices vary significantly by:
- Region (tier-1 cities > tier-2 > tier-3)
- Season (peak season June-Aug, Dec; off-season Oct-Nov)
- Day of week (weekends typically higher)
- Lead time (last-minute bookings premium)

---

## Guest Name Handling

The system automatically parses full names into first/last components:

✅ **Supported formats:**
- "John Smith" → first: "John", last: "Smith"
- "李明" (Chinese) → Auto-converts to pinyin for booking
- "Jean-Claude Van Damme" → Handles hyphenated names
- "王 宏伟" → Handles space-separated Chinese names

⚠️ **Best practice:**
- Provide full legal name as it appears on ID
- For Chinese guests, use full Chinese name; system handles pinyin conversion
- For compound surnames, provide in standard format

---

## Error Messages

Common error responses and meanings:

| Error | Cause | Solution |
|-------|-------|----------|
| "Invalid region ID" | Region doesn't exist | Verify region_id with admin |
| "No hotels found" | Region exists but no inventory | Try different dates or region |
| "Invalid date format" | Date not YYYY-MM-DD | Reformat date string |
| "Room not available" | Sold out for selected dates | Try adjacent dates or different room type |
| "Rate check failed" | Rate no longer valid | Run check_room_availability again |
| "Booking creation failed" | Guest info invalid or system error | Verify guest name format |
| "unauthorized" | Token invalid, expired, or deleted | Regenerate Skill Token in customer portal `/user/home` |

---

## Order Status Reference

| Status | Chinese | Meaning |
|--------|---------|---------|
| `UNPAID` | 待支付 | Booking created, payment not yet made |
| `PENDING` | 已支付，待酒店确认 | Payment received, waiting for hotel to confirm |
| `CONFIRMED` | 已确认 | Hotel confirmed, booking is guaranteed |
| `CANCELLED` | 已取消 | Booking has been cancelled |
| `CONFIRM_FAILED` | 确认失败 | Hotel confirmation failed, contact support |

> **Important**: `PENDING` means the payment was successful and the hotel is processing confirmation — do NOT tell the user to pay again.

---

## Authentication

This skill supports Skill Token authentication only. Generate a Skill Token in the customer portal `/user/home`, store it locally in `{baseDir}/skill_token.txt`, and send it as `token` in every request.

Skill Tokens expire after 3 months and can be deleted by the customer. If a token is deleted or expired, the next API call should fail with `unauthorized`; remove the local token file and ask the user to generate a new one.

---

## Nearby Hotel Search

`search_hotels` supports two priced-candidate location modes:

| Mode | Required location fields | Meaning |
|------|--------------------------|---------|
| Region | `region_id` | Search from the configured region center using the existing region range |
| Nearby | `latitude`, `longitude`, `radius_km` | Search strictly within the explicit radius around the supplied coordinate |

Nearby request example:

```json
{
  "token": "<skill_token>",
  "latitude": 22.518,
  "longitude": 113.943,
  "radius_km": 2,
  "check_in_date": "2026-07-20",
  "check_out_date": "2026-07-21",
  "adults": 2,
  "room_count": 1
}
```

Each result includes `distance_km`. Never widen a user-provided radius without explicit approval. `min_price` is a recent cached candidate price, not an occupancy-specific guaranteed rate. Call `query_room_rates` for every candidate that will be compared or recommended.

Do not invent coordinates from model knowledge. Use coordinates returned by TourMind APIs. If no exact coordinate can be confirmed, explain that the requested distance cannot be guaranteed and ask for a more specific recognized location or coordinate.

## Room Rate Response

`query_room_rates` returns all room types. Each room type has `products`; each product represents:

- room type
- max occupancy
- meal type/count
- effective cancellation policy

Each product contains only the lowest-price RP for that product dimension:

```json
{
  "max_occupancy": 2,
  "meal_type": "1",
  "meal_count": 1,
  "cancellation_policy": {
    "type": "free_cancel_before_deadline",
    "free_cancel_deadline": "2026-05-01T12:00:00+08:00",
    "advanced_hour": 96,
    "effective_non_refundable": false
  },
  "rate": {
    "rate_code": "xxx",
    "currency": "CNY",
    "total_price": 1260,
    "per_night_price": 630,
    "payment_type": 0,
    "is_on_request": false,
    "stripe_payment_fee": {
      "fee_rate": 0.035,
      "fee_amount": 44.1,
      "payable_amount": 1304.1,
      "currency": "CNY",
      "notice": "使用 Stripe 支付时，Stripe 平台会按订单金额收取 3.5% 的支付处理手续费。该费用由 Stripe 平台收取，用于信用卡/支付网络处理，并非酒店订单房费、税费或 TourMind 额外订单费用。"
    }
  }
}
```

Use `product.rate.rate_code` for `check_room_availability`. Do not create a booking directly from `query_room_rates`; always re-check availability first.

`stripe_payment_fee` is an estimate for Stripe payment only. It does not change the room rate; it tells the customer the Stripe platform processing fee and estimated total payable amount if Stripe is selected.

## Payment Types

| payment_type | Meaning |
|--------------|---------|
| `4` | Stripe |
| `11` | WeChat Pay |
| `12` | Alipay |

`pay_order` returns `pay_url`, `request_id`, and `third_party_order_no`.

When `payment_type=4` (Stripe), the response also includes:

| Field | Meaning |
|-------|---------|
| `order_amount` | Hotel order amount before Stripe processing fee |
| `stripe_payment_fee.fee_rate` | Stripe platform processing fee rate: `0.035` |
| `stripe_payment_fee.fee_amount` | Estimated Stripe processing fee |
| `stripe_payment_fee.payable_amount` | Estimated total amount payable through Stripe |
| `stripe_payment_fee.notice` | Customer-facing explanation that the fee is charged by Stripe, not by the hotel order or TourMind |

## Workflow Decision Tree

```
User request for booking?
├─ City search? → search_location → search_hotels with region + dates
├─ Exact hotel? → search_hotels with keyword → query_room_rates with hotel_id
├─ Landmark/nearby? → resolve exact coordinate → search_hotels with coordinates + radius
│  └─ Got candidates → query_room_rates for each candidate being presented
│     └─ Compare rates → check_room_availability for specific room
│        └─ Available? → create_booking with guest info
│           └─ Success → query_booking for confirmation
│
├─ Check status? → query_booking with booking_id
│
├─ Cancel booking? → confirm booking_id, then cancel_booking
│
└─ Need confirmation? → query_booking
```

---

## Performance Notes

- **Search latency:** ~1-2 seconds (network dependent)
- **Rate queries:** ~500ms per hotel
- **Availability checks:** Real-time, ~300ms
- **Booking creation:** 2-5 seconds (includes confirmation)

For bulk operations, consider rate-limiting to avoid API throttling.
