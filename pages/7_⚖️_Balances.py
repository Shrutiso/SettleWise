import streamlit as st
import plotly.graph_objects as go
import os
from datetime import date

from database.database import SessionLocal
from database.models import (
    User, Group, Expense, Settlement, GroupMember
)
from services.balance_engine import (
    calculate_balances,
    calculate_all_balances,
    get_creditors_and_debtors,
)
from utils.helpers import inject_css, require_auth, sidebar_branding, get_page_config

st.set_page_config(**get_page_config("Balance Center"))

inject_css()
sidebar_branding()
require_auth()

st.title("⚖️ Balance Center")
st.caption("See who owes whom, filter by group, and record or view settlements")
st.divider()

db = SessionLocal()

try:
    groups = db.query(Group).all()
    
    view_mode = st.radio(
        "View Mode",
        ["All Groups Combined", "Specific Group"],
        horizontal=True,
    )

    selected_group = None

    if view_mode == "Specific Group":
        if groups:
            selected_group = st.selectbox(
                "Select Group",
                groups,
                format_func=lambda x: x.name,
            )
        else:
            st.info("No groups found. Please create a group first.")

    # =====================================================
    # CALCULATE BALANCES
    # =====================================================
    if selected_group:
        balances = calculate_balances(selected_group.id, db)
    else:
        balances = calculate_all_balances(db)

    creditors, debtors = get_creditors_and_debtors(balances)

    # =====================================================
    # SUMMARY CARDS
    # =====================================================
    total_credit = sum(c[2] for c in creditors)
    total_debit = sum(d[2] for d in debtors)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "💚 Total Owed to Members",
            f"₹{total_credit:,.2f}"
        )

    with col2:
        st.metric(
            "🔴 Total Owed by Members",
            f"₹{total_debit:,.2f}"
        )

    with col3:
        st.metric(
            "👥 Active Members In View",
            len(balances)
        )

    st.divider()

    # =====================================================
    # BALANCE CHART
    # =====================================================
    if balances:
        st.subheader("📊 Net Balances")
        sorted_balances = sorted(
            balances.items(),
            key=lambda x: x[1]["balance"],
        )

        names = [b[1]["name"] for b in sorted_balances]
        amounts = [b[1]["balance"] for b in sorted_balances]
        colors = [
            "#10b981" if a >= 0 else "#ef4444"
            for a in amounts
        ]

        fig = go.Figure(data=[go.Bar(
            y=names,
            x=amounts,
            orientation="h",
            marker=dict(
                color=colors,
                cornerradius=6,
            ),
            text=[
                f"₹{abs(v):,.2f}" for v in amounts
            ],
            textposition="inside",
            textfont=dict(
                color="white",
                size=13,
                family="Inter",
            ),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Balance: ₹%{x:,.2f}<extra></extra>"
            ),
        )])

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", color="#94a3b8"),
            margin=dict(l=20, r=20, t=10, b=20),
            xaxis=dict(
                gridcolor="rgba(99,102,241,0.08)",
                zerolinecolor="rgba(99,102,241,0.2)",
                zerolinewidth=2,
            ),
            yaxis=dict(gridcolor="rgba(99,102,241,0.08)"),
            height=max(250, len(balances) * 50),
            showlegend=False,
        )

        st.plotly_chart(fig, width="stretch")
        st.divider()

        # =====================================================
        # CREDITORS & DEBTORS
        # =====================================================
        c_col, d_col = st.columns(2)

        with c_col:
            st.subheader("💚 Creditors")
            st.caption("These members are owed money")

            if creditors:
                for _, name, amount in creditors:
                    st.markdown(f"""
                    <div class="glass-card" style="
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 8px;
                        padding: 14px 18px;
                    ">
                        <span style="font-weight: 600; color: #e2e8f0;">
                            {name}
                        </span>
                        <span style="
                            font-weight: 800;
                            color: #10b981;
                            font-size: 16px;
                        ">+₹{amount:,.2f}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No creditors")

        with d_col:
            st.subheader("🔴 Debtors")
            st.caption("These members owe money")

            if debtors:
                for _, name, amount in debtors:
                    st.markdown(f"""
                    <div class="glass-card" style="
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 8px;
                        padding: 14px 18px;
                    ">
                        <span style="font-weight: 600; color: #e2e8f0;">
                            {name}
                        </span>
                        <span style="
                            font-weight: 800;
                            color: #ef4444;
                            font-size: 16px;
                        ">-₹{amount:,.2f}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No debtors")

    else:
        st.info("No active balances or expenses found for this view.")

    st.divider()

    # =====================================================
    # RECORD SETTLEMENT
    # =====================================================
    st.subheader("✏️ Record Settlement")

    # Limit members to selected group if applicable
    if selected_group:
        users_for_settlement = db.query(User).join(GroupMember, User.id == GroupMember.user_id).filter(
            GroupMember.group_id == selected_group.id,
            GroupMember.status == "ACTIVE"
        ).all()
    else:
        users_for_settlement = db.query(User).all()

    if len(users_for_settlement) >= 2:
        s_col1, s_col2, s_col3 = st.columns(3)

        with s_col1:
            payer = st.selectbox(
                "Payer (who is paying)",
                users_for_settlement,
                format_func=lambda x: x.name,
                key="settle_payer_select"
            )

        with s_col2:
            receiver = st.selectbox(
                "Receiver (who gets paid)",
                users_for_settlement,
                format_func=lambda x: x.name,
                key="settle_receiver_select",
            )

        with s_col3:
            amount = st.number_input(
                "Settlement Amount (₹)",
                min_value=0.0,
                step=100.0,
                key="settle_amount_input"
            )

        # Allow group selection if viewing all, or pre-fill
        if not selected_group:
            target_group = st.selectbox(
                "Associate with Group",
                groups,
                format_func=lambda x: x.name,
                key="settle_group_select"
            )
        else:
            target_group = selected_group

        if st.button("💸 Record Settlement", type="primary", width="stretch"):
            if payer.id == receiver.id:
                st.error("Payer and Receiver cannot be the same person.")
            elif amount <= 0:
                st.error("Amount must be greater than 0.")
            elif not target_group:
                st.error("Please associate this settlement with a group.")
            else:
                settlement = Settlement(
                    group_id=target_group.id,
                    payer_id=payer.id,
                    receiver_id=receiver.id,
                    amount=amount,
                    settlement_date=date.today(),
                )
                db.add(settlement)
                db.commit()
                st.success(
                    f"✅ Settlement recorded: {payer.name} → {receiver.name} ₹{amount:,.2f} in '{target_group.name}'"
                )
                st.rerun()

    else:
        st.info("Need at least 2 active members to record settlements.")

    st.divider()

    # =====================================================
    # SETTLEMENT HISTORY
    # =====================================================
    st.subheader("📜 Settlement History")

    # Filter history by selected group if applicable
    if selected_group:
        history = db.query(Settlement).filter(Settlement.group_id == selected_group.id).all()
    else:
        history = db.query(Settlement).all()

    if history:
        rows = []
        for s in history:
            p = db.query(User).filter(User.id == s.payer_id).first()
            r = db.query(User).filter(User.id == s.receiver_id).first()
            g = db.query(Group).filter(Group.id == s.group_id).first()
            rows.append({
                "Date": s.settlement_date,
                "Group": g.name if g else "Global / None",
                "Payer": p.name if p else "—",
                "Receiver": r.name if r else "—",
                "Amount": f"₹{s.amount:,.2f}",
            })

        st.dataframe(
            rows,
            width="stretch",
            height=300,
        )
    else:
        st.info("No settlements recorded yet.")

finally:
    db.close()