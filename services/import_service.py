"""
Import Service – Persists CSV data to SQLite via SQLAlchemy.

Handles:
- Auto-creation of Users from paid_by names
- Auto-creation of a default group for CSV imports
- Saving expenses with participant splits
- Saving anomaly records
- Logging import history
"""

import pandas as pd
from datetime import datetime, date

from database.database import SessionLocal
from database.models import (
    User,
    Group,
    GroupMember,
    Expense,
    ExpenseParticipant,
    Anomaly,
    ImportLog,
)


# =====================================================
# FIND OR CREATE USER
# =====================================================

def find_or_create_user(name, db):
    """
    Look up a user by normalized name.
    Create if not found.
    """
    normalized = str(name).strip().title()

    user = db.query(User).filter(
        User.name == normalized
    ).first()

    if not user:
        user = User(name=normalized)
        db.add(user)
        db.flush()

    return user


# =====================================================
# FIND OR CREATE DEFAULT GROUP
# =====================================================

def find_or_create_default_group(db):
    """
    Get or create the 'Imported Expenses' group
    used for CSV imports.
    """
    group = db.query(Group).filter(
        Group.name == "Imported Expenses"
    ).first()

    if not group:
        group = Group(name="Imported Expenses")
        db.add(group)
        db.flush()

    return group


# =====================================================
# SAVE EXPENSES
# =====================================================

def save_expenses(df, anomalies, db):
    """
    Save expense rows from the DataFrame into the database.
    Skips rows that have HIGH-severity anomalies on critical fields.
    Returns count of imported rows.
    """
    # Build a set of row numbers with HIGH severity issues
    # that should be skipped
    high_rows = set()
    for a in anomalies:
        if a.get("severity") == "HIGH":
            row_num = a.get("row_number")
            if row_num is not None:
                high_rows.add(row_num)

    group = find_or_create_default_group(db)

    imported_count = 0

    for idx, row in df.iterrows():

        row_number = idx + 1  # 1-indexed

        # Skip rows with HIGH severity anomalies
        if row_number in high_rows:
            continue

        # ------- PAYER -------
        paid_by_raw = row.get("paid_by")
        if pd.isna(paid_by_raw) or str(paid_by_raw).strip() == "":
            continue

        payer = find_or_create_user(paid_by_raw, db)

        # Ensure payer is a group member
        existing_member = db.query(GroupMember).filter(
            GroupMember.group_id == group.id,
            GroupMember.user_id == payer.id,
            GroupMember.status == "ACTIVE"
        ).first()

        if not existing_member:
            membership = GroupMember(
                group_id=group.id,
                user_id=payer.id,
                joined_on=date.today(),
                status="ACTIVE"
            )
            db.add(membership)

        # ------- DATE -------
        try:
            expense_date = pd.to_datetime(
                row.get("date")
            ).date()
        except Exception:
            expense_date = date.today()

        # ------- CURRENCY & AMOUNT -------
        currency_raw = row.get("currency")
        if pd.isna(currency_raw) or not isinstance(currency_raw, str) or currency_raw.strip() == "" or currency_raw.strip().lower() == "nan":
            currency = "INR"
        else:
            currency = currency_raw.strip().upper()

        try:
            raw_amount = float(
                str(row.get("amount", 0)).replace(",", "")
            )
        except (ValueError, TypeError):
            continue

        # Convert foreign currencies to INR
        from services.currency_converter import convert_to_inr
        amount = convert_to_inr(raw_amount, currency)

        # ------- SPLIT TYPE -------
        split_type_raw = row.get("split_type")
        if pd.isna(split_type_raw) or not isinstance(split_type_raw, str) or split_type_raw.strip() == "" or split_type_raw.strip().lower() == "nan":
            split_type = "equal"
        else:
            split_type = split_type_raw.strip().lower()

        # ------- DESCRIPTION -------
        description = str(
            row.get("description", "")
        ).strip()

        # ------- NOTES -------
        notes = str(
            row.get("notes", "")
        ).strip()

        if notes == "nan":
            notes = ""

        # Log original currency/amount in notes if converted
        if currency != "INR":
            original_info = f"[Original: {raw_amount} {currency}]"
            if notes:
                notes = f"{original_info} {notes}"
            else:
                notes = original_info
            currency = "INR"

        # ------- CREATE EXPENSE -------
        expense = Expense(
            group_id=group.id,
            description=description,
            amount=amount,
            currency=currency,
            expense_date=expense_date,
            paid_by=payer.id,
            split_type=split_type,
            notes=notes,
        )

        db.add(expense)
        db.flush()

        # ------- PARTICIPANTS -------
        # Parse split_with column
        split_with_raw = row.get("split_with", "")

        if pd.isna(split_with_raw):
            split_with_raw = ""

        # SettleWise CSV uses semicolons as delimiters for participants
        split_with_normalized = str(split_with_raw).replace(";", ",")
        participant_names = [
            n.strip() for n in split_with_normalized.split(",")
            if n.strip() and n.strip().lower() != "nan"
        ]

        # Always include the payer as a participant
        all_participant_names = list(set(
            [str(paid_by_raw).strip().title()] + [
                n.strip().title() for n in participant_names
            ]
        ))

        # Parse split_details for exact/percentage/shares splits
        split_details_raw = row.get("split_details", "")
        split_details = {}

        if not pd.isna(split_details_raw) and str(split_details_raw).strip():
            try:
                # SettleWise CSV uses semicolons for detail pairs (e.g. Rohan 700; Priya 400; Meera 400)
                normalized_details = str(split_details_raw).replace(";", ",").replace("%", "")
                for pair in normalized_details.split(","):
                    pair = pair.strip()
                    if not pair:
                        continue
                    if ":" in pair:
                        name_part, val_part = pair.split(":", 1)
                        name_part = name_part.strip().title()
                        val_part = val_part.strip()
                        split_details[name_part] = float(val_part)
                    else:
                        # Split from right on the last whitespace
                        parts = pair.rsplit(None, 1)
                        if len(parts) == 2:
                            name_part = parts[0].strip().title()
                            val_part = parts[1].strip()
                            split_details[name_part] = float(val_part)
            except Exception:
                pass

        num_participants = len(all_participant_names)
        participants_data = []
        total_shares_assigned = 0.0

        for pname in all_participant_names:

            participant_user = find_or_create_user(pname, db)

            # Ensure participant is a group member
            existing_pm = db.query(GroupMember).filter(
                GroupMember.group_id == group.id,
                GroupMember.user_id == participant_user.id,
                GroupMember.status == "ACTIVE"
            ).first()

            if not existing_pm:
                pm = GroupMember(
                    group_id=group.id,
                    user_id=participant_user.id,
                    joined_on=date.today(),
                    status="ACTIVE"
                )
                db.add(pm)

            share_amount = 0.0
            share_percentage = None
            share_units = None

            if split_type == "equal":
                share_amount = round(
                    amount / num_participants, 2
                ) if num_participants > 0 else 0

            elif split_type == "exact" or split_type == "unequal":
                total_exact = sum(split_details.get(n, 0) for n in all_participant_names)
                val = split_details.get(pname, 0)
                if total_exact > 0:
                    share_amount = round(amount * val / total_exact, 2)
                else:
                    share_amount = round(amount / num_participants, 2)

            elif split_type == "percentage":
                total_pct = sum(split_details.get(n, 0) for n in all_participant_names)
                pct = split_details.get(pname, 0)
                if total_pct > 0:
                    normalized_pct = (pct / total_pct) * 100
                else:
                    normalized_pct = 100 / num_participants
                share_percentage = normalized_pct
                share_amount = round(amount * normalized_pct / 100, 2)

            elif split_type == "shares" or split_type == "share":
                units = split_details.get(pname, 1)
                share_units = units
                total_units = sum(
                    split_details.get(n, 1)
                    for n in all_participant_names
                )
                if total_units > 0:
                    share_amount = round(
                        amount * units / total_units, 2
                    )
                else:
                    share_amount = round(amount / num_participants, 2)

            participants_data.append({
                "user_id": participant_user.id,
                "share_amount": share_amount,
                "share_percentage": share_percentage,
                "share_units": share_units,
            })
            total_shares_assigned += share_amount

        # Adjust any rounding discrepancy on the last participant
        if participants_data and num_participants > 0:
            diff = round(amount - total_shares_assigned, 2)
            if diff != 0.0:
                participants_data[-1]["share_amount"] = round(participants_data[-1]["share_amount"] + diff, 2)

        # Write to database
        for p_info in participants_data:
            ep = ExpenseParticipant(
                expense_id=expense.id,
                user_id=p_info["user_id"],
                share_amount=p_info["share_amount"],
                share_percentage=p_info["share_percentage"],
                share_units=p_info["share_units"],
            )
            db.add(ep)

        imported_count += 1

    return imported_count


