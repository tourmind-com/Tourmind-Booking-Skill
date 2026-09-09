# TourMind Booking API and Field Reference

Use this reference when building TourMind requests, resolving POIs, selecting candidates, mapping images, or interpreting price, cancellation, tax and booking fields.

## Contents

1. [Shared request rules](#shared-request-rules)
2. [Returned result-page URL language](#returned-result-page-url-language)
3. [Date and occupancy rules](#date-and-occupancy-rules)
4. [Location and POI resolution](#location-and-poi-resolution)
5. [Endpoint contracts](#endpoint-contracts)
6. [Candidate verification and ranking](#candidate-verification-and-ranking)
7. [Display field mappings](#display-field-mappings)
8. [Cancellation, tax and payment semantics](#cancellation-tax-and-payment-semantics)
9. [Booking and order rules](#booking-and-order-rules)
10. [Errors and performance](#errors-and-performance)

## Shared request rules

- Base URL: `https://api.tourmind.com`
- Skill version: read the exact `metadata.version` value declared in the YAML frontmatter of `SKILL.md`.
- Method: `POST`
- Content type: `application/json`
- Credential file: `{baseDir}/skill_token.txt` stores at most one current credential.
- Channel routing: no token or `uk_` uses ToC; `sk_` uses ToB. Prefix routing never replaces server authorization.
- Credential fields: ToC may use only `user_key`; ToB must use only `token`. Never send both fields or send either field to the opposite channel.
- Send the Skill version only as `current_version` to the active channel's update endpoint; do not attach it to hotel, rate, booking, order, cancellation, or payment requests.
- Send `region_id` and `hotel_id` as strings.
- `search_hotels.lowest_price` and `search_hotels.highest_price` **MUST be sent in CNY**. Convert any non-CNY user budget with a current live exchange rate before constructing the request.
- Success: `{"ok": true, "data": {...}}`
- Failure: `{"ok": false, "error_code": "...", "error": "error description"}`. `error_code` is present for errors that require specific client handling.
- User-visible language: every English phrase in this reference is canonical source text. Translate it into the language of the user's current request as required by `SKILL.md`. Preserve exact API field names, enum/code values, identifiers, currencies, variables, Markdown structure, and the meaning of returned data. Preserve URLs exactly except for the required result-page locale-path substitution below; translate user-facing summaries without altering facts.

Select the active channel before every workflow:

| Credential state | Channel | Credential in request body |
|---|---|---|
| File absent or empty | Public personal (ToC) | None for public read endpoints; an order operation must pause for sign-in |
| Begins with `uk_` | Personal (ToC) | `user_key` only on ToC endpoints that accept or require it |
| Begins with `sk_` | Business (ToB) | `token` on every ToB endpoint |
| Any other content | None | Do not call an endpoint; request a valid `uk_` or `sk_` token |

Call the update endpoint on the first use of this Skill in every new conversation and when an existing conversation resumes after at least 24 hours of inactivity. Do not call it before every workflow endpoint.

## Returned result-page URL language

Localize every returned hotel-list and hotel-detail `data.web_url` to the response language before showing it:

| Response language | URL locale |
|---|---|
| Chinese | `zh-CN` |
| English | `en-US` |
| Japanese | `ja` |
| Korean | `ko` |
| Spanish | `es` |
| Arabic | `ar` |
| Any other language | `en-US` |

Choose from the user's current request language, or an explicitly requested response language. Do not choose from the destination, hotel country, nationality, account type, or credential. For example, an English request about a hotel in the UAE uses `en-US`; an Arabic request uses `ar`.

Current result URLs encode this value as the locale path segment in `/zh-CN/skills/access`. Apply the mapping to `search_hotels.data.web_url`, `query_room_rates.data.web_url`, and each successful `batch_query_room_rates.data.results[].data.web_url` by replacing only that locale path segment. Preserve the scheme, host, remaining path, query string if present, parameter order, and the complete opaque fragment or access ticket exactly. This locale substitution is the only allowed URL change. If the expected locale segment is absent, leave the URL unchanged rather than constructing or guessing one. `web_url_expires_at` and `web_url_one_time` retain their original meaning and value.

No token or `uk_` request:

```json
{
  "current_version": "<declared-skill-version>"
}
```

Send it to `POST /skill/toc/check_skill_update` without `user_key`.

`sk_` request:

```json
{
  "token": "<sk-token>",
  "current_version": "<declared-skill-version>"
}
```

Send it to `POST /skill/tob/check_skill_update`.

The update endpoint may return:

```json
{
  "ok": true,
  "data": {},
  "skill_update": {
    "available": true,
    "display_to_user": true,
    "latest_version": "1.1.0",
    "message": "TourMind Booking 1.1.0 has been released with an improved hotel-image experience.",
    "release_source_url": "https://updates.tourmind.com/skills/booking/1.1.0"
  }
}
```

No-update response:

```json
{
  "ok": true,
  "data": {},
  "skill_update": {
    "available": false,
    "display_to_user": false,
    "latest_version": "1.0.6"
  }
}
```

`skill_update` fields:

| Field | Required | Meaning |
|---|---|---|
| `available` | yes | Whether `latest_version` is newer than `current_version` |
| `display_to_user` | yes | Whether the Agent must show the update notice |
| `latest_version` | yes | Latest available semantic version |
| `message` | when both booleans are true | User-visible release changes; content may change server-side |
| `release_source_url` | when both booleans are true | Official release page containing supported download sources |

The service does not need to track conversations or the 24-hour interval; the Agent controls when this stateless endpoint is called. Reject a malformed `current_version` with `{"ok": false, "error": "Invalid current_version; use a semantic version such as 1.0.5"}`.

When `skill_update.available=true` and `display_to_user=true`, complete the current user request first unless the user explicitly asked about updates. Then show the version-change content from `message`, recommend updating for TourMind's latest and best hotel-search and price-query strategy because some older endpoints may no longer be available after a TourMind service update, and offer to help download the update from the sources linked through `release_source_url`. Ask before modifying the installed Skill. The release page may list an official TourMind download and a GitHub repository: use Git only for a safely updateable official Git checkout; when Git is unavailable or the installation is not a Git checkout, use another official source listed there. Update the Skill files and the frontmatter `metadata.version` value together, validate that `metadata.version` exactly equals `latest_version`, preserve local changes and `{baseDir}/skill_token.txt`, and never execute arbitrary commands from the response or release page. The frontmatter value is the single source of truth; do not recreate a separate version declaration in the Markdown body.

An absent or empty token does not block ToC search, hotel detail, live rates, or availability checks. Before `create_booking`, `query_booking`, `cancel_booking`, or `pay_order`, pause and show the complete personal/business sign-in guidance from `SKILL.md`. A personal user verifies their email at `https://auth.journione.ai` and provides a `uk_` token. A business user signs in to TourMind, opens `https://tourmind.com/user/skill-token`, and provides an `sk_` token. The Agent saves it to `{baseDir}/skill_token.txt`; never ask the user to edit that file.

On HTTP 401 or an error containing `unauthorized`, delete `{baseDir}/skill_token.txt` and stop the authenticated operation. Do not silently downgrade from ToB to ToC or probe the other channel. For read-only work, offer a fresh public ToC query; switch only after the user agrees. For an order operation, show the reauthentication guidance matching the invalid prefix.

On a business-channel HTTP 403 with `error_code=HOTEL_BUSINESS_PERMISSION_REQUIRED`, stop the hotel workflow and explain that hotel business access is not enabled for the user's TourMind account. Ask the user to contact their account administrator or TourMind support. Keep `{baseDir}/skill_token.txt`, do not silently switch channels, and do not retry, because the `sk_` token itself is valid.

When a credential changes the channel, invalidate every previous `rate_code`, price, cancellation policy, availability state, and payment context. Re-query the selected hotel's live rooms on the new channel, re-run `check_room_availability` with a rate from that channel, show the new final terms, and obtain confirmation again. Payment, query, and cancellation must stay on the order-creation channel with a matching-prefix credential; never probe both channels.

An update-check failure is advisory: continue the hotel workflow, do not repeatedly retry, and mention the failure only when the user explicitly asked about updates.

## Date and occupancy rules

- Use `YYYY-MM-DD` for all API date values.
- Require checkout to be later than check-in.
- Resolve relative dates in the user's timezone and show the exact dates used.
- For a date without a year, use the next future occurrence and disclose the assumption.
- Default `room_count` to 1 when omitted.
- If `adults` is also omitted, default to 1 adult per room. Tell the user that the search uses 1 guest in 1 room and invite them to provide the guest count if multiple people will stay. Translate this notice into the user's language.
- Preserve any adult count the user already provided; never replace it with the default.
- `adults` means adults per room, not the total across all rooms.
- Default `children` to 0 and `children_ages` to `[]` when omitted.
- `children` and `children_ages` also describe one room. The age array length must equal `children`, and every age must be from 0 through 17.
- `room_count` repeats the same adult/child configuration for every room. Ask for the per-room occupancy when the user gives only totals for multiple rooms. Do not send `room_occupancies`; mixed configurations are unsupported.
- Do not call live-rate endpoints until location, check-in and check-out are known. Supply the default adult count when the user omitted it.

Currency values use ISO 4217 codes such as `CNY`, `USD`, `EUR`, `GBP` or `JPY`.

### Search currency and result display currency

- Search filtering is CNY-only: every `lowest_price` and `highest_price` request value **MUST be a CNY whole-stay total across all requested rooms**.
- For a non-CNY user budget, obtain a current live exchange rate immediately before the request. Never use model memory, an assumed rate, or an old rate from unrelated conversation context.
- For a per-room nightly budget, calculate `request_bound_CNY = source_bound × live_CNY_rate × night_count × room_count`.
- For an explicitly stated whole-trip total, calculate `request_bound_CNY = source_total × live_CNY_rate`; do not multiply by nights or rooms again.
- If a current live exchange rate cannot be obtained, do not guess. Ask for a CNY budget or obtain permission to continue without a price filter.
- For hotel-list and room-rate presentation, default to CNY when the current request is in Chinese. Default to USD for English and every other non-Chinese language. Use a different currency only when the user explicitly asks for it.
- Convert both per-night and whole-stay figures with one current live rate and label converted display amounts as approximate. Disclose the rate, source, and retrieval time. Never relabel an unconverted number.
- Display conversion does not change transaction data. Preserve the original returned amount and currency for `check_room_availability`, final booking confirmation, and `create_booking`.

## Location and POI resolution

### Region-first routing

Use `search_location` and inspect `regions[]` before `place` for cities, administrative areas, neighborhoods, business districts, large attractions, scenic areas, national parks, ski areas, resorts and islands, unless the user explicitly requires distance from a precise point or supplies a radius.

A region is high-confidence only when its name/full name strongly matches the complete destination phrase, its country/city context is compatible, and its `region_type` is reasonable. A positive `hotel_count`, when present, is strong support but not sufficient alone. Reject unrelated same-name results; ask one focused clarification if multiple plausible regions remain. Pass the selected string `region_id` and resolved name as `location_name`. Do not choose `place` merely because it exists when a reliable region match is available.

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

### Exact-point and broad-POI fallback

Use `place` for a station, address, specific entrance, compact landmark, map pin, explicit radius, or wording that clearly requires distance from an exact point. Confirm that the returned place name, address and country/city context match the request. Preserve an explicit radius exactly; otherwise use `place.recommended_radius_km`, currently 3 km. Pass `place.latitude`, `place.longitude`, the radius and `location_name=place.name` to `search_hotels`, then state the returned `search_scope`.

When a broad destination has no reliable region match, treat the matched `place` as a representative point rather than a boundary. With no explicit radius, begin at `place.recommended_radius_km` and probe the next larger values from `3, 5, 10, 20 km` until at least five candidates are available, the latest result reaches the 20-candidate limit, or 20 km has been searched. Merge all probe pools by string `hotel_id` and retain narrower-radius candidates. Disclose the final scope and expansion. If fewer than five candidates remain at 20 km, ask for a preferred entrance, visitor center or gateway town, or offer a wider search; do not silently jump to 50 km.

If neither a reliable region nor a matching place exists, report that the location cannot be resolved.

Do not derive coordinates from model knowledge, use a hotel as a proxy center, or substitute a city center while describing it as the requested POI.

## Endpoint contracts

### `check_skill_update`

Paths:

- Personal channel: `POST /skill/toc/check_skill_update`
- Business channel: `POST /skill/tob/check_skill_update`

Read-only, idempotent version check.

| Field | Type | Required | Meaning |
|---|---|---|---|
| `token` | string | ToB only | Required `sk_` business token; never send `user_key` to ToB |
| `current_version` | string | yes | Exact semantic version from the YAML frontmatter `metadata.version` field in `SKILL.md` |

ToC sends only `current_version`, even when a `uk_` credential is stored.

When no update is available, return `skill_update.available=false` and `display_to_user=false`. When an update is available, return the complete top-level `skill_update` object documented above.

### `search_location`

Paths:

- Personal channel: `POST /skill/toc/search_location`
- Business channel: `POST /skill/tob/search_location`

Request:

| Field | Type | Required | Meaning |
|---|---|---|---|
| `token` | string | ToB only | Required `sk_` business token; never send `user_key` to ToB |
| `keyword` | string | yes | City, district, POI, landmark or hotel phrase |

ToC is public and sends no credential for this endpoint.

Response data:

- `regions[]`: `region_id`, names, `region_type`, `latitude`, `longitude`, country and hotel count.
- `hotels[]`: hotel identifiers and basic name/address/region fields.
- `place`: the first Google Places result selected by TourMind, including `place_id`, `name`, `formatted_address`, `latitude`, `longitude`, `types`, `source`, `recommended_radius_km` and `search_scope`.

Apply the routing rules above: use a reliable region for destination-area lodging intent, and use `place` for exact-point or explicit-radius intent. The current API exposes one Google result, so validate it against the request before using it.

### `search_hotels`

Paths:

- Personal channel: `POST /skill/toc/search_hotels`
- Business channel: `POST /skill/tob/search_hotels`

ToB requires `token` containing the stored `sk_` credential. ToC is public; when a stored `uk_` credential exists, include it as `user_key` only if the endpoint contract accepts it. A personal credential is never required merely to search or obtain a result link.

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
| `children` | integer | no | Children per room; default 0 |
| `children_ages` | integer[] | no | One age from 0–17 for each child in one room |
| `lowest_price` | number | no | **MUST be a CNY total** for the entire stay across all requested rooms; never a nightly amount. Convert a non-CNY budget with a current live exchange rate before sending. |
| `highest_price` | number | no | **MUST be a CNY total** for the entire stay across all requested rooms; never a nightly amount. Convert a non-CNY budget with a current live exchange rate before sending. |
| `location_name` | string | priced searches | Resolved region or Google place name used to describe the result page |

Price-bound normalization is mandatory:

- If the user's bound is not CNY, obtain a current live exchange rate and first convert it with `bound_CNY = source_bound × live_CNY_rate`.
- Convert a per-room nightly bound with `request_bound_CNY = bound_CNY × night_count × room_count`.
- `night_count` is the number of nights between `check_in_date` and `check_out_date`.
- Convert each supplied lower and upper bound independently. If the user supplies only one bound, send only that converted bound.
- If the user explicitly supplies a whole-trip total, convert it to CNY when necessary but do not multiply it again.
- Treat an ordinary hotel price range without explicit trip-total wording as per room per night, disclose that assumption, and ask only when the surrounding context makes the basis genuinely unclear.

Example: one room from September 1 through September 4 is three nights. For a requested CNY 300–400 per-room nightly range, send:

```json
{
  "check_in_date": "2026-09-01",
  "check_out_date": "2026-09-04",
  "room_count": 1,
  "lowest_price": 900,
  "highest_price": 1200
}
```

For two rooms with the same dates and nightly range, the bounds become `lowest_price=1800` and `highest_price=2400`. These request fields filter cached candidates by whole-stay bounds; they do not replace live product verification through `query_room_rates` or a successful `batch_query_room_rates` item.

The endpoint returns at most 20 hotels. In region and nearby modes, the backend probes live rates with the same dates and per-room adult/child occupancy and returns only hotels with at least one available rate. Keyword mode does not run this probe. Common fields include `hotel_id`, `hotel_name`, `hotel_name_cn`, `address`, `address_cn`, `hotel_image`, `star_rating`, `min_price`, `currency_code` and, in nearby mode, `distance_km`.

Priced searches may also return `data.search_scope`, `data.web_url`, `data.web_url_expires_at` and `data.web_url_one_time`. When present, apply **Returned result-page URL language** and include the localized `data.web_url` in the user-facing response. The link can be opened repeatedly until `data.web_url_expires_at` when `data.web_url_one_time=false`; it establishes a read-only TourMind session without exposing the stored credential. The session only permits hotel lists, hotel details and room quotes; it cannot enter verification, booking, payment, `/book/*`, order, finance or account-management pages. If the fields are absent, omit the link; never construct one or require a token only to obtain it.

`min_price` is a recent cached candidate signal. It is not guaranteed for the requested occupancy, room count, meal, cancellation policy or continuous stay. Never present it as a live bookable price.

### `get_hotel_detail`

Paths:

- Personal channel: `POST /skill/toc/get_hotel_detail`
- Business channel: `POST /skill/tob/get_hotel_detail`

Request: string `hotel_id`; ToB additionally requires `token` containing the stored `sk_` credential. ToC is public and sends no credential.

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

### `query_room_rates`

Paths:

- Personal channel: `POST /skill/toc/query_room_rates`
- Business channel: `POST /skill/tob/query_room_rates`

Request:

| Field | Type | Required |
|---|---|---|
| `token` | string | ToB only; required `sk_` token |
| `user_key` | string | ToC optional when a stored `uk_` exists and the endpoint accepts it |
| `hotel_id` | string | yes |
| `check_in_date` | string | yes |
| `check_out_date` | string | yes |
| `adults` | integer | yes |
| `room_count` | integer | no |
| `children` | integer | no; children per room |
| `children_ages` | integer[] | no; one 0–17 age per child in one room |

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

Do not map numeric/string `meal_type` codes to breakfast, dinner or another meal without a documented mapping. `meal_count=0` may be shown as no included meal; when positive but the type is unknown, use the localized equivalent of `Meal included for {meal_count} guests; type not specified`.

The response may also include `data.web_url`, `data.web_url_expires_at` and `data.web_url_one_time`. The link can be opened repeatedly until `data.web_url_expires_at` when `data.web_url_one_time=false`. The linked TourMind page displays the hotel and returned room quotes in read-only mode. Apply **Returned result-page URL language**, preserve it with that exact hotel, and show it directly below the hotel's hero image using the localized label equivalent of `[View hotel details]`. Apart from the required locale-path substitution, preserve the URL exactly; never show the original image URL as a separate link and never substitute the hotel-list `search_hotels.data.web_url`. It does not support verification, booking, payment, `/book/*`, order management, finance or account management. Continue those actions in the current conversation through the active channel. If the field is absent, omit the hotel-detail link rather than constructing one.

An empty live result is HTTP 200 with `data.room_types=[]` and `data.reason=no_matching_live_room`. Do not treat it as a system failure.

### `batch_query_room_rates`

Paths:

- Personal channel: `POST /skill/toc/batch_query_room_rates`
- Business channel: `POST /skill/tob/batch_query_room_rates`

Use this endpoint to query multiple candidate hotels under one shared stay and per-room occupancy configuration. ToB requires `token` containing the stored `sk_` credential. ToC is public; when a stored `uk_` credential exists, include it as `user_key` only if the endpoint contract accepts it.

| Field | Type | Required |
|---|---|---|
| `token` | string | ToB only; required `sk_` token |
| `user_key` | string | ToC optional when a stored `uk_` exists and the endpoint accepts it |
| `hotel_ids` | string[] | yes; 1–20 hotels |
| `check_in_date` | string | yes |
| `check_out_date` | string | yes |
| `adults` | integer | yes; per room |
| `room_count` | integer | no; default 1 |
| `children` | integer | no; per room |
| `children_ages` | integer[] | no; one 0–17 age per child in one room |

Within each request, the server uses a fixed four-worker pool and preserves input order. A client may run up to three `batch_query_room_rates` requests concurrently when multiple batches are required; never exceed three concurrent requests. Each request still accepts at most 20 hotel IDs. Do not add client-side concurrency around individual hotels within a batch. Top-level `ok=true` means the batch completed; inspect each item independently. Abbreviated response:

```json
{
  "ok": true,
  "data": {
    "results": [
      {"hotel_id": "23059757", "ok": true, "data": {"total": 1}},
      {"hotel_id": "999999999", "ok": false, "reason": "hotel_not_found", "error": "hotel not found"}
    ],
    "summary": {"total": 2, "matched": 1, "empty": 0, "failed": 1}
  }
}
```

`matched` counts hotels with products, `empty` counts successful `no_matching_live_room` results, and `failed` counts per-hotel errors. The documented rate-query `reason` codes apply to each `data.results[]` item independently. Keep successful items when another item fails. Each successful item may include that hotel's read-only `data.web_url`; apply **Returned result-page URL language** before showing it. Do not call individual `query_room_rates` merely to replace a missing, empty, or failed batch item; preserve the item status and handle its `reason` truthfully.

### `check_room_availability`

Paths:

- Personal channel: `POST /skill/toc/check_room_availability`
- Business channel: `POST /skill/tob/check_room_availability`

Request: string `hotel_id`, `rate_code`, dates, `adults`, `room_count`, `children`, and `children_ages`. Occupancy fields retain the same per-room meaning. ToB additionally requires `token` containing the stored `sk_` credential. ToC is public and sends no credential.

Use the selected rate code from `query_room_rates` or a successful `batch_query_room_rates` item. The checked response may return a new rate code, price and cancellation details. Use the checked values—not the earlier query values—for booking.

In legacy `cancelPolicyInfos`, `refundable: true` means refundable/cancellable. `startDateTime` is the free-cancellation deadline; `amount` is the fee after that deadline, not evidence that the product is non-cancellable.

### `create_booking`

Paths:

- Personal channel: `POST /skill/toc/create_booking`
- Business channel: `POST /skill/tob/create_booking`

Request fields:

| Field | Required by this skill | Source |
|---|---|---|
| `user_key` | ToC only; yes | Stored `uk_` credential |
| `token` | ToB only; yes | Stored `sk_` credential |
| `hotel_id` | yes | Selected hotel |
| `rate_code` | yes | Latest availability check |
| `check_in_date`, `check_out_date` | yes | Confirmed dates |
| `guest_name` | yes | User's full legal name |
| `contact_email` | **yes** | User-supplied valid email |
| `adults`, `room_count`, `children`, `children_ages` | yes | Confirmed per-room occupancy; use 0 and `[]` when there are no children |
| `currency`, `total_price` | yes | Latest availability check |

The backend may technically accept an omitted email, but this skill must not call `create_booking` without one. Do not offer a skip option. A basic plausibility check requires one `@`, non-empty local/domain parts and a domain containing a dot; do not overclaim deliverability validation.

Return `data.agent_ref_id` as the TourMind order number.

### `query_booking`

Paths:

- Personal channel: `POST /skill/toc/query_booking`
- Business channel: `POST /skill/tob/query_booking`

Request: `agent_ref_id`, plus `user_key` containing `uk_` for ToC or `token` containing `sk_` for ToB.

Use for current order status and confirmation details. Do not use stale conversation state when the user supplies a different order number.

### `cancel_booking`

Paths:

- Personal channel: `POST /skill/toc/cancel_booking`
- Business channel: `POST /skill/tob/cancel_booking`

Request: `agent_ref_id`, plus `user_key` containing `uk_` for ToC or `token` containing `sk_` for ToB. Confirm the exact order number and order-creation channel before calling.

The response may include `status`, `cancel_fee`, `refund_amount` and `currency`.

### `pay_order`

Paths:

- Personal channel: `POST /skill/toc/pay_order`
- Business channel: `POST /skill/tob/pay_order`

Request: `agent_ref_id`, the public `payment_method` API value, and `user_key` containing `uk_` for ToC or `token` containing `sk_` for ToB. Supported payment values are `Stripe`, `微信支付` (WeChat Pay), and `支付宝` (Alipay).

There is no custom return URL. Return `pay_url` to the user. For Stripe, also show the returned order amount, 3.5% fee and estimated payable amount before starting payment. Disclose that once charged, the Stripe processing fee is non-refundable even if the booking is later cancelled within the hotel's free-cancellation period, and obtain the user's explicit acknowledgement before calling the payment endpoint.

## Candidate verification and ranking

Use all candidates needed for a fair top-five choice; do not merely display the first five cached-price rows.

1. Preserve the complete original `search_hotels` candidate pool. Exclude search-level hard failures, including explicit radius and star constraints, only from the recommendation pool; record all failed hard constraints on the original candidate.
2. Split the remaining candidates into batches of at most 20 hotel IDs and call `batch_query_room_rates`. Run one request when one batch is sufficient; when multiple batches are required, run no more than three requests concurrently. Process each item independently and retain partial successes. Use `query_room_rates` when only one hotel needs rates; do not use it merely to replace a missing, empty, or failed batch item.
3. Filter products by occupancy, room count, strict budget, requested room/meal and other hard fields.
4. Drop candidates with no matching live product only from the recommendation pool; retain their identifiers and `no matching live product` status in the original pool.
5. Treat `is_on_request=true` as supplier-confirmation inventory, not immediate availability. Exclude it when the user explicitly requires immediately bookable or real-time available inventory; otherwise rank it after `is_on_request=false` and use the localized label equivalent of `Inventory requires supplier confirmation`.
6. Resolve required facilities through hotel details when needed.
7. Apply the user's explicit sort first.
8. Default tie-break order: number/strength of verified preference matches, immediate bookability, distance, live stay total, cancellation flexibility.
9. Select five. If fewer qualify, show fewer and state why.

Generate each `Why it matches` statement from evidence that affected ranking. Good examples:

- `0.8 km from the search center; the closest bookable hotel in this set`
- `Lowest verified total for the four-night stay`
- `Meets the five-star requirement and has a verified pool`
- `Offers the requested twin room with free cancellation through November 1`

Do not use generic praise or cached price. If the user asks to view all returned results, show the complete original candidate pool, split into localized equivalents of `Meets all hard constraints` and `Does not meet all hard constraints`, and state every exclusion reason for each non-match. Verify each additional hotel's live rate before quoting it and fetch static details needed by the same output template. A candidate with no matching live product must remain in the complete-pool view, but its price must use the localized equivalent of `No matching live room or quote`; never present it as a match or substitute cached `min_price`.

## Display field mappings

### Hotel list

| Display item | Source |
|---|---|
| Candidate count | `search_hotels.data.total` or returned array length |
| Distance | `search_hotels.data.hotels[].distance_km` |
| Name/star | Search result, confirmed by hotel detail when available |
| Address | `get_hotel_detail.data.hotel.address_cn`, then `address` |
| Hero image | Hotel-image priority described above; render it without exposing the source URL as a separate link |
| Hotel detail page | The same hotel's `query_room_rates.data.web_url` or successful `batch_query_room_rates.data.results[].data.web_url`; never use `search_hotels.data.web_url` |
| Room/price | Matching live product from `query_room_rates` or a successful `batch_query_room_rates` item; convert for presentation to the selected display currency when necessary |
| Cancellation | Matching product's `cancellation_policy` |
| Tax or fee note | Show only explicit tax or fee data returned by the API, or when the user asks |
| Match reason | Verified user constraint/preference fields only |

For hotel lists and room-rate details, the selected display currency is:

| Current request | Default display currency |
|---|---|
| Chinese | `CNY` |
| English or any other non-Chinese language | `USD` |
| User explicitly requests a currency | The requested ISO 4217 currency |

When the live product currency differs from the selected display currency, obtain a current live exchange rate and convert both `per_night_price` and `total_price` consistently. Label converted amounts as approximate and state the exchange rate, source, and retrieval time below the results. Tell the user that another display currency is available on request. Preserve the original product amount and currency for availability checking and booking.

### Room details

Room image priority:

1. exact live `room_type.basic_room_image`
2. confidently matching static `rooms[].basic_room_image`
3. generic room gallery with an explicit non-correspondence label
4. no image message

For a Chinese response, use `name_cn` when non-empty; otherwise use `name`. For other response languages, use `name` when non-empty and fall back to `name_cn`. Render an empty/`Others` name using the localized equivalent of `Other / room assigned at check-in`. Show bed, maximum occupancy, conservative meal text, per-night price, total price, cancellation and `is_on_request` status together.

## Cancellation, tax and payment semantics

Cancellation:

- `type=non_refundable` or `effective_non_refundable=true` → non-refundable.
- `type=free_cancel_before_deadline` → show the exact deadline and its returned timezone offset.
- Never remove or silently convert the timezone.

Tax and fees:

- In the final booking-confirmation template, state that the TourMind room price is tax included. A small number of countries or regions require hotels to collect city or tourism taxes at check-in; include the required customer notice in that template.
- Read `hotel.fees.mandatory` for city/resort/on-property charges and show its explicit content separately in every final booking-confirmation template. Do not invent an amount or charging basis.
- When no explicit mandatory-fee content is returned, write the localized equivalent of `The hotel did not return any additional mandatory fee information.`; do not infer that no fee can ever be collected.
- Do not add mandatory-fee prose numerically unless the API gives an unambiguous amount and charging basis.

Stripe:

- The 3.5% fee is Stripe payment processing, not room rate, hotel tax or a TourMind booking surcharge.
- Show it only when Stripe is being considered or selected. Before starting payment, disclose that once charged, this processing fee is non-refundable, including when the booking is later cancelled within the hotel's free-cancellation period, and obtain the user's explicit acknowledgement.
- Use returned `fee_amount` and `payable_amount`; do not recompute when values are available.
- Before cancelling an order paid through Stripe, explain that the eligible room-charge refund follows the hotel's cancellation policy but the charged Stripe processing fee will not be refunded, even during the free-cancellation period. Obtain explicit cancellation confirmation after this disclosure.

## Booking and order rules

Guest names should match identification documents. The service handles Chinese and Latin-script names; do not promise a specific transliteration.

Before booking, confirm:

- a stored credential matching the active channel: `uk_` as `user_key` for ToC, or `sk_` as `token` for ToB;
- exact hotel and room product;
- dates, adults per room, children per room, every child's age per room, and room count;
- latest checked total/currency, cancellation policy and availability;
- hotel `checkin.begin_time` and `checkout.time`, or the localized equivalent of `Not provided by the hotel` if either field is absent;
- explicit `hotel.fees.mandatory` content, or the localized equivalent of `The hotel did not return any additional mandatory fee information.`;
- the tax notice and 7×24 TourMind customer-service contact `+86-755 3665 4666`;
- full legal guest name;
- mandatory contact email.

Present the complete final booking-confirmation template defined in `SKILL.md` after `check_room_availability` and before `create_booking`; require an explicit user confirmation of that displayed information.

If the user provides a credential after room selection, determine whether the channel changed. On any channel change, discard all prior rate and availability data, re-query on the new channel, recheck availability, and obtain confirmation again. Even when no token becomes `uk_` and remains on ToC, run a fresh final availability and price check before creating the order.

Record the order-creation channel with `agent_ref_id` in conversation context. Payment, query, and cancellation must use that same channel and a matching-prefix credential. If the current credential belongs to the other channel, stop and request the credential used for that order; never try both channels.

Common order statuses:

| Status | Meaning |
|---|---|
| `UNPAID` | Created, awaiting payment |
| `PENDING` | Paid, waiting for hotel confirmation; do not ask the user to pay again |
| `CONFIRMED` | Confirmed by hotel |
| `CANCELLED` | Cancelled |
| `CONFIRM_FAILED` | Hotel confirmation failed |

## Errors and performance

The `reason` codes in the table below apply to `query_room_rates` responses and individual `batch_query_room_rates.data.results[]` items. Process batch item reasons independently; an item-level error does not make the whole batch unsuccessful. `invalid_request` may also be returned as a top-level error when the entire single-hotel or batch request is malformed.

| Error/symptom | Required handling |
|---|---|
| `unauthorized` / HTTP 401 | Delete `{baseDir}/skill_token.txt`, stop the authenticated operation, and show the reauthentication guidance matching the invalid prefix; do not silently downgrade or probe the other channel |
| `error_code=HOTEL_BUSINESS_PERMISSION_REQUIRED` / HTTP 403 on ToB | Stop the hotel workflow. State that hotel business access is not enabled for the user's TourMind account and ask them to contact their account administrator or TourMind support. Keep the token file; replacing the valid `sk_` token does not grant the missing permission |
| Missing token before an order operation | Pause and show both personal and business sign-in choices from `SKILL.md`; do not block public ToC read-only work |
| Unknown token prefix | Do not call an endpoint; request a complete token beginning `uk_` or `sk_` |
| Channel changed after rate selection | Invalidate prior rates, re-query and recheck on the new channel, then obtain confirmation again |
| No search candidates | Report the exact constraint set; offer changes without applying them |
| Candidates but no live products | State that hotels were found but none had matching live rooms |
| `reason=no_matching_live_room` | Treat as a successful business-empty result and suggest changing dates or occupancy |
| `reason=hotel_not_found` | State that the hotel is missing or unavailable |
| `reason=upstream_timeout` | State that real-time pricing timed out and may be retried later |
| `reason=upstream_error` | Report a temporary service failure; never describe it as no availability |
| `reason=hotel_detail_unavailable` | Report that hotel details required for the room response are temporarily unavailable |
| `reason=invalid_request` | Correct the request before retrying |
| Budget-capped search empty | Optionally probe without budget only to diagnose over-budget inventory |
| Rate check failed | Re-run availability once for the selected rate; if still failed, report it |
| Booking creation failed | Report the error; do not retry with guessed guest/order data |

Use `batch_query_room_rates` for multi-hotel rate retrieval, with at most 20 hotels per request and at most three concurrent batch requests per client. Keep booking, cancellation and payment operations sequential and explicitly confirmed.

Optional response fields can differ by channel. For example, one channel may return `basic_room_image` while the other omits it. Render only fields actually returned by the active channel; never infer channel-specific optional data from the other channel.
