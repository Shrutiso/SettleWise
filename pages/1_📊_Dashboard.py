import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from utils.helpers import inject_css, require_auth, sidebar_branding
from database.database import SessionLocal
from database.models import (
    Expense, User, Anomaly, Settlement, ImportLog, Group
)

st.set_page_config(
    page_title="SettleWise | Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

inject_css()
sidebar_branding()
require_auth()

# ------- PLOTLY DARK THEME -------
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(
        family="Inter, sans-serif",
        color="#94a3b8"
    ),
    margin=dict(l=20, r=20, t=40, b=20),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        borderwidth=0,
    ),
    xaxis=dict(
        gridcolor="rgba(99,102,241,0.08)",
        zerolinecolor="rgba(99,102,241,0.1)",
    ),
    yaxis=dict(
        gridcolor="rgba(99,102,241,0.08)",
        zerolinecolor="rgba(99,102,241,0.1)",
    ),
)

COLORS = [
    "#6366f1", "#8b5cf6", "#06b6d4", "#10b981",
    "#f59e0b", "#ec4899", "#ef4444", "#14b8a6",
]


# =====================================================
# PAGE HEADER
# =====================================================

st.title("📊 Dashboard")
st.caption("Real-time expense overview and financial insights")

st.divider()


# =====================================================
# LOAD DATA
# =====================================================

db = SessionLocal()

