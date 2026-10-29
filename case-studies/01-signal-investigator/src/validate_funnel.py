
"""Reusable data-quality validation for ecommerce funnels."""

# Funnel stages in their expected order
STAGES = [
    "sessions",
    "view_item_sessions",
    "add_to_cart_sessions",
    "begin_checkout_sessions",
    "payment_attempt_sessions",
    "orders",
]

COUNT_COLUMNS = STAGES + ["payment_failed_sessions"]


def validate_row(row):
    """Check one funnel record and return its errors."""

    errors = []
    counts = {}

    # Check 1: Values must be valid non-negative integers
    for column in COUNT_COLUMNS:
        try:
            value = int(row.get(column, ""))
            counts[column] = value

            if value < 0:
                errors.append(f"{column} cannot be negative")

        except (ValueError, TypeError):
            errors.append(f"{column} is missing or invalid")

    # Check 2: Funnel counts should not increase
    for previous, current in zip(STAGES, STAGES[1:]):
        if previous in counts and current in counts:
            if counts[current] > counts[previous]:
                errors.append(
                    f"{current} ({counts[current]}) exceeds "
                    f"{previous} ({counts[previous]})"
                )

    # Check 3: Failed-payment sessions cannot exceed attempts
    if (
        "payment_failed_sessions" in counts
        and "payment_attempt_sessions" in counts
    ):
        if (
            counts["payment_failed_sessions"]
            > counts["payment_attempt_sessions"]
        ):
            errors.append(
                "Payment failures exceed payment attempts"
            )

    return errors


def validate_dataset(rows):
    """Validate every record and check for duplicates."""

    errors = []
    seen = set()

    for number, row in enumerate(rows, start=2):
        key = (row.get("date"), row.get("channel"))

        if not all(key):
            errors.append(f"CSV line {number}: Missing date or channel")

        if key in seen:
            errors.append(
                f"CSV line {number}: Duplicate date/channel {key}"
            )

        seen.add(key)

        for error in validate_row(row):
            errors.append(f"CSV line {number}: {error}")

    return errors
