import streamlit as st
import os

from database.database import SessionLocal
from database.models import (
    User, Group, Settlement
)
from services.settlement_engine import (
    generate_settlements,
    generate_all_settlements,
    apply_settlement,
    apply_all_settlements,
)
from utils.helpers import inject_css, require_auth, sidebar_branding, get_page_config

st.set_page_config(**get_page_config("Settlement Recommendations"))

inject_css()
sidebar_branding()
require_auth()

st.title("🤝 Settlement Recommendations")
st.caption("Optimized recommendations to settle all balances with minimum transactions")
st.divider()

db = SessionLocal()

try:
    # =====================================================
    # GROUP SELECTOR
    # =====================================================
    groups = db.query(Group).all()

    view_mode = st.radio(
        "Scope",
        ["All Groups", "Specific Group"],
        horizontal=True,
    )

    selected_group = None

    if view_mode == "Specific Group" and groups:
        selected_group = st.selectbox(
            "Select Group",
            groups,
            format_func=lambda x: x.name,
        )

    st.divider()

    # =====================================================
    # GENERATE SETTLEMENTS
    # =====================================================
    st.subheader("⚡ Generate Optimized Settlements")
    st.markdown("""
    The settlement engine uses a **greedy min-transactions algorithm** to minimize
    the number of payments needed to settle all debts.
    """)

    if st.button(
        "🧮 Calculate Settlements",
        type="primary",
        width="stretch",
    ):
        with st.spinner("Calculating optimal settlements..."):
            if selected_group:
                recommendations = generate_settlements(
                    selected_group.id, db
                )
            else:
                recommendations = generate_all_settlements(db)

        st.session_state["recommendations"] = recommendations

    # =====================================================
    # DISPLAY RECOMMENDATIONS
    # =====================================================
    if "recommendations" in st.session_state:
        recommendations = st.session_state["recommendations"]

        if not recommendations:
            st.markdown("""
            <div style="
                text-align: center;
                padding: 40px;
                background: linear-gradient(135deg, rgba(16,185,129,0.08), rgba(52,211,153,0.05));
                border: 1px solid rgba(16,185,129,0.2);
                border-radius: 16px;
                margin: 20px 0;
            ">
                <p style="font-size: 40px; margin-bottom: 8px;">✅</p>
                <h3 style="color: #10b981;">All Settled!</h3>
                <p style="color: #94a3b8;">
                    No outstanding balances. Everyone is even.
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            total_amount = sum(r["amount"] for r in recommendations)

            s1, s2 = st.columns(2)
            with s1:
                st.metric(
                    "🔢 Transactions Needed",
                    len(recommendations),
                )
            with s2:
                st.metric(
                    "💰 Total Settlement",
                    f"₹{total_amount:,.2f}",
                )

            st.divider()
            st.subheader("💸 Recommended Payments")

            # Display each recommendation as a styled card
            for i, rec in enumerate(recommendations):
                st.markdown(f"""
                <div class="settlement-card" style="
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    gap: 16px;
                    background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(139,92,246,0.05));
                    border: 1px solid rgba(99,102,241,0.15);
                    border-radius: 12px;
                    padding: 12px 18px;
                    margin-bottom: 10px;
                ">
                    <div style="
                        display: flex;
                        align-items: center;
                        gap: 16px;
                        flex: 1;
                    ">
                        <div style="
                            background: rgba(239,68,68,0.1);
                            border-radius: 50%;
                            width: 44px;
                            height: 44px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-size: 18px;
                        ">💳</div>
                        <div>
                            <div style="
                                font-size: 16px;
                                font-weight: 700;
                                color: #e2e8f0;
                            ">
                                {rec['from_name']}
                                <span style="color: #6366f1;"> → </span>
                                {rec['to_name']}
                            </div>
                            <div style="
                                font-size: 12px;
                                color: #64748b;
                                margin-top: 2px;
                            ">
                                Payment #{i+1} of {len(recommendations)}
                            </div>
                        </div>
                    </div>
                    <div style="font-weight: 800; font-size: 18px; color: #10b981;">
                        ₹{rec['amount']:,.2f}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.divider()

            # =====================================================
            # ACCEPT SETTLEMENTS
            # =====================================================
            st.subheader("✅ Record Settlements")

            a1, a2 = st.columns(2)
            with a1:
                if st.button(
                    "✅ Accept All & Record",
                    type="primary",
                    width="stretch",
                ):
                    with st.spinner("Recording settlements..."):
                        g_id = selected_group.id if selected_group else None
                        apply_all_settlements(recommendations, db, group_id=g_id)

                    st.balloons()
                    st.success(
                        f"✅ {len(recommendations)} settlements recorded successfully!"
                    )
                    # Clear recommendations
                    del st.session_state["recommendations"]
                    st.rerun()

            with a2:
                if st.button(
                    "🔄 Recalculate / Clear",
                    width="stretch",
                ):
                    del st.session_state["recommendations"]
                    st.rerun()

            st.divider()

            # Individual accept buttons
            st.subheader("📝 Accept Individual Settlements")
            for i, rec in enumerate(recommendations):
                col1, col2, col3 = st.columns([5, 2, 2])
                with col1:
                    st.write(
                        f"**{rec['from_name']}** → **{rec['to_name']}**"
                    )
                with col2:
                    st.write(f"₹{rec['amount']:,.2f}")
                with col3:
                    if st.button(
                        "Accept",
                        key=f"accept_{i}",
                    ):
                        g_id = selected_group.id if selected_group else None
                        apply_settlement(
                            rec["from_id"],
                            rec["to_id"],
                            rec["amount"],
                            db,
                            group_id=g_id
                        )
                        st.success(f"✅ Recorded!")
                        st.rerun()

    st.divider()

    # =====================================================
    # SETTLEMENT HISTORY
    # =====================================================
    st.subheader("📜 Settlement History")

    # Filter history by selected group if applicable
    if selected_group:
        history = db.query(Settlement).filter(Settlement.group_id == selected_group.id).order_by(Settlement.id.desc()).all()
    else:
        history = db.query(Settlement).order_by(Settlement.id.desc()).all()

    if history:
        for s in history:
            p = db.query(User).filter(User.id == s.payer_id).first()
            r = db.query(User).filter(User.id == s.receiver_id).first()
            g = db.query(Group).filter(Group.id == s.group_id).first()
            
            c_info, c_action = st.columns([7, 3])
            
            with c_info:
                group_tag = f" [{g.name}]" if g else " [Global]"
                st.markdown(f"""
                <div class="glass-card" style="
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 14px 18px;
                ">
                    <div>
                        <span style="font-weight: 600; color: #e2e8f0;">
                            {p.name if p else '—'} → {r.name if r else '—'} {group_tag}
                        </span>
                        <span style="
                            color: #64748b;
                            font-size: 12px;
                            margin-left: 12px;
                        ">
                            {s.settlement_date or '—'}
                        </span>
                    </div>
                    <span style="
                        font-weight: 800;
                        color: #10b981;
                        font-size: 16px;
                    ">₹{s.amount:,.2f}</span>
                </div>
                """, unsafe_allow_html=True)
                
            with c_action:
                # Add Delete Settlement button
                if st.button("🗑️ Remove Settlement", key=f"delete_settle_{s.id}", width="stretch"):
                    db.delete(s)
                    db.commit()
                    st.success("Settlement removed successfully!")
                    st.rerun()

    else:
        st.info("No settlements recorded yet.")

finally:
    db.close()