try:
    expenses = db.query(Expense).all()
    users = db.query(User).all()
    anomalies = db.query(Anomaly).all()
    settlements = db.query(Settlement).all()
    groups = db.query(Group).all()

    total_expense_count = len(expenses)
    total_member_count = len(users)
    total_anomaly_count = len(anomalies)
    total_settlement_count = len(settlements)
    total_group_count = len(groups)

    unresolved_anomalies = len([
        a for a in anomalies if a.status == "PENDING"
    ])

    total_expense_amount = sum(
        e.amount for e in expenses if e.amount
    ) if expenses else 0

    total_settlement_amount = sum(
        s.amount for s in settlements if s.amount
    ) if settlements else 0

    # =====================================================
    # KPI CARDS
    # =====================================================

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "💰 Total Expenses",
            f"₹{total_expense_amount:,.0f}",
            f"{total_expense_count} transactions"
        )

    with col2:
        st.metric(
            "👥 Members",
            total_member_count,
        )

    with col3:
        st.metric(
            "📁 Groups",
            total_group_count,
        )

    with col4:
        st.metric(
            "🤝 Settlements",
            f"₹{total_settlement_amount:,.0f}",
            f"{total_settlement_count} completed"
        )

    with col5:
        st.metric(
            "⚠️ Anomalies",
            unresolved_anomalies,
            f"{total_anomaly_count} total"
        )

    st.divider()

    if not expenses:
        st.markdown("""
        <div style="
            text-align: center;
            padding: 60px 20px;
            background: linear-gradient(135deg, rgba(99,102,241,0.06), rgba(139,92,246,0.04));
            border: 1px dashed rgba(99,102,241,0.2);
            border-radius: 16px;
        ">
            <p style="font-size: 48px; margin-bottom: 12px;">📂</p>
            <h3 style="color: #e2e8f0; margin-bottom: 8px;">No Expense Data Yet</h3>
            <p style="color: #94a3b8;">
                Import your first CSV file to see the dashboard come alive.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # =====================================================
    # BUILD DATAFRAMES
    # =====================================================

    expense_records = []
    for e in expenses:
        payer = db.query(User).filter(
            User.id == e.paid_by
        ).first()

        expense_records.append({
            "date": e.expense_date,
            "description": e.description or "",
            "amount": e.amount or 0,
            "currency": e.currency or "INR",
            "paid_by": payer.name if payer else "Unknown",
            "split_type": e.split_type or "equal",
        })

    expense_df = pd.DataFrame(expense_records)

    # Parse dates
    expense_df["date"] = pd.to_datetime(
        expense_df["date"], errors="coerce"
    )
    expense_df["month"] = expense_df["date"].dt.strftime("%Y-%m")
    expense_df["month_label"] = expense_df["date"].dt.strftime("%b %Y")

    # Categorize expenses
    def categorize(desc):
        desc_lower = str(desc).lower()
        if any(w in desc_lower for w in ["rent", "house", "flat"]):
            return "🏠 Rent"
        elif any(w in desc_lower for w in ["food", "dinner", "lunch", "breakfast", "restaurant", "cafe", "swiggy", "zomato", "biryani", "pizza", "chai"]):
            return "🍔 Food"
        elif any(w in desc_lower for w in ["travel", "cab", "uber", "ola", "flight", "train", "bus", "petrol", "fuel"]):
            return "🚗 Travel"
        elif any(w in desc_lower for w in ["electricity", "water", "wifi", "internet", "gas", "maintenance"]):
            return "⚡ Utilities"
        elif any(w in desc_lower for w in ["grocery", "vegetables", "milk", "fruits"]):
            return "🛒 Groceries"
        elif any(w in desc_lower for w in ["movie", "cinema", "game", "fun", "park", "parasailing", "beach"]):
            return "🎬 Entertainment"
        elif any(w in desc_lower for w in ["medical", "medicine", "doctor", "hospital"]):
            return "🏥 Medical"
        elif any(w in desc_lower for w in ["shop", "clothes", "amazon", "flipkart"]):
            return "🛍️ Shopping"
        else:
            return "📦 Other"

    expense_df["category"] = expense_df["description"].apply(categorize)

    # =====================================================
    # CHARTS ROW 1
    # =====================================================

    left, right = st.columns(2)

    # ------- EXPENSE TREND -------
    with left:
        st.subheader("📈 Expense Trend")

        monthly = expense_df.groupby(
            ["month", "month_label"]
        )["amount"].sum().reset_index()

        monthly = monthly.sort_values("month")

        fig_trend = go.Figure()

        fig_trend.add_trace(go.Scatter(
            x=monthly["month_label"],
            y=monthly["amount"],
            mode="lines+markers",
            fill="tozeroy",
            line=dict(
                color="#6366f1",
                width=3,
                shape="spline"
            ),
            marker=dict(
                size=8,
                color="#8b5cf6",
                line=dict(color="#6366f1", width=2),
            ),
            fillcolor="rgba(99,102,241,0.1)",
            name="Expenses",
        ))

        fig_trend.update_layout(
            **PLOTLY_LAYOUT,
            showlegend=False,
            height=350,
        )

        st.plotly_chart(fig_trend, use_container_width=True)

    # ------- EXPENSE DISTRIBUTION -------
    with right:
        st.subheader("🍩 Expense Distribution")

        cat_df = expense_df.groupby(
            "category"
        )["amount"].sum().reset_index()

        cat_df = cat_df.sort_values(
            "amount", ascending=False
        )

        fig_dist = go.Figure(data=[go.Pie(
            labels=cat_df["category"],
            values=cat_df["amount"],
            hole=0.55,
            marker=dict(colors=COLORS),
            textinfo="label+percent",
            textfont=dict(size=12),
            hovertemplate="<b>%{label}</b><br>₹%{value:,.0f}<br>%{percent}<extra></extra>",
        )])

        fig_dist.update_layout(
            **PLOTLY_LAYOUT,
            showlegend=False,
            height=350,
            annotations=[dict(
                text=f"₹{total_expense_amount:,.0f}",
                x=0.5, y=0.5,
                font_size=18,
                font_color="#e2e8f0",
                showarrow=False,
            )],
        )

        st.plotly_chart(fig_dist, use_container_width=True)

    st.divider()

    # =====================================================
    # CHARTS ROW 2
    # =====================================================

    bottom1, bottom2 = st.columns(2)

    # ------- TOP SPENDERS -------
    with bottom1:
        st.subheader("🏆 Top Spenders")

        spender_df = expense_df.groupby(
            "paid_by"
        )["amount"].sum().reset_index()

        spender_df = spender_df.sort_values(
            "amount", ascending=True
        )

        fig_spenders = go.Figure(data=[go.Bar(
            y=spender_df["paid_by"],
            x=spender_df["amount"],
            orientation="h",
            marker=dict(
                color=spender_df["amount"],
                colorscale=[
                    [0, "#6366f1"],
                    [0.5, "#8b5cf6"],
                    [1, "#06b6d4"],
                ],
                cornerradius=6,
            ),
            text=[f"₹{v:,.0f}" for v in spender_df["amount"]],
            textposition="inside",
            textfont=dict(
                color="white",
                size=13,
                family="Inter",
            ),
            hovertemplate="<b>%{y}</b><br>₹%{x:,.0f}<extra></extra>",
        )])

        fig_spenders.update_layout(
            **PLOTLY_LAYOUT,
            showlegend=False,
            height=350,
        )

        st.plotly_chart(fig_spenders, use_container_width=True)

    # ------- AI INSIGHTS -------
    with bottom2:
        st.subheader("🧠 AI Insights")

        insights = []

        # Top category insight
        if not cat_df.empty:
            top_cat = cat_df.iloc[0]
            pct = (top_cat["amount"] / total_expense_amount * 100)
            insights.append({
                "icon": "💡",
                "text": f"<strong>{top_cat['category']}</strong> is the largest spending category at <strong>{pct:.0f}%</strong> of total expenses."
            })

        # Top spender
        if not spender_df.empty:
            top_spender = spender_df.iloc[-1]
            insights.append({
                "icon": "📊",
                "text": f"<strong>{top_spender['paid_by']}</strong> is the top spender with <strong>₹{top_spender['amount']:,.0f}</strong> in total."
            })

        # Monthly trend
        if len(monthly) >= 2:
            latest = monthly.iloc[-1]["amount"]
            prev = monthly.iloc[-2]["amount"]
            if prev > 0:
                change = ((latest - prev) / prev) * 100
                direction = "increased" if change > 0 else "decreased"
                insights.append({
                    "icon": "✨",
                    "text": f"Spending <strong>{direction} {abs(change):.0f}%</strong> compared to last month."
                })

        # Anomaly insight
        if total_anomaly_count > 0:
            high_anom = len([
                a for a in anomalies
                if a.severity == "HIGH"
            ])
            insights.append({
                "icon": "🚨",
                "text": f"<strong>{unresolved_anomalies} unresolved anomalies</strong> detected ({high_anom} high severity)."
            })

        # Average expense
        if total_expense_count > 0:
            avg = total_expense_amount / total_expense_count
            insights.append({
                "icon": "💰",
                "text": f"Average expense amount is <strong>₹{avg:,.0f}</strong> per transaction."
            })

        # Currency mix
        currencies = expense_df["currency"].unique()
        if len(currencies) > 1:
            insights.append({
                "icon": "🌍",
                "text": f"Expenses span <strong>{len(currencies)} currencies</strong>: {', '.join(currencies)}."
            })

        # Pending settlements
        if total_settlement_count > 0:
            insights.append({
                "icon": "🤝",
                "text": f"<strong>₹{total_settlement_amount:,.0f}</strong> settled across <strong>{total_settlement_count}</strong> payments."
            })

        # Build insight cards using HTML (not markdown ** which doesn't render in unsafe_allow_html)
        accent_colors = ["#6366f1", "#8b5cf6", "#06b6d4", "#10b981", "#f59e0b", "#ec4899", "#ef4444"]
        insight_html = ""
        for i, insight in enumerate(insights):
            color = accent_colors[i % len(accent_colors)]
            insight_html += f"""
            <div style="
                padding: 12px 16px;
                margin: 8px 0;
                background: linear-gradient(135deg,
                    rgba({99 + i*15},{102 + i*10},{241 - i*15},0.08),
                    rgba(139,92,246,0.04));
                border-left: 3px solid {color};
                border-radius: 0 12px 12px 0;
                font-size: 14px;
                line-height: 1.5;
                color: #e2e8f0;
            ">
                {insight['icon']} {insight['text']}
            </div>
            """

        if insight_html:
            st.markdown(
                f'<div class="insight-card">{insight_html}</div>',
                unsafe_allow_html=True
            )
        else:
            st.info("Import expense data to see AI-generated insights.")

    st.divider()

    # =====================================================
    # RECENT ACTIVITY
    # =====================================================

    st.subheader("🕐 Recent Activity")

    recent = sorted(
        expenses,
        key=lambda e: e.expense_date or datetime.min.date(),
        reverse=True,
    )[:5]

    if recent:
        cols = st.columns(len(recent))

        for col, exp in zip(cols, recent):
            payer = db.query(User).filter(
                User.id == exp.paid_by
            ).first()

            with col:
                st.markdown(f"""
                <div class="glass-card" style="text-align: center;">
                    <div style="font-size: 24px; margin-bottom: 8px;">
                        {categorize(exp.description or "").split(" ")[0]}
                    </div>
                    <div style="
                        font-size: 13px;
                        color: #e2e8f0;
                        font-weight: 600;
                        margin-bottom: 4px;
                        white-space: nowrap;
                        overflow: hidden;
                        text-overflow: ellipsis;
                    ">{(exp.description or "—")[:20]}</div>
                    <div class="settlement-amount" style="font-size: 18px;">
                        ₹{exp.amount:,.0f}
                    </div>
                    <div style="
                        color: #64748b;
                        font-size: 11px;
                        margin-top: 4px;
                    ">
                        by {payer.name if payer else '—'}
                    </div>
                </div>
                """, unsafe_allow_html=True)

finally:
    db.close()