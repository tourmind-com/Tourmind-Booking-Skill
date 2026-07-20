# TourMind Booking Skill

TourMind's end-to-end hotel booking skill for AI clients. It supports POI resolution, live hotel and room comparison, rate verification, booking, order management, cancellation, and payment.

## Features

- Resolves cities, hotels, landmarks, stations, and other POIs without inventing coordinates.
- Verifies up to 20 hotel candidates against live room products and selects the five best matches.
- Returns consistent hotel cards with images, distance, live prices, cancellation terms, tax status, and evidence-based match reasons.
- Returns hotel details, room images, beds, meals, live quotes, and cancellation terms together.
- Rechecks price and availability before booking.
- Creates bookings after collecting the guest's legal name and required contact email.
- Queries and cancels existing bookings.
- Starts Stripe, WeChat Pay, or Alipay payments and discloses Stripe's 3.5% processing fee when applicable.

## Installable contents

```
├── .gitignore
├── LICENSE
├── README.md
├── SKILL.md
├── references/
│   └── parameter_guide.md
```

Evaluation fixtures, test reports, review translations, and development-only validators are intentionally excluded from the installable release.

## Installation

Clone the repository into your AI client's skills directory:

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/tourmind-com/Tourmind-Booking-Skill.git ~/.codex/skills/tourmind-booking
```

Generate a Skill Token in the customer portal at `/user/home`, save it as `skill_token.txt` in the installed skill directory, and restrict its permissions:

```bash
chmod 600 ~/.codex/skills/tourmind-booking/skill_token.txt
```

The token file is excluded by `.gitignore` and must never be committed. Restart the AI client or gateway after installation. No local MCP server is required; the skill calls the TourMind Skill API directly over HTTP.

## API

**Base URL:** `http://39.108.114.224:9028`

| Endpoint | Purpose |
|---|---|
| `POST /tob/skill/search_location` | Resolve a region, POI, or hotel |
| `POST /tob/skill/search_hotels` | Search hotel candidates |
| `POST /tob/skill/get_hotel_detail` | Get hotel details and images |
| `POST /tob/skill/query_room_rates` | Get live rooms and rates |
| `POST /tob/skill/check_room_availability` | Recheck price and availability |
| `POST /tob/skill/create_booking` | Create a booking |
| `POST /tob/skill/query_booking` | Query a booking |
| `POST /tob/skill/cancel_booking` | Cancel a booking |
| `POST /tob/skill/pay_order` | Start payment |

Every request body must include the `token` generated in the customer portal.

## Example

```
User: Find a hotel in Tokyo for two adults from April 28 to April 30.

Assistant: TourMind returned 20 candidates. I verified live rooms and rates and selected the five best matches.

           1. Example Hotel
           [hotel hero image]
           Lowest matching live rate: JPY 18,000 per night; JPY 36,000 total
           Why it matches: low verified total in this set; fits two adults; immediately bookable inventory.

           I can also show the remaining candidates or the complete returned pool.

User: Show me the standard rooms at the second hotel.

Assistant: Here are the hotel's details, room images, and current matching quotes. Choose a room and I will perform a final price and availability check.

User: Book the standard king room.

Assistant: Please provide the guest's full legal name and a contact email. The email is required for booking status and cancellation notifications.

User: Alex Smith, guest@example.com

Assistant: Booking created. TourMind order number: TM20260428001. Choose Stripe, WeChat Pay, or Alipay.
```

## API reference

See [references/parameter_guide.md](references/parameter_guide.md) for request fields, POI proxy logic, candidate ranking, image mapping, taxes, and booking rules. Resolve city and region IDs through the live `search_location` endpoint instead of relying on hardcoded values.
