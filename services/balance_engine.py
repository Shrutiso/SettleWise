"""
Balance Engine – Calculates who owes whom.

Handles multiple split types:
- equal: split evenly among all participants
- exact: each participant has a fixed share_amount
- percentage: each participant has a percentage share
- shares: each participant has share units

Returns net balances per user within a group.
"""

from database.database import SessionLocal
from database.models import (
    User,
    Expense,
    ExpenseParticipant,
    Settlement,
    Group,
)


# =====================================================
# CALCULATE NET BALANCES
# =====================================================

def calculate_balances(group_id, db):
    """
    Calculate net balance for each user in a group.

    Positive balance = user is owed money (creditor)
    Negative balance = user owes money (debtor)

    Returns: dict of {user_id: {"name": str, "balance": float}}
    """
    balances = {}

    # Initialize balances for all users
    users = db.query(User).all()

    for user in users:
        balances[user.id] = {
            "name": user.name,
            "balance": 0.0,
        }

    # Process expenses
    expenses = db.query(Expense).filter(
        Expense.group_id == group_id
    ).all()

    for expense in expenses:

        payer_id = expense.paid_by
        amount = expense.amount or 0

        if payer_id not in balances:
            continue

        # Credit the payer with the full amount
        balances[payer_id]["balance"] += amount

        # Get participants
        participants = db.query(ExpenseParticipant).filter(
            ExpenseParticipant.expense_id == expense.id
        ).all()

        if not participants:
            # If no participants recorded, assume equal split
            # among all group users (fallback)
            group_users = list(balances.keys())
            share = amount / len(group_users) if group_users else 0
            for uid in group_users:
                balances[uid]["balance"] -= share
            continue

        # Debit each participant with their share
        for participant in participants:

            uid = participant.user_id

            if uid not in balances:
                # User might have been created but not tracked
                user = db.query(User).filter(
                    User.id == uid
                ).first()
                balances[uid] = {
                    "name": user.name if user else f"User {uid}",
                    "balance": 0.0,
                }

            share = participant.share_amount or 0
            balances[uid]["balance"] -= share

    # Subtract recorded settlements
    settlements = db.query(Settlement).filter(
        Settlement.group_id == group_id
    ).all()

    for settlement in settlements:

        pid = settlement.payer_id
        rid = settlement.receiver_id
        amt = settlement.amount or 0

        # Settlement means payer paid receiver
        if pid in balances:
            balances[pid]["balance"] -= amt

        if rid in balances:
            balances[rid]["balance"] += amt

    # Round balances to avoid floating point noise
    for uid in balances:
        balances[uid]["balance"] = round(
            balances[uid]["balance"], 2
        )

    # Remove users with zero balance and no activity
    # (keep only users involved in this group's expenses)
    involved_users = set()

    for expense in expenses:
        involved_users.add(expense.paid_by)
        parts = db.query(ExpenseParticipant).filter(
            ExpenseParticipant.expense_id == expense.id
        ).all()
        for p in parts:
            involved_users.add(p.user_id)

    filtered = {
        uid: info for uid, info in balances.items()
        if uid in involved_users
    }

    return filtered


# =====================================================
# CALCULATE ALL BALANCES (NO GROUP FILTER)
# =====================================================

def calculate_all_balances(db):
    """
    Calculate net balances across ALL expenses (all groups).
    Useful for the global balances view.
    """
    balances = {}

    users = db.query(User).all()
    for user in users:
        balances[user.id] = {
            "name": user.name,
            "balance": 0.0,
        }

    expenses = db.query(Expense).all()

    for expense in expenses:

        payer_id = expense.paid_by
        amount = expense.amount or 0

        if payer_id not in balances:
            continue

        balances[payer_id]["balance"] += amount

        participants = db.query(ExpenseParticipant).filter(
            ExpenseParticipant.expense_id == expense.id
        ).all()

        if not participants:
            all_uids = list(balances.keys())
            share = amount / len(all_uids) if all_uids else 0
            for uid in all_uids:
                balances[uid]["balance"] -= share
            continue

        for participant in participants:
            uid = participant.user_id
            if uid not in balances:
                user = db.query(User).filter(
                    User.id == uid
                ).first()
                balances[uid] = {
                    "name": user.name if user else f"User {uid}",
                    "balance": 0.0,
                }
            share = participant.share_amount or 0
            balances[uid]["balance"] -= share

    # Settlements
    settlements = db.query(Settlement).all()

    for settlement in settlements:
        pid = settlement.payer_id
        rid = settlement.receiver_id
        amt = settlement.amount or 0

        if pid in balances:
            balances[pid]["balance"] -= amt
        if rid in balances:
            balances[rid]["balance"] += amt

    for uid in balances:
        balances[uid]["balance"] = round(
            balances[uid]["balance"], 2
        )

    return balances


# =====================================================
# GET CREDITORS & DEBTORS
# =====================================================

def get_creditors_and_debtors(balances):
    """
    Separate users into creditors (owed money)
    and debtors (owe money).

    Returns:
        creditors: list of (user_id, name, amount) sorted desc
        debtors: list of (user_id, name, amount) sorted desc
    """
    creditors = []
    debtors = []

    for uid, info in balances.items():
        bal = info["balance"]
        if bal > 0.01:  # Small threshold for float noise
            creditors.append(
                (uid, info["name"], bal)
            )
        elif bal < -0.01:
            debtors.append(
                (uid, info["name"], abs(bal))
            )

    creditors.sort(key=lambda x: x[2], reverse=True)
    debtors.sort(key=lambda x: x[2], reverse=True)

    return creditors, debtors
