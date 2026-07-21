# TourMind Booking API and Field Reference

Use this reference when building TourMind requests, resolving POIs, selecting candidates, mapping images, or interpreting price, cancellation, tax and booking fields.

## Contents

1. [Shared request rules](#shared-request-rules)
2. [Date and occupancy rules](#date-and-occupancy-rules)
3. [Location and POI resolution](#location-and-poi-resolution)
4. [Endpoint contracts](#endpoint-contracts)
5. [Candidate verification and ranking](#candidate-verification-and-ranking)
6. [Display field mappings](#display-field-mappings)
7. [Cancellation, tax and payment semantics](#cancellation-tax-and-payment-semantics)
8. [Booking and order rules](#booking-and-order-rules)
9. [Errors and performance](#errors-and-performance)

## Shared request rules

- Base URL: `http://8.210.23.56:9028`
- Method: `POST`
- Content type: `application/json`
- Authentication: include `token` from `{baseDir}/skill_token.txt` in every request body.
- Send `region_id` and `hotel_id` as strings.
- Success: `{"ok": true, "data": {...}}`
- Failure: `{"ok": false, "error": "error description"}`

If the token file is absent or empty, ask the user for a newly generated Skill Token from `/user/home` before calling an endpoint. On HTTP 401 or an error containing `unauthorized`, delete the token file and stop until a new token is supplied.

## Date and occupancy rules

- Use `YYYY-MM-DD` for all API date values.
- Require checkout to be later than check-in.
- Resolve relative dates in the user's timezone and show the exact dates used.
- For a date without a year, use the next future occurrence and disclose the assumption.
- Default `room_count` to 1 when omitted.
- If `adults` is also omitted, default to 1 adult per room. Tell the user that the search uses 1 guest in 1 room and invite them to provide the guest count if multiple people will stay. Translate this notice into the user's language.
- Preserve any adult count the user already provided; never replace it with the default.
- `adults` means adults per room, not the total across all rooms.
- Do not call live-rate endpoints until location, check-in and check-out are known. Supply the default adult count when the user omitted it.

Currency values use ISO 4217 codes such as `CNY`, `USD`, `EUR`, `GBP` or `JPY`. Display the currency returned by the API; do not silently relabel it.

## Location and POI resolution

### Region mode

Resolve city and administrative-area names through `search_location`. Do not rely on a hardcoded region list when a live lookup is available.

### Nearby mode

`search_hotels` nearby mode requires all three fields:

```json
{
  "latitude": 22.518,
  "longitude": 113.943,
  "radius_km": 2
}
```

Never widen an explicit radius without permission.

### Google POI resolution

Use this flow for a landmark, station, ski area, address or business district:

1. Search the complete POI phrase with `search_location`.
2. Use the singular `data.place` returned by TourMind. The API selects the first Google Places result; do not ask the user to select another result in this version.
3. If the user supplied a radius, preserve it exactly. Otherwise use `place.recommended_radius_km`, currently 3 km.
4. Pass `place.latitude`, `place.longitude`, the radius, and `location_name=place.name` to `search_hotels`.
5. State `place.search_scope` when the default radius is used.
6. If no Google place exists, use an exact TourMind region match when available. Otherwise report that the location cannot be resolved.

Do not derive coordinates from model knowledge, use a hotel as a proxy center, or substitute a city center while describing it as the requested POI.

## Endpoint contracts

### `POST /tob/skill/search_location`

Request:

| Field | Type | Required | Meaning |
|---|---|---|---|
| `token` | string | yes | Skill Token |
| `keyword` | string | yes | City, district, POI, landmark or hotel phrase |

Response data:

- `regions[]`: `region_id`, names, `region_type`, `latitude`, `longitude`, country and hotel count.
- `hotels[]`: hotel identifiers and basic name/address/region fields.
- `place`: the first Google Places result selected by TourMind, including `place_id`, `name`, `formatted_address`, `latitude`, `longitude`, `types`, `source`, `recommended_radius_km` and `search_scope`.

For a nearby request, use `place` directly. The current API intentionally selects the first Google result.

### `POST /tob/skill/search_hotels`

Three location modes are supported:

| Mode | Location fields | Purpose |
|---|---|---|
| Region | `region_id` | Priced candidates for a city/region |
| Nearby | `latitude`, `longitude`, `radius_km` | Priced candidates around a coordinate |
| Keyword | `keyword` | Resolve a hotel or proxy coordinate; does not produce final live prices |

Priced-search fields:

| Field | Type | Required | Meaning |
|---|---|---|---|
| `check_in_date` | string | yes | `YYYY-MM-DD` |
| `check_out_date` | string | yes | `YYYY-MM-DD` |
| `adults` | integer | yes | Adults per room |
| `room_count` | integer | no | Default 1 |
| `lowest_price` | number | no | Candidate lower bound in CNY |
| `highest_price` | number | no | Candidate upper bound in CNY |
| `location_name` | string | priced searches | Resolved region or Google place name used to describe the result page |

The endpoint returns at most 20 hotels. Common fields include `hotel_id`, `hotel_name`, `hotel_name_cn`, `address`, `address_cn`, `hotel_image`, `star_rating`, `min_price`, `currency_code` and, in nearby mode, `distance_km`.

Priced searches also return `search_scope` and `presentation` with `type=text/html`, a temporary public `view_url`, and `expires_at`. Include the `view_url` in the user-facing response so the user can open the visual hotel list.

`min_price` is a recent cached candidate signal. It is not guaranteed for the requested occupancy, room count, meal, cancellation policy or continuous stay. Never present it as a live bookable price.

### `POST /tob/skill/get_hotel_detail`

Request: `token`, string `hotel_id`.

`data.hotel` may include:

| Group | Fields |
|---|---|
| Identity | `hotel_id`, `name`, `name_cn` |
| Location | `address`, `address_cn`, `latitude`, `longitude`, region fields |
| Contact and class | `telephone`, `star_rating`, country fields |
| Images | `hotel_image`, `hotel_images`, `image_groups` |
| Content | `amenities`, descriptions, check-in/out, policies, `fees` |

`data.rooms[]` may include `room_id`, names, `area_range`, `occupancy`, bed fields and `basic_room_image`. These are static room definitions, not live inventory.

Hero-image priority for a displayed hotel:

1. `hotel.hotel_image`
2. `image_groups` item labeled `Primary image`, preferring a valid `1000px`/largest `href`
3. first valid `hotel_images` item
4. no image message; never use an unrelated image

When the final list contains five hotels, call this endpoint for those five so the required hero image, address, facilities and fee disclosures can be rendered. Do not call it for all 20 unless a user constraint such as a required pool must be checked across the candidate pool or the user asks to view all results.

### `POST /tob/skill/query_room_rates`

Request:

| Field | Type | Required |
|---|---|---|
| `token` | string | yes |
| `hotel_id` | string | yes |
| `check_in_date` | string | yes |
| `check_out_date` | string | yes |
| `adults` | integer | yes |
| `room_count` | integer | no |

`data.room_types[]` contains room-level names, bed description, optional `basic_room_image` and `products[]`.

Each product represents a room/occupancy/meal/cancellation combination and contains:

```json
{
  "max_occupancy": 2,
  "meal_type": "1",
  "meal_count": 0,
  "cancellation_policy": {
    "type": "free_cancel_before_deadline",
    "free_cancel_deadline": "2026-11-01T10:00:00+08:00",
    "effective_non_refundable": false
  },
  "rate": {
    "rate_code": "rate-code",
    "currency": "CNY",
    "total_price": 2978,
    "per_night_price": 744.5,
    "payment_type": 1,
    "is_on_request": false,
    "stripe_payment_fee": {
      "fee_rate": 0.035,
      "fee_amount": 104.23,
      "payable_amount": 3082.23,
      "currency": "CNY"
    }
  }
}
```

Use only products whose occupancy and other hard requirements match the user. A non-empty product with `is_on_request=true` is a request/confirmation product, not immediate inventory; label it clearly.

Do not map numeric/string `meal_type` codes to breakfast, dinner or another meal without a documented mapping. `meal_count=0` may be shown as no included meal; when positive but the type is unknown, say `Meal included for {meal_count} guests; type not specified`.

The response also includes `presentation.view_url` and `presentation.expires_at`. The temporary room-rate page displays all returned room products and supports live price verification for a displayed `rate_code`. It does not create an order. After verification, the user can copy the checked quote and return to the authenticated AI conversation to continue booking.

### `POST /tob/skill/check_room_availability`

Request: `token`, string `hotel_id`, `rate_code`, dates, `adults`, `room_count`.

Use the selected `query_room_rates` rate code. The checked response may return a new rate code, price and cancellation details. Use the checked values—not the earlier query values—for booking.

In legacy `cancelPolicyInfos`, `refundable: true` means refundable/cancellable. `startDateTime` is the free-cancellation deadline; `amount` is the fee after that deadline, not evidence that the product is non-cancellable.

### `POST /tob/skill/create_booking`

Request fields:

| Field | Required by this skill | Source |
|---|---|---|
| `token` | yes | Token file |
| `hotel_id` | yes | Selected hotel |
| `rate_code` | yes | Latest availability check |
| `check_in_date`, `check_out_date` | yes | Confirmed dates |
| `guest_name` | yes | User's full legal name |
| `contact_email` | **yes** | User-supplied valid email |
| `adults`, `room_count` | yes | Confirmed occupancy |
| `currency`, `total_price` | yes | Latest availability check |

The backend may technically accept an omitted email, but this skill must not call `create_booking` without one. Do not offer a skip option. A basic plausibility check requires one `@`, non-empty local/domain parts and a domain containing a dot; do not overclaim deliverability validation.

Return `data.agent_ref_id` as the TourMind order number.

### `POST /tob/skill/query_booking`

Request: `token`, `agent_ref_id`.

Use for current order status and confirmation details. Do not use stale conversation state when the user supplies a different order number.

### `POST /tob/skill/cancel_booking`

Request: `token`, `agent_ref_id`. Confirm the exact order number before calling.

The response may include `status`, `cancel_fee`, `refund_amount` and `currency`.

### `POST /tob/skill/pay_order`

Request: `token`, `agent_ref_id`, and the public `payment_method` API value: `Stripe`, `微信支付` (WeChat Pay), or `支付宝` (Alipay).

There is no custom return URL. Return `pay_url` to the user. For Stripe, also show the returned order amount, 3.5% fee and estimated payable amount before starting payment.

## Candidate verification and ranking

Use all candidates needed for a fair top-five choice; do not merely display the first five cached-price rows.

1. Preserve the complete original `search_hotels` candidate pool. Exclude search-level hard failures, including explicit radius and star constraints, only from the recommendation pool; record all failed hard constraints on the original candidate.
2. Query live rates for remaining candidates in controlled batches.
3. Filter products by occupancy, room count, strict budget, requested room/meal and other hard fields.
4. Drop candidates with no matching live product only from the recommendation pool; retain their identifiers and `no matching live product` status in the original pool.
5. Treat `is_on_request=true` as supplier-confirmation inventory, not immediate availability. Exclude it when the user explicitly requires immediately bookable or real-time available inventory; otherwise rank it after `is_on_request=false` and label it `Inventory requires supplier confirmation`.
6. Resolve required facilities through hotel details when needed.
7. Apply the user's explicit sort first.
8. Default tie-break order: number/strength of verified preference matches, immediate bookability, distance, live stay total, cancellation flexibility.
9. Select five. If fewer qualify, show fewer and state why.

Generate each `Why it matches` statement from evidence that affected ranking. Good examples:

- `0.8 km from the search center; the closest bookable hotel in this set`
- `Lowest verified total for the four-night stay`
- `Meets the five-star requirement and has a verified pool`
- `Offers the requested twin room with free cancellation through November 1`

Do not use generic praise or cached price. If the user asks to view all returned results, show the complete original candidate pool, split into `Meets all hard constraints` and `Does not meet all hard constraints` sections, and state every exclusion reason for each non-match. Verify each additional hotel's live rate before quoting it and fetch static details needed by the same output template. A candidate with no matching live product must remain in the complete-pool view, but its price must read `No matching live room or quote`; never present it as a match or substitute cached `min_price`.

## Display field mappings

### Hotel list

| Display item | Source |
|---|---|
| Candidate count | `search_hotels.data.total` or returned array length |
| Distance | `search_hotels.hotels[].distance_km` |
| Name/star | Search result, confirmed by hotel detail when available |
| Address | `get_hotel_detail.hotel.address_cn`, then `address` |
| Hero image | Hotel-image priority described above |
| Room/price | Matching live product from `query_room_rates` |
| Cancellation | Matching product's `cancellation_policy` |
| Tax or fee note | Show only explicit tax or fee data returned by the API, or when the user asks |
| Match reason | Verified user constraint/preference fields only |

### Room details

Room image priority:

1. exact live `room_type.basic_room_image`
2. confidently matching static `rooms[].basic_room_image`
3. generic room gallery with an explicit non-correspondence label
4. no image message

Use `name_cn` when non-empty, otherwise `name`. Render an empty/`Others` name as `Other / room assigned at check-in`. Show bed, maximum occupancy, conservative meal text, per-night price, total price, cancellation and `is_on_request` status together.

## Cancellation, tax and payment semantics

Cancellation:

- `type=non_refundable` or `effective_non_refundable=true` → non-refundable.
- `type=free_cancel_before_deadline` → show the exact deadline and its returned timezone offset.
- Never remove or silently convert the timezone.

Tax and fees:

- `total_price` is the API's current room quote. Do not claim that it includes all destination or on-property taxes unless the API explicitly says so.
- Read `hotel.fees.mandatory` for city/resort/on-property charges and surface it only when the API returns explicit content.
- Do not notify the user that fee or tax data is absent, incomplete, or unknown unless the user specifically asks about taxes or fees.
- Do not add mandatory-fee prose numerically unless the API gives an unambiguous amount and charging basis.

Stripe:

- The 3.5% fee is Stripe payment processing, not room rate, hotel tax or a TourMind booking surcharge.
- Show it only when Stripe is being considered or selected.
- Use returned `fee_amount` and `payable_amount`; do not recompute when values are available.

## Booking and order rules

Guest names should match identification documents. The service handles Chinese and Latin-script names; do not promise a specific transliteration.

Before booking, confirm:

- exact hotel and room product;
- dates, occupancy and room count;
- latest checked total/currency and cancellation policy;
- full legal guest name;
- mandatory contact email.

Common order statuses:

| Status | Meaning |
|---|---|
| `UNPAID` | Created, awaiting payment |
| `PENDING` | Paid, waiting for hotel confirmation; do not ask the user to pay again |
| `CONFIRMED` | Confirmed by hotel |
| `CANCELLED` | Cancelled |
| `CONFIRM_FAILED` | Hotel confirmation failed |

## Errors and performance

| Error/symptom | Required handling |
|---|---|
| `unauthorized` / HTTP 401 | Delete token file and request a new token |
| No search candidates | Report the exact constraint set; offer changes without applying them |
| Candidates but no live products | State that hotels were found but none had matching live rooms |
| Budget-capped search empty | Optionally probe without budget only to diagnose over-budget inventory |
| Rate check failed | Re-run availability once for the selected rate; if still failed, report it |
| Booking creation failed | Report the error; do not retry with guessed guest/order data |

Batch rate/detail calls conservatively to avoid API throttling. Parallelize independent read-only queries in small batches, but keep booking, cancellation and payment operations sequential and explicitly confirmed.
