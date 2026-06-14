import streamlit as st
import os

from database.database import SessionLocal
from database.models import (
    User, Group, GroupMember, Expense, ExpenseParticipant, Settlement, Anomaly, ImportLog
)
from utils.helpers import inject_css, require_auth, sidebar_branding, get_page_config

st.set_page_config(**get_page_config("Settings"))

inject_css()
sidebar_branding()
require_auth()

st.title("⚙️ Settings")
st.caption("Manage SettleWise configurations, account details, and database maintenance")
st.divider()

db = SessionLocal()

try:
    # 1. Account Details Section
    st.subheader("👤 Account Information")
    user_name = st.session_state.get("user_name", "User")
    user_email = st.session_state.get("user_email", "user@gmail.com")
    
    st.markdown(f"""
    <div class="glass-card" style="padding: 20px; border-radius: 12px; margin-bottom: 20px;">
        <p style="margin: 0; font-size: 14px; color: #94a3b8;">Full Name</p>
        <p style="margin: 4px 0 12px 0; font-size: 18px; font-weight: 700; color: #e2e8f0;">{user_name}</p>
        <p style="margin: 0; font-size: 14px; color: #94a3b8;">Email Address</p>
        <p style="margin: 4px 0 0 0; font-size: 18px; font-weight: 700; color: #e2e8f0;">{user_email}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()

    # 2. Preferences / Theme
    st.subheader("🎨 Customization")
    st.toggle("Sleek Dark Mode (Always Active)", value=True, disabled=True, help="SettleWise utilizes a curated premium dark theme configured globally.")
    st.selectbox("System Default Currency", ["INR (₹)", "USD ($)", "EUR (€)", "GBP (£)"], index=0, disabled=True, help="INR is configured as the main transactional base currency.")
    
    st.divider()

    # 3. System Maintenance & Reset
    st.subheader("⚠️ Database Maintenance")
    st.warning("Critical Zone: Resetting database will delete all imported and manual expenses, settlements, group structures, and anomalies permanently. This cannot be undone.")
    
    confirm_reset = st.checkbox("I verify that I want to delete all application data. (Note: Your login account will remain active.)")
    
    if st.button("🚨 Clear All Application Data", type="primary", disabled=not confirm_reset, width="stretch"):
        with st.spinner("Wiping application data..."):
            try:
                # Wiping tables
                db.query(ExpenseParticipant).delete()
                db.query(Expense).delete()
                db.query(Settlement).delete()
                db.query(Anomaly).delete()
                db.query(ImportLog).delete()
                db.query(GroupMember).delete()
                db.query(Group).delete()
                db.query(User).delete()
                
                db.commit()
                st.success("🎉 Database successfully reset! All transaction, group, and member records have been cleared.")
            except Exception as e:
                db.rollback()
                st.error(f"Failed to reset database: {e}")
                
    st.divider()

    # 4. About SettleWise
    st.subheader("ℹ️ About SettleWise")
    st.markdown("""
    **SettleWise** is a production-grade shared expense management & anomaly detection platform designed to streamline financial workflows.
    
    Developed with:
    - **Streamlit** for visual interactive interface
    - **SQLAlchemy & SQLite** for robust data modeling and structured persistence
    - **Pandas & Plotly** for real-time financial dashboards and analytical reporting
    - **Greedy Min-Transactions Algorithm** for smart settlements optimization
    
    *Version 1.1.0 (Build Upgrade)*
    """)

finally:
    db.close()
