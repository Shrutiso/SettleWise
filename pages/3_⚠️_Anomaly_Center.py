import streamlit as st
from utils.helpers import inject_css, require_auth, sidebar_branding, get_page_config
from database.database import SessionLocal
from database.models import Anomaly

st.set_page_config(**get_page_config("Anomaly Center"))

inject_css()
sidebar_branding()
require_auth()

st.title("🚨 Anomaly Center")
st.caption("Review and manage data quality issues and expense anomalies")
st.divider()

db = SessionLocal()

try:
    # Get all anomalies first for summary stats
    all_anomalies = db.query(Anomaly).all()

    high_count = len([a for a in all_anomalies if a.severity == "HIGH"])
    medium_count = len([a for a in all_anomalies if a.severity == "MEDIUM"])
    low_count = len([a for a in all_anomalies if a.severity == "LOW"])
    pending_count = len([a for a in all_anomalies if a.status == "PENDING"])
    resolved_count = len([a for a in all_anomalies if a.status == "RESOLVED"])

    # KPI dashboard
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        st.metric("Total Anomalies", len(all_anomalies))
    with kpi2:
        st.metric("Pending", pending_count)
    with kpi3:
        st.metric("High Severity", high_count)
    with kpi4:
        st.metric("Medium Severity", medium_count)
    with kpi5:
        st.metric("Low Severity", low_count)

    st.divider()

    # Filters
    st.subheader("🔍 Filters")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        severity_filter = st.selectbox(
            "Filter by Severity",
            ["ALL", "HIGH", "MEDIUM", "LOW"]
        )
    with col_f2:
        status_filter = st.selectbox(
            "Filter by Status",
            ["ALL", "PENDING", "RESOLVED"]
        )

    # Query matching filters
    query = db.query(Anomaly)
    if severity_filter != "ALL":
        query = query.filter(Anomaly.severity == severity_filter)
    if status_filter != "ALL":
        query = query.filter(Anomaly.status == status_filter)
    
    filtered_anomalies = query.all()

    # Display Table
    st.subheader("📋 Detected Anomalies")
    if filtered_anomalies:
        rows = []
        for anomaly in filtered_anomalies:
            rows.append({
                "ID": anomaly.id,
                "Row Number": anomaly.row_number,
                "Type": anomaly.anomaly_type,
                "Severity": anomaly.severity,
                "Description": anomaly.description,
                "Action Taken": anomaly.action_taken or "None",
                "Status": anomaly.status
            })
        st.dataframe(rows, width="stretch", height=400)
    else:
        st.success("🎉 No anomalies found matching the criteria!")

    st.divider()

    # Action section
    st.subheader("⚡ Actions")

    if all_anomalies:
        # User-friendly labels for dropdown
        anomaly_options = {
            a.id: f"#{a.id} - {a.anomaly_type} ({a.severity}) | Status: {a.status} | {a.description[:40]}..."
            for a in all_anomalies
        }
        
        selected_id = st.selectbox(
            "Select Anomaly to Action",
            options=list(anomaly_options.keys()),
            format_func=lambda x: anomaly_options[x]
        )

        selected_anomaly = db.query(Anomaly).filter(Anomaly.id == selected_id).first()

        if selected_anomaly:
            st.info(f"**Selected:** {selected_anomaly.description}")
            
            act1, act2 = st.columns(2)
            with act1:
                # Mark as Resolved button
                if selected_anomaly.status != "RESOLVED":
                    if st.button("✅ Mark as Resolved", width="stretch", type="primary"):
                        selected_anomaly.status = "RESOLVED"
                        selected_anomaly.action_taken = "Manually reviewed and resolved by user."
                        db.commit()
                        st.success(f"Anomaly #{selected_id} marked as RESOLVED.")
                        st.rerun()
                else:
                    st.button("✅ Mark as Resolved", width="stretch", disabled=True)
            
            with act2:
                # Reopen button
                if selected_anomaly.status != "PENDING":
                    if st.button("🔄 Reopen Anomaly", width="stretch"):
                        selected_anomaly.status = "PENDING"
                        selected_anomaly.action_taken = "Reopened for review."
                        db.commit()
                        st.warning(f"Anomaly #{selected_id} reopened (status set to PENDING).")
                        st.rerun()
                else:
                    st.button("🔄 Reopen Anomaly", width="stretch", disabled=True)
    else:
        st.info("No anomalies available to action.")

finally:
    db.close()