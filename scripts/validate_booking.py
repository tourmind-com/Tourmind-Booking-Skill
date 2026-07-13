#!/usr/bin/env python3
"""
Booking validation script for TourMind Booking Skill
Validates that booking creation returns expected fields
"""

import json
import sys
from typing import Dict, Any, List

def validate_booking_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate booking response contains required fields

    Returns:
        {
            "valid": bool,
            "errors": List[str],
            "warnings": List[str],
            "booking_id": str or None
        }
    """
    errors = []
    warnings = []
    booking_id = None

    # Check if response has expected structure
    if not isinstance(response, dict):
        errors.append("Response is not a dictionary")
        return {"valid": False, "errors": errors, "warnings": warnings, "booking_id": None}

    # Check required fields for successful booking
    required_fields = ["booking_id", "total_price", "currency", "status"]
    for field in required_fields:
        if field not in response:
            errors.append(f"Missing required field: {field}")
        elif field == "booking_id":
            booking_id = response[field]

    # Validate field types
    if "total_price" in response:
        try:
            float(response["total_price"])
        except (TypeError, ValueError):
            errors.append("total_price must be numeric")

    if "status" in response:
        valid_statuses = ["confirmed", "pending", "failed", "cancelled"]
        if response["status"] not in valid_statuses:
            warnings.append(f"status '{response['status']}' is non-standard (expected: {valid_statuses})")

    # Optional but recommended fields
    optional_fields = ["hotel_name", "check_in", "check_out", "guest_name"]
    for field in optional_fields:
        if field not in response:
            warnings.append(f"Recommended field missing: {field}")

    is_valid = len(errors) == 0
    return {
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "booking_id": booking_id
    }


def validate_search_response(response: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate hotel search response"""
    errors = []
    warnings = []

    if not isinstance(response, list):
        errors.append("Response must be a list of hotels")
        return {"valid": False, "errors": errors, "warnings": warnings}

    if len(response) == 0:
        warnings.append("No hotels returned (may be valid for some regions/dates)")

    # Check each hotel has required fields
    required_hotel_fields = ["hotel_id", "hotel_name", "lowest_price", "currency"]
    for i, hotel in enumerate(response):
        if not isinstance(hotel, dict):
            errors.append(f"Hotel {i} is not a dictionary")
            continue

        for field in required_hotel_fields:
            if field not in hotel:
                errors.append(f"Hotel {i} missing field: {field}")

    is_valid = len(errors) == 0
    return {
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "hotel_count": len(response)
    }


if __name__ == "__main__":
    # Example usage
    if len(sys.argv) > 1:
        try:
            data = json.loads(sys.argv[1])
            if isinstance(data, list):
                result = validate_search_response(data)
            else:
                result = validate_booking_response(data)
            print(json.dumps(result, indent=2))
        except json.JSONDecodeError as e:
            print(json.dumps({
                "valid": False,
                "errors": [f"Invalid JSON: {e}"]
            }))
    else:
        print("Usage: python3 validate_booking.py '<json_response>'")
