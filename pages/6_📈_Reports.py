import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import io
from datetime import datetime

from database.database import SessionLocal
from database.models import (
    User, Group, Expense, Settlement, ImportLog, Anomaly
)
from services.balance_engine import calculate_all_balances
from utils.helpers import inject_css, require_auth, sidebar_branding, get_page_config

st.set_page_config(**get_page_config("Reports & Analytics"))

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

st.title("📈 Reports & Analytics")
st.caption("Deep-dive financial reports, spending patterns, data quality health, and exports")
st.divider()

db = SessionLocal()

try:
    # Fetch core data
    expenses = db.query(Expense).all()
    users = db.query(User).all()
    settlements = db.query(Settlement).all()
    imports = db.query(ImportLog).all()
    anomalies = db.query(Anomaly).all()

    total_users = len(users)
    total_expenses = len(expenses)
    total_settlements = len(settlements)
    total_imports = len(imports)
    total_anomalies = len(anomalies)

    total_expense_amount = sum(e.amount for e in expenses if e.amount) if expenses else 0.0
    total_settlement_amount = sum(s.amount for s in settlements if s.amount) if settlements else 0.0

    # System Health Score
    total_rows_imported = sum(imp.total_rows for imp in imports if imp.total_rows) if imports else 0
    if total_rows_imported > 0:
        health_score = max(0.0, 100.0 - (total_anomalies / total_rows_imported * 100))
    else:
        health_score = 100.0

    # KPI CARDS & HEALTH SCORE
    col1, col2, col3 = st.columns([1, 1, 1.2])

    with col1:
        st.markdown(f"""
        <div class="glass-card" style="text-align: center; height: 160px; padding: 25px 15px;">
            <div style="font-size: 13px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px;">Total Expenses</div>
            <div style="font-size: 32px; font-weight: 800; background: linear-gradient(135deg, #6366f1, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 10px 0;">
                ₹{total_expense_amount:,.0f}
            </div>
            <div style="font-size: 12px; color: #64748b;">{total_expenses} transactions across all groups</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="glass-card" style="text-align: center; height: 160px; padding: 25px 15px;">
            <div style="font-size: 13px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px;">Settlements Recorded</div>
            <div style="font-size: 32px; font-weight: 800; background: linear-gradient(135deg, #06b6d4, #10b981); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 10px 0;">
                ₹{total_settlement_amount:,.0f}
            </div>
            <div style="font-size: 12px; color: #64748b;">{total_settlements} payments recorded</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        health_color = "#10b981" if health_score >= 85 else "#f59e0b" if health_score >= 60 else "#ef4444"
        health_icon = "🟢" if health_score >= 85 else "🟡" if health_score >= 60 else "🔴"
        health_status = "Excellent" if health_score >= 85 else "Fair" if health_score >= 60 else "Critical Issues"
        st.markdown(f"""
        <div class="glass-card" style="text-align: center; height: 160px; padding: 22px 15px;">
            <div style="font-size: 13px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px;">System Data Health</div>
            <div style="font-size: 32px; font-weight: 800; color: {health_color}; margin: 10px 0;">
                {health_score:.1f}%
            </div>
            <div style="font-size: 12px; color: #94a3b8;">
                {health_icon} <strong>{health_status}</strong> ({total_anomalies} anomalies found)
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    if not expenses:
        st.info("No expense data available. Please upload a CSV or manually add expenses first.")
        st.stop()

    # Load data into DataFrame
    expense_records = []
    for e in expenses:
        payer = db.query(User).filter(User.id == e.paid_by).first()
        grp = db.query(Group).filter(Group.id == e.group_id).first()
        expense_records.append({
            "date": e.expense_date,
            "description": e.description or "",
            "amount": e.amount or 0,
            "currency": e.currency or "INR",
            "paid_by": payer.name if payer else "Unknown",
            "group": grp.name if grp else "Unknown",
            "split_type": e.split_type or "equal",
        })
    expense_df = pd.DataFrame(expense_records)
    expense_df["date"] = pd.to_datetime(expense_df["date"], errors="coerce")
    expense_df["month"] = expense_df["date"].dt.strftime("%Y-%m")
    expense_df["month_label"] = expense_df["date"].dt.strftime("%b %Y")

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

    # Tabs for analytics
    st.subheader("📊 Financial Analytics Tabs")
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📅 Monthly Spendings", 
        "🏷️ Category Breakdown", 
        "👤 Per-Member Stacked",
        "👥 Group Spending Report",
        "👩‍👦 Member Spending Summary",
        "⚠️ Anomaly Insights"
    ])

    with tab1:
        monthly_spend = expense_df.groupby(["month", "month_label"])["amount"].sum().reset_index().sort_values("month")
        fig_monthly = go.Figure(data=[go.Bar(
            x=monthly_spend["month_label"],
            y=monthly_spend["amount"],
            marker_color="#6366f1",
            text=[f"₹{v:,.0f}" for v in monthly_spend["amount"]],
            textposition="auto",
            hovertemplate="<b>%{x}</b><br>Spending: ₹%{y:,.2f}<extra></extra>"
        )])
        fig_monthly.update_layout(
            **PLOTLY_LAYOUT,
            title="Total Spendings By Month",
            height=400,
        )
        st.plotly_chart(fig_monthly, width="stretch")

    with tab2:
        cat_df = expense_df.groupby("category")["amount"].sum().reset_index().sort_values("amount", ascending=False)
        fig_cat = go.Figure(data=[go.Pie(
            labels=cat_df["category"],
            values=cat_df["amount"],
            hole=0.55,
            marker=dict(colors=COLORS),
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>Total: ₹%{value:,.2f}<br>%{percent}<extra></extra>"
        )])
        fig_cat.update_layout(
            **PLOTLY_LAYOUT,
            title="Spending Categories Breakdown",
            height=400,
        )
        st.plotly_chart(fig_cat, width="stretch")

    with tab3:
        spender_monthly = expense_df.groupby(["month", "month_label", "paid_by"])["amount"].sum().reset_index().sort_values("month")
        fig_spender = px.bar(
            spender_monthly,
            x="month_label",
            y="amount",
            color="paid_by",
            title="Monthly Spending Breakdown by Payer",
            color_discrete_sequence=COLORS,
            barmode="stack"
        )
        fig_spender.update_layout(
            **PLOTLY_LAYOUT,
            height=400,
            xaxis_title="Month",
            yaxis_title="Total Paid (₹)"
        )
        st.plotly_chart(fig_spender, width="stretch")

    with tab4:
        # Group Spending Report
        st.markdown("##### Spending by Group")
        group_spend = expense_df.groupby("group").agg(
            total_spent=("amount", "sum"),
            avg_spent=("amount", "mean"),
            transactions=("amount", "count")
        ).reset_index().sort_values("total_spent", ascending=False)
        
        group_spend["total_spent"] = group_spend["total_spent"].round(2)
        group_spend["avg_spent"] = group_spend["avg_spent"].round(2)
        
        st.dataframe(group_spend, width="stretch")
        
        # Group distribution pie chart
        fig_grp = px.pie(
            group_spend,
            names="group",
            values="total_spent",
            title="Total Spending Distribution by Group",
            color_discrete_sequence=COLORS,
            hole=0.4
        )
        fig_grp.update_layout(**PLOTLY_LAYOUT, height=350)
        st.plotly_chart(fig_grp, width="stretch")

    with tab5:
        # Member Spending Report
        st.markdown("##### Spending by Member")
        member_spend = expense_df.groupby("paid_by").agg(
            total_paid=("amount", "sum"),
            avg_paid=("amount", "mean"),
            transactions=("amount", "count")
        ).reset_index().sort_values("total_paid", ascending=False)
        
        member_spend["total_paid"] = member_spend["total_paid"].round(2)
        member_spend["avg_paid"] = member_spend["avg_paid"].round(2)
        member_spend["percentage_of_total"] = ((member_spend["total_paid"] / total_expense_amount) * 100).round(1)
        
        st.dataframe(member_spend, width="stretch")
        
        # Member distribution bar chart
        fig_mem_bar = px.bar(
            member_spend,
            x="paid_by",
            y="total_paid",
            text="total_paid",
            title="Total Spending by Member",
            color="paid_by",
            color_discrete_sequence=COLORS
        )
        fig_mem_bar.update_layout(**PLOTLY_LAYOUT, height=350, showlegend=False)
        st.plotly_chart(fig_mem_bar, width="stretch")

    with tab6:
        # Anomaly Report
        st.markdown("##### Data Quality & Anomalies Breakdown")
        
        if anomalies:
            anom_records = [{
                "severity": a.severity,
                "type": a.anomaly_type,
                "status": a.status
            } for a in anomalies]
            anom_df_all = pd.DataFrame(anom_records)
            
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                st.markdown("**Anomalies by Severity**")
                sev_counts = anom_df_all["severity"].value_counts().reset_index()
                sev_counts.columns = ["Severity", "Count"]
                st.dataframe(sev_counts, width="stretch")
                
                fig_sev = px.pie(sev_counts, names="Severity", values="Count", color_discrete_sequence=["#ef4444", "#f59e0b", "#10b981"])
                fig_sev.update_layout(**PLOTLY_LAYOUT, height=250)
                st.plotly_chart(fig_sev, width="stretch")
                
            with col_a2:
                st.markdown("**Anomalies by Status**")
                stat_counts = anom_df_all["status"].value_counts().reset_index()
                stat_counts.columns = ["Status", "Count"]
                st.dataframe(stat_counts, width="stretch")
                
                fig_stat = px.bar(stat_counts, x="Status", y="Count", color="Status", color_discrete_sequence=["#ef4444", "#10b981"])
                fig_stat.update_layout(**PLOTLY_LAYOUT, height=250, showlegend=False)
                st.plotly_chart(fig_stat, width="stretch")
        else:
            st.success("Clean report: No anomalies detected in the database!")

    st.divider()

    # =====================================================
    # CSV IMPORT LOG & HEALTH LOGS
    # =====================================================
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("📥 CSV Import Logs")
        if imports:
            import_data = []
            for imp in imports:
                import_data.append({
                    "Date": imp.imported_at.strftime("%Y-%m-%d %H:%M") if imp.imported_at else "—",
                    "Filename": imp.file_name or "—",
                    "Total Rows": imp.total_rows,
                    "Imported": imp.imported_rows,
                    "Anomalies": imp.anomalies_found
                })
            st.dataframe(pd.DataFrame(import_data), width="stretch", height=250)
        else:
            st.info("No import logs recorded.")

    with col_b:
        st.subheader("🚨 Unresolved Anomalies")
        unresolved_anom = [a for a in anomalies if a.status == "PENDING"]
        if unresolved_anom:
            anom_data = []
            for anom in unresolved_anom:
                anom_data.append({
                    "Row": anom.row_number,
                    "Type": anom.anomaly_type,
                    "Severity": anom.severity,
                    "Description": anom.description,
                })
            anom_df = pd.DataFrame(anom_data)
            
            def style_anom(val):
                if val == "HIGH":
                    return "color: #ef4444; font-weight: bold"
                elif val == "MEDIUM":
                    return "color: #f59e0b; font-weight: bold"
                return "color: #10b981"
            
            styled_anom = anom_df.style.map(style_anom, subset=["Severity"])
            st.dataframe(styled_anom, width="stretch", height=250)
        else:
            st.success("✅ Clean system health — all anomalies resolved or none found!")

    st.divider()

    # =====================================================
    # EXPORTS & DOWNLOAD CENTER
    # =====================================================
    st.subheader("📥 Export & Reports Center")
    st.caption("Download reports and database exports in multiple formats")

    ex1, ex2, ex3, ex4 = st.columns(4)

    # ------- 1. EXPORT EXPENSES CSV -------
    with ex1:
        st.markdown("""
        <div class="glass-card" style="text-align: center; height: 180px; padding: 20px 10px;">
            <div style="font-size: 32px; margin-bottom: 5px;">📊</div>
            <div style="font-weight: 700; font-size: 15px; color: #e2e8f0;">Expenses (CSV)</div>
            <div style="font-size: 12px; color: #94a3b8; margin: 8px 0 15px 0;">All cleaned expenses currently in the database</div>
        </div>
        """, unsafe_allow_html=True)
        
        csv_expenses = expense_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download CSV",
            data=csv_expenses,
            file_name=f"settlewise_expenses_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            width="stretch"
        )

    # ------- 2. EXPORT SETTLEMENTS CSV -------
    with ex2:
        st.markdown("""
        <div class="glass-card" style="text-align: center; height: 180px; padding: 20px 10px;">
            <div style="font-size: 32px; margin-bottom: 5px;">📜</div>
            <div style="font-weight: 700; font-size: 15px; color: #e2e8f0;">Settlements (CSV)</div>
            <div style="font-size: 12px; color: #94a3b8; margin: 8px 0 15px 0;">Ledger of all completed and recorded payments</div>
        </div>
        """, unsafe_allow_html=True)

        settlement_records = []
        for s in settlements:
            p = db.query(User).filter(User.id == s.payer_id).first()
            r = db.query(User).filter(User.id == s.receiver_id).first()
            settlement_records.append({
                "date": s.settlement_date,
                "payer": p.name if p else "Unknown",
                "receiver": r.name if r else "Unknown",
                "amount": s.amount,
                "notes": s.notes or ""
            })
        settlement_df = pd.DataFrame(settlement_records)
        csv_settlements = settlement_df.to_csv(index=False).encode('utf-8')

        st.download_button(
            label="⬇️ Download CSV",
            data=csv_settlements,
            file_name=f"settlewise_settlements_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            width="stretch"
        )

    # ------- 3. EXPORT EXCEL FILE -------
    with ex3:
        st.markdown("""
        <div class="glass-card" style="text-align: center; height: 180px; padding: 20px 10px;">
            <div style="font-size: 32px; margin-bottom: 5px;">📈</div>
            <div style="font-weight: 700; font-size: 15px; color: #e2e8f0;">Full Audit (Excel)</div>
            <div style="font-size: 12px; color: #94a3b8; margin: 8px 0 15px 0;">Full data report with all sheets in an XLSX file</div>
        </div>
        """, unsafe_allow_html=True)

        anomaly_records = []
        for a in anomalies:
            anomaly_records.append({
                "row_number": a.row_number,
                "type": a.anomaly_type,
                "severity": a.severity,
                "description": a.description,
                "status": a.status,
                "action_taken": a.action_taken or ""
            })
        excel_anom_df = pd.DataFrame(anomaly_records)
        
        # Build Excel binary
        excel_output = io.BytesIO()
        with pd.ExcelWriter(excel_output, engine='openpyxl') as writer:
            expense_df.to_excel(writer, sheet_name='Expenses', index=False)
            settlement_df.to_excel(writer, sheet_name='Settlements', index=False)
            excel_anom_df.to_excel(writer, sheet_name='Anomalies', index=False)
        
        st.download_button(
            label="⬇️ Download Excel",
            data=excel_output.getvalue(),
            file_name=f"settlewise_full_audit_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch"
        )

    # ------- 4. EXPORT HTML SUMMARY -------
    with ex4:
        st.markdown("""
        <div class="glass-card" style="text-align: center; height: 180px; padding: 20px 10px;">
            <div style="font-size: 32px; margin-bottom: 5px;">📄</div>
            <div style="font-weight: 700; font-size: 15px; color: #e2e8f0;">Summary (HTML)</div>
            <div style="font-size: 12px; color: #94a3b8; margin: 8px 0 15px 0;">Print-ready invoice/summary report with balances</div>
        </div>
        """, unsafe_allow_html=True)

        all_balances = calculate_all_balances(db)
        
        balance_rows_html = ""
        for uid, info in all_balances.items():
            bal = info["balance"]
            bal_style = "color: #10b981; font-weight: bold;" if bal >= 0 else "color: #ef4444; font-weight: bold;"
            balance_rows_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{info['name']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; text-align: right; {bal_style}">
                    ₹{bal:,.2f}
                </td>
            </tr>
            """

        recent_expenses_html = ""
        for idx, row in expense_df.head(10).iterrows():
            recent_expenses_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{row['date'].strftime('%Y-%m-%d') if pd.notna(row['date']) else '—'}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{row['description']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{row['paid_by']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; text-align: right;">₹{row['amount']:,.2f}</td>
            </tr>
            """

        recent_settlements_html = ""
        for rec in settlement_records[:10]:
            recent_settlements_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{rec['date'].strftime('%Y-%m-%d') if rec['date'] else '—'}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{rec['payer']} → {rec['receiver']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; text-align: right; color: #10b981; font-weight: bold;">₹{rec['amount']:,.2f}</td>
            </tr>
            """

        html_report = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>SettleWise Group Settlement Summary Report</title>
    <style>
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            color: #1e293b;
            background-color: #f8fafc;
            margin: 0;
            padding: 40px;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: #ffffff;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .logo {{
            font-size: 24px;
            font-weight: 800;
            color: #6366f1;
        }}
        .title {{
            text-align: right;
        }}
        .title h1 {{
            margin: 0;
            font-size: 22px;
            color: #0f172a;
        }}
        .title p {{
            margin: 5px 0 0 0;
            font-size: 13px;
            color: #64748b;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: #f1f5f9;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
        .card-label {{
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #64748b;
            font-weight: 600;
        }}
        .card-val {{
            font-size: 20px;
            font-weight: 800;
            color: #0f172a;
            margin-top: 5px;
        }}
        h2 {{
            font-size: 16px;
            color: #0f172a;
            border-left: 4px solid #6366f1;
            padding-left: 10px;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            margin-bottom: 20px;
        }}
        th {{
            background-color: #f8fafc;
            text-align: left;
            padding: 10px;
            font-weight: 600;
            color: #475569;
            border-bottom: 2px solid #e2e8f0;
        }}
        .btn-print {{
            display: block;
            width: 100%;
            text-align: center;
            background: #6366f1;
            color: white;
            padding: 12px;
            border-radius: 8px;
            font-weight: 600;
            text-decoration: none;
            margin-top: 40px;
            box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.2);
            transition: background 0.2s;
        }}
        .btn-print:hover {{
            background: #4f46e5;
        }}
        @media print {{
            body {{
                background-color: #ffffff;
                padding: 0;
            }}
            .container {{
                box-shadow: none;
                padding: 0;
            }}
            .btn-print {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">💰 SettleWise</div>
            <div class="title">
                <h1>Financial Summary Report</h1>
                <p>Generated on {datetime.now().strftime('%d %b %Y, %H:%M')}</p>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <div class="card-label">Total Spends</div>
                <div class="card-val">₹{total_expense_amount:,.2f}</div>
            </div>
            <div class="card">
                <div class="card-label">Active Members</div>
                <div class="card-val">{total_users}</div>
            </div>
            <div class="card">
                <div class="card-label">Settled Ledgers</div>
                <div class="card-val">₹{total_settlement_amount:,.2f}</div>
            </div>
            <div class="card">
                <div class="card-label">Data Health</div>
                <div class="card-val">{health_score:.1f}%</div>
            </div>
        </div>

        <h2>⚖️ User Net Balances</h2>
        <table>
            <thead>
                <tr>
                    <th style="width: 60%;">User</th>
                    <th style="width: 40%; text-align: right;">Net Balance</th>
                </tr>
            </thead>
            <tbody>
                {balance_rows_html}
            </tbody>
        </table>

        <h2>💸 Recent Group Expenses (Max 10)</h2>
        <table>
            <thead>
                <tr>
                    <th style="width: 20%;">Date</th>
                    <th style="width: 45%;">Description</th>
                    <th style="width: 20%;">Paid By</th>
                    <th style="width: 15%; text-align: right;">Amount</th>
                </tr>
            </thead>
            <tbody>
                {recent_expenses_html}
            </tbody>
        </table>

        <h2>🤝 Settlement History Ledger (Max 10)</h2>
        <table>
            <thead>
                <tr>
                    <th style="width: 20%;">Date</th>
                    <th style="width: 60%;">Payment Flow</th>
                    <th style="width: 20%; text-align: right;">Amount</th>
                </tr>
            </thead>
            <tbody>
                {recent_settlements_html}
            </tbody>
        </table>

        <a href="#" onclick="window.print(); return false;" class="btn-print">🖨️ Print Report or Save as PDF</a>
    </div>
</body>
</html>
"""

        st.download_button(
            label="⬇️ Download Summary",
            data=html_report.encode('utf-8'),
            file_name=f"settlewise_summary_report_{datetime.now().strftime('%Y%m%d')}.html",
            mime="text/html",
            width="stretch"
        )

finally:
    db.close()