# =====================================================
# SAVE ANOMALIES
# =====================================================

def save_anomalies(anomalies, db):
    """
    Persist detected anomalies to the database.
    """
    for anomaly in anomalies:

        record = Anomaly(
            row_number=anomaly.get("row_number"),
            anomaly_type=anomaly.get("type"),
            severity=anomaly.get("severity"),
            description=anomaly.get("description"),
            action_taken=anomaly.get("action"),
            status="PENDING",
            created_at=datetime.now(),
        )

        db.add(record)

    return len(anomalies)


# =====================================================
# SAVE IMPORT LOG
# =====================================================

def save_import_log(filename, total_rows, imported_rows,
                    anomalies_count, db):
    """
    Record the import event for audit trail.
    """
    log = ImportLog(
        file_name=filename,
        total_rows=total_rows,
        imported_rows=imported_rows,
        anomalies_found=anomalies_count,
        imported_at=datetime.now(),
    )

    db.add(log)

    return log


# =====================================================
# FULL IMPORT PIPELINE
# =====================================================

def run_full_import(df, filename):
    """
    Complete import pipeline:
    1. Detect anomalies
    2. Save anomalies to DB
    3. Save valid expenses to DB
    4. Create import log
    5. Commit everything

    Returns dict with results.
    """
    from services.anomaly_detector import detect_anomalies

    db = SessionLocal()

    try:
        # Step 1: Detect anomalies
        anomalies = detect_anomalies(df)

        # Step 2: Save anomalies
        anomaly_count = save_anomalies(anomalies, db)

        # Step 3: Save expenses (skipping HIGH rows)
        imported_rows = save_expenses(df, anomalies, db)

        # Step 4: Save import log
        save_import_log(
            filename=filename,
            total_rows=len(df),
            imported_rows=imported_rows,
            anomalies_count=anomaly_count,
            db=db,
        )

        # Step 5: Commit
        db.commit()

        return {
            "success": True,
            "total_rows": len(df),
            "imported_rows": imported_rows,
            "skipped_rows": len(df) - imported_rows,
            "anomalies": anomalies,
            "anomaly_count": anomaly_count,
        }

    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e),
        }

    finally:
        db.close()