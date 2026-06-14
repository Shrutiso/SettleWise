import pandas as pd
from datetime import datetime


# =====================================================
# MISSING FIELDS
# =====================================================

def detect_missing_fields(df):

    anomalies = []

    required = [
        "date",
        "description",
        "paid_by",
        "amount",
        "currency",
        "split_type"
    ]

    for idx, row in df.iterrows():

        for col in required:

            if col not in df.columns:

                anomalies.append({
                    "row_number": idx + 1,
                    "type": "Missing Column",
                    "severity": "HIGH",
                    "description": f"Column '{col}' not found",
                    "action": "Import blocked"
                })

            elif pd.isna(row[col]):

                anomalies.append({
                    "row_number": idx + 1,
                    "type": "Missing Field",
                    "severity": "HIGH",
                    "description": f"{col} is missing",
                    "action": "Row skipped"
                })

    return anomalies


# =====================================================
# AMOUNT ISSUES
# =====================================================

def detect_amount_issues(df):

    anomalies = []

    for idx, row in df.iterrows():

        try:

            amount = float(
                str(row["amount"]).replace(",", "")
            )

            if amount < 0:

                anomalies.append({
                    "row_number": idx + 1,
                    "type": "Negative Amount",
                    "severity": "MEDIUM",
                    "description": f"Amount = {amount}",
                    "action": "Treated as refund"
                })

            elif amount == 0:

                anomalies.append({
                    "row_number": idx + 1,
                    "type": "Zero Amount",
                    "severity": "MEDIUM",
                    "description": "Expense amount is zero",
                    "action": "Imported with warning"
                })

        except Exception:

            anomalies.append({
                "row_number": idx + 1,
                "type": "Invalid Amount",
                "severity": "HIGH",
                "description": str(row["amount"]),
                "action": "Row skipped"
            })

    return anomalies


# =====================================================
# FUTURE DATES
# =====================================================

def detect_future_dates(df):

    anomalies = []

    if "date" not in df.columns:
        return anomalies

    today = datetime.today().date()

    for idx, row in df.iterrows():

        try:

            expense_date = pd.to_datetime(
                row["date"]
            ).date()

            if expense_date > today:

                anomalies.append({
                    "row_number": idx + 1,
                    "type": "Future Date",
                    "severity": "MEDIUM",
                    "description": str(expense_date),
                    "action": "Imported with warning"
                })

        except Exception:

            anomalies.append({
                "row_number": idx + 1,
                "type": "Invalid Date",
                "severity": "HIGH",
                "description": str(row["date"]),
                "action": "Row skipped"
            })

    return anomalies


# =====================================================
# NAME NORMALIZATION
# =====================================================

def detect_name_variations(df):

    anomalies = []

    if "paid_by" not in df.columns:
        return anomalies

    for idx, row in df.iterrows():

        if pd.isna(row["paid_by"]):
            continue

        original = str(row["paid_by"])

        cleaned = original.strip().title()

        if original != cleaned:

            anomalies.append({
                "row_number": idx + 1,
                "type": "Name Variation",
                "severity": "LOW",
                "description": f"{original} → {cleaned}",
                "action": "Auto-normalized"
            })

    return anomalies


# =====================================================
# DUPLICATES
# =====================================================

def detect_possible_duplicates(df):

    anomalies = []

    seen = {}

    for idx, row in df.iterrows():

        paid_by = str(
            row.get("paid_by", "")
        ).strip().lower()

        amount = str(
            row.get("amount", "")
        ).replace(",", "")

        date = str(
            row.get("date", "")
        ).strip()

        description = str(
            row.get("description", "")
        ).strip().lower()

        key = (
            date,
            paid_by,
            amount,
            description
        )

        if key in seen:

            anomalies.append({
                "row_number": idx + 1,
                "type": "Duplicate Expense",
                "severity": "HIGH",
                "description":
                f"Possible duplicate of row {seen[key] + 1}",
                "action": "Needs approval"
            })

        else:
            seen[key] = idx

    return anomalies


# =====================================================
# CURRENCY ISSUES
# =====================================================

def detect_currency_issues(df):

    anomalies = []

    valid = [
        "INR",
        "USD",
        "EUR",
        "GBP"
    ]

    if "currency" not in df.columns:
        return anomalies

    for idx, row in df.iterrows():

        currency = row["currency"]

        if pd.isna(currency):
            continue

        if str(currency).upper() not in valid:

            anomalies.append({
                "row_number": idx + 1,
                "type": "Unknown Currency",
                "severity": "MEDIUM",
                "description": str(currency),
                "action": "Imported with warning"
            })

    return anomalies


# =====================================================
# SPLIT TYPE VALIDATION
# =====================================================

def detect_invalid_split_types(df):

    anomalies = []

    valid = [
        "equal",
        "exact",
        "percentage",
        "shares"
    ]

    if "split_type" not in df.columns:
        return anomalies

    for idx, row in df.iterrows():

        split_type = str(
            row["split_type"]
        ).lower()

        if split_type not in valid:

            anomalies.append({
                "row_number": idx + 1,
                "type": "Invalid Split Type",
                "severity": "HIGH",
                "description": split_type,
                "action": "Row skipped"
            })

    return anomalies


# =====================================================
# MASTER DETECTOR
# =====================================================

def detect_anomalies(df):

    anomalies = []

    anomalies.extend(
        detect_missing_fields(df)
    )

    anomalies.extend(
        detect_amount_issues(df)
    )

    anomalies.extend(
        detect_future_dates(df)
    )

    anomalies.extend(
        detect_name_variations(df)
    )

    anomalies.extend(
        detect_possible_duplicates(df)
    )

    anomalies.extend(
        detect_currency_issues(df)
    )

    anomalies.extend(
        detect_invalid_split_types(df)
    )

    return anomalies