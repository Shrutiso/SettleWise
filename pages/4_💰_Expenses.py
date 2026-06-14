import streamlit as st
import os
from datetime import date, datetime
from database.database import SessionLocal
from database.models import Expense, Group, User, GroupMember, ExpenseParticipant
from services.currency_converter import convert_to_inr
from utils.helpers import inject_css, require_auth, sidebar_branding, get_page_config

st.set_page_config(**get_page_config("Expenses"))

inject_css()
sidebar_branding()
require_auth()

st.title("💰 Expense Management")
st.caption("Add, view, filter, edit, or delete expenses")
st.divider()

db = SessionLocal()

try:
    # Load all groups and users
    groups = db.query(Group).all()
    users = db.query(User).all()

    if not groups:
        st.warning("⚠️ Please create a group first on the **Groups** page.")
        st.stop()

    if not users:
        st.warning("⚠️ Please create users first.")
        st.stop()

    # We will use tabs to separate Add, Edit, and View/Filter functionalities
    tab_view, tab_add, tab_edit = st.tabs(["📋 View Expense History", "➕ Add New Expense", "✏️ Edit Expense"])

    # =====================================================
    # TAB 1: VIEW & FILTER EXPENSES
    # =====================================================
    with tab_view:
        st.subheader("🔍 Filters")
        
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        
        with f_col1:
            filter_group = st.selectbox(
                "Filter by Group",
                ["ALL"] + [g.name for g in groups]
            )
        
        with f_col2:
            filter_payer = st.selectbox(
                "Filter by Payer",
                ["ALL"] + [u.name for u in users]
            )
            
        with f_col3:
            filter_start_date = st.date_input("From Date", value=date(2020, 1, 1))
            
        with f_col4:
            filter_end_date = st.date_input("To Date", value=date.today())

        # Build Query
        query = db.query(Expense)
        
        if filter_group != "ALL":
            selected_g = db.query(Group).filter(Group.name == filter_group).first()
            if selected_g:
                query = query.filter(Expense.group_id == selected_g.id)
                
        if filter_payer != "ALL":
            selected_u = db.query(User).filter(User.name == filter_payer).first()
            if selected_u:
                query = query.filter(Expense.paid_by == selected_u.id)
                
        query = query.filter(Expense.expense_date >= filter_start_date)
        query = query.filter(Expense.expense_date <= filter_end_date)
        
        filtered_expenses = query.order_by(Expense.expense_date.desc()).all()
        
        st.subheader("Expense List")
        if not filtered_expenses:
            st.info("No expenses found matching the filter criteria.")
        else:
            expense_rows = []
            for exp in filtered_expenses:
                grp_name = exp.group.name if exp.group else "Deleted Group"
                payer_name = exp.payer.name if exp.payer else "Deleted User"
                
                # Get participants names
                participants_names = ", ".join([p.user.name for p in exp.participants if p.user])
                
                expense_rows.append({
                    "ID": exp.id,
                    "Group": grp_name,
                    "Description": exp.description,
                    "Amount (INR)": exp.amount,
                    "Date": exp.expense_date,
                    "Paid By": payer_name,
                    "Split Type": exp.split_type,
                    "Participants": participants_names,
                    "Notes": exp.notes or ""
                })
            
            st.dataframe(expense_rows, width="stretch", height=400)

    # =====================================================
    # TAB 2: ADD NEW EXPENSE
    # =====================================================
    with tab_add:
        st.subheader("Add New Expense")
        
        add_col1, add_col2 = st.columns(2)
        
        with add_col1:
            selected_group = st.selectbox(
                "Select Group",
                groups,
                format_func=lambda x: x.name,
                key="add_group_select"
            )
            
            # Fetch active group members
            group_members = db.query(User).join(GroupMember, User.id == GroupMember.user_id).filter(
                GroupMember.group_id == selected_group.id,
                GroupMember.status == "ACTIVE"
            ).all()
            
            if not group_members:
                st.error("This group has no active members! Add members in the **Groups** page.")
                group_members = []
            
            payer = st.selectbox(
                "Paid By",
                group_members,
                format_func=lambda x: x.name if x else "N/A",
                key="add_payer_select"
            )
            
            description = st.text_input("Expense Description", placeholder="e.g. Dinner, Taxi", key="add_desc")
            
            amount = st.number_input("Amount", min_value=0.0, step=10.0, key="add_amount")
            
            currency = st.selectbox("Currency", ["INR", "USD", "EUR", "GBP"], key="add_currency")
            
            expense_date = st.date_input("Expense Date", value=date.today(), key="add_date")

        with add_col2:
            st.markdown("**Split Details**")
            
            if group_members:
                participants = st.multiselect(
                    "Participating Members",
                    group_members,
                    default=group_members,
                    format_func=lambda x: x.name,
                    key="add_participants"
                )
            else:
                participants = []
                
            split_type = st.selectbox(
                "Split Type",
                ["equal", "exact", "percentage", "shares"],
                key="add_split_type"
            )
            
            notes = st.text_area("Notes / Details", placeholder="Additional comments...", key="add_notes")
            
            # Dynamic inputs based on split type
            split_inputs = {}
            if participants and split_type in ["exact", "percentage", "shares"]:
                st.markdown("##### Split Breakdown")
                for p in participants:
                    if split_type == "exact":
                        split_inputs[p.id] = st.number_input(f"Share for {p.name} (in original currency)", min_value=0.0, step=1.0, key=f"add_exact_{p.id}")
                    elif split_type == "percentage":
                        split_inputs[p.id] = st.number_input(f"Percentage for {p.name} (%)", min_value=0.0, max_value=100.0, step=5.0, key=f"add_pct_{p.id}")
                    elif split_type == "shares":
                        split_inputs[p.id] = st.number_input(f"Shares/Units for {p.name}", min_value=0.0, value=1.0, step=1.0, key=f"add_share_{p.id}")

        if st.button("🚀 Save Expense", width="stretch", type="primary", key="save_new_exp_btn"):
            if not group_members:
                st.error("No active members in selected group.")
            elif not payer:
                st.error("Please specify who paid.")
            elif not description.strip():
                st.error("Description is required.")
            elif amount <= 0:
                st.error("Amount must be greater than 0.")
            elif not participants:
                st.error("At least one participant must be selected.")
            else:
                # Validation checks on inputs
                valid = True
                if split_type == "exact":
                    total_exact = sum(split_inputs[p.id] for p in participants)
                    if abs(total_exact - amount) > 0.01:
                        st.error(f"Sum of exact splits ({total_exact}) must equal the total amount ({amount}).")
                        valid = False
                elif split_type == "percentage":
                    total_pct = sum(split_inputs[p.id] for p in participants)
                    if abs(total_pct - 100.0) > 0.01:
                        st.error(f"Sum of percentages ({total_pct}%) must equal 100%.")
                        valid = False
                
                if valid:
                    # Convert to INR
                    inr_amount = convert_to_inr(amount, currency)
                    
                    # Generate notes with conversion log if necessary
                    final_notes = notes.strip()
                    if currency != "INR":
                        original_info = f"[Original: {amount} {currency}]"
                        final_notes = f"{original_info} {final_notes}".strip()
                    
                    # 1. Create Expense
                    new_exp = Expense(
                        group_id=selected_group.id,
                        description=description.strip(),
                        amount=inr_amount,
                        currency="INR", # We store all clean data in INR
                        expense_date=expense_date,
                        paid_by=payer.id,
                        split_type=split_type,
                        notes=final_notes
                    )
                    
                    db.add(new_exp)
                    db.flush() # Get the new_exp.id
                    
                    # 2. Add Participants
                    num_p = len(participants)
                    total_assigned_inr = 0.0
                    participants_data = []
                    
                    for p in participants:
                        share_amount = 0.0
                        share_percentage = None
                        share_units = None
                        
                        if split_type == "equal":
                            share_amount = round(inr_amount / num_p, 2)
                        elif split_type == "exact":
                            # Split details are in original currency, convert each to INR
                            p_orig_amount = split_inputs[p.id]
                            share_amount = convert_to_inr(p_orig_amount, currency)
                        elif split_type == "percentage":
                            share_percentage = split_inputs[p.id]
                            share_amount = round(inr_amount * (share_percentage / 100.0), 2)
                        elif split_type == "shares":
                            share_units = split_inputs[p.id]
                            total_units = sum(split_inputs[part.id] for part in participants)
                            if total_units > 0:
                                share_amount = round(inr_amount * (share_units / total_units), 2)
                            else:
                                share_amount = round(inr_amount / num_p, 2)
                                
                        participants_data.append({
                            "user_id": p.id,
                            "share_amount": share_amount,
                            "share_percentage": share_percentage,
                            "share_units": share_units
                        })
                        total_assigned_inr += share_amount
                    
                    # Rounding correction on the last participant
                    if participants_data and num_p > 0:
                        diff = round(inr_amount - total_assigned_inr, 2)
                        if diff != 0.0:
                            participants_data[-1]["share_amount"] = round(participants_data[-1]["share_amount"] + diff, 2)
                            
                    # Save participants
                    for p_data in participants_data:
                        ep = ExpenseParticipant(
                            expense_id=new_exp.id,
                            user_id=p_data["user_id"],
                            share_amount=p_data["share_amount"],
                            share_percentage=p_data["share_percentage"],
                            share_units=p_data["share_units"]
                        )
                        db.add(ep)
                        
                    db.commit()
                    st.success("🎉 Expense added and participant splits created successfully!")
                    st.rerun()

    # =====================================================
    # TAB 3: EDIT & DELETE EXPENSE
    # =====================================================
    with tab_edit:
        st.subheader("Edit or Delete Expense")
        
        all_expenses = db.query(Expense).order_by(Expense.id.desc()).all()
        
        if not all_expenses:
            st.info("No expenses available to edit.")
        else:
            expense_options = {
                e.id: f"#{e.id} - {e.description} ({e.amount} INR) | Paid by: {e.payer.name if e.payer else 'Deleted'} | Date: {e.expense_date}"
                for e in all_expenses
            }
            
            selected_edit_id = st.selectbox(
                "Select Expense to Edit/Delete",
                options=list(expense_options.keys()),
                format_func=lambda x: expense_options[x],
                key="edit_exp_select"
            )
            
            selected_exp = db.query(Expense).filter(Expense.id == selected_edit_id).first()
            
            if selected_exp:
                st.markdown("---")
                
                # Fetch active group members for the selected group
                edit_group_members = db.query(User).join(GroupMember, User.id == GroupMember.user_id).filter(
                    GroupMember.group_id == selected_exp.group_id,
                    GroupMember.status == "ACTIVE"
                ).all()
                
                # Current participants
                curr_participant_ids = [p.user_id for p in selected_exp.participants]
                curr_participants = [u for u in edit_group_members if u.id in curr_participant_ids]
                
                edit_col1, edit_col2 = st.columns(2)
                
                with edit_col1:
                    edit_description = st.text_input("Expense Description", value=selected_exp.description, key="edit_desc")
                    
                    edit_amount = st.number_input("Amount (INR)", min_value=0.0, value=selected_exp.amount, step=10.0, key="edit_amount")
                    
                    edit_payer = st.selectbox(
                        "Paid By",
                        edit_group_members,
                        index=edit_group_members.index(selected_exp.payer) if selected_exp.payer in edit_group_members else 0,
                        format_func=lambda x: x.name if x else "N/A",
                        key="edit_payer_select"
                    )
                    
                    edit_expense_date = st.date_input("Expense Date", value=selected_exp.expense_date, key="edit_date")

                with edit_col2:
                    st.markdown("**Split Details**")
                    
                    edit_participants = st.multiselect(
                        "Participating Members",
                        edit_group_members,
                        default=curr_participants if curr_participants else edit_group_members,
                        format_func=lambda x: x.name,
                        key="edit_participants"
                    )
                    
                    edit_split_type = st.selectbox(
                        "Split Type",
                        ["equal", "exact", "percentage", "shares"],
                        index=["equal", "exact", "percentage", "shares"].index(selected_exp.split_type) if selected_exp.split_type in ["equal", "exact", "percentage", "shares"] else 0,
                        key="edit_split_type"
                    )
                    
                    # Clean note display without prefix
                    clean_notes = selected_exp.notes or ""
                    
                    edit_notes = st.text_area("Notes", value=clean_notes, key="edit_notes")
                    
                    # Pre-fill inputs for edit based on split type
                    edit_inputs = {}
                    if edit_participants and edit_split_type in ["exact", "percentage", "shares"]:
                        st.markdown("##### Split Breakdown")
                        
                        # Find existing splits
                        existing_splits = {p.user_id: p for p in selected_exp.participants}
                        
                        for p in edit_participants:
                            existing = existing_splits.get(p.id)
                            
                            if edit_split_type == "exact":
                                val = existing.share_amount if (existing and selected_exp.split_type == "exact") else 0.0
                                edit_inputs[p.id] = st.number_input(f"Share for {p.name} (INR)", min_value=0.0, value=val, step=10.0, key=f"edit_exact_{p.id}")
                                
                            elif edit_split_type == "percentage":
                                val = existing.share_percentage if (existing and selected_exp.split_type == "percentage") else 0.0
                                edit_inputs[p.id] = st.number_input(f"Percentage for {p.name} (%)", min_value=0.0, max_value=100.0, value=val, step=5.0, key=f"edit_pct_{p.id}")
                                
                            elif edit_split_type == "shares":
                                val = existing.share_units if (existing and selected_exp.split_type == "shares") else 1.0
                                edit_inputs[p.id] = st.number_input(f"Shares/Units for {p.name}", min_value=0.0, value=val, step=1.0, key=f"edit_share_{p.id}")

                # Save / Delete buttons
                st.markdown("<br/>", unsafe_allow_html=True)
                btn_col1, btn_col2 = st.columns(2)
                
                with btn_col1:
                    if st.button("💾 Save Changes", width="stretch", type="primary", key="save_edit_btn"):
                        if not edit_description.strip():
                            st.error("Description is required.")
                        elif edit_amount <= 0:
                            st.error("Amount must be greater than 0.")
                        elif not edit_participants:
                            st.error("At least one participant must be selected.")
                        else:
                            # Validation
                            valid = True
                            if edit_split_type == "exact":
                                total_exact = sum(edit_inputs[p.id] for p in edit_participants)
                                if abs(total_exact - edit_amount) > 0.01:
                                    st.error(f"Sum of exact splits ({total_exact}) must equal the total amount ({edit_amount}).")
                                    valid = False
                            elif edit_split_type == "percentage":
                                total_pct = sum(edit_inputs[p.id] for p in edit_participants)
                                if abs(total_pct - 100.0) > 0.01:
                                    st.error(f"Sum of percentages ({total_pct}%) must equal 100%.")
                                    valid = False
                            
                            if valid:
                                # Update Expense
                                selected_exp.description = edit_description.strip()
                                selected_exp.amount = edit_amount
                                selected_exp.payer = edit_payer
                                selected_exp.expense_date = edit_expense_date
                                selected_exp.split_type = edit_split_type
                                selected_exp.notes = edit_notes.strip()
                                
                                # Clear and recreate participants
                                db.query(ExpenseParticipant).filter(ExpenseParticipant.expense_id == selected_exp.id).delete()
                                
                                num_p = len(edit_participants)
                                total_assigned_inr = 0.0
                                participants_data = []
                                
                                for p in edit_participants:
                                    share_amount = 0.0
                                    share_percentage = None
                                    share_units = None
                                    
                                    if edit_split_type == "equal":
                                        share_amount = round(edit_amount / num_p, 2)
                                    elif edit_split_type == "exact":
                                        share_amount = edit_inputs[p.id]
                                    elif edit_split_type == "percentage":
                                        share_percentage = edit_inputs[p.id]
                                        share_amount = round(edit_amount * (share_percentage / 100.0), 2)
                                    elif edit_split_type == "shares":
                                        share_units = edit_inputs[p.id]
                                        total_units = sum(edit_inputs[part.id] for part in edit_participants)
                                        if total_units > 0:
                                            share_amount = round(edit_amount * (share_units / total_units), 2)
                                        else:
                                            share_amount = round(edit_amount / num_p, 2)
                                            
                                    participants_data.append({
                                        "user_id": p.id,
                                        "share_amount": share_amount,
                                        "share_percentage": share_percentage,
                                        "share_units": share_units
                                    })
                                    total_assigned_inr += share_amount
                                
                                # Rounding correction on the last participant
                                if participants_data and num_p > 0:
                                    diff = round(edit_amount - total_assigned_inr, 2)
                                    if diff != 0.0:
                                        participants_data[-1]["share_amount"] = round(participants_data[-1]["share_amount"] + diff, 2)
                                        
                                # Save participants
                                for p_data in participants_data:
                                    ep = ExpenseParticipant(
                                        expense_id=selected_exp.id,
                                        user_id=p_data["user_id"],
                                        share_amount=p_data["share_amount"],
                                        share_percentage=p_data["share_percentage"],
                                        share_units=p_data["share_units"]
                                    )
                                    db.add(ep)
                                    
                                db.commit()
                                st.success("🎉 Expense changes saved successfully!")
                                st.rerun()
                                
                with btn_col2:
                    st.warning("⚠️ Critical Zone")
                    confirm_delete = st.checkbox("Confirm Delete", key="confirm_delete_expense_chk")
                    if st.button("🗑️ Delete Expense", width="stretch", type="primary", disabled=not confirm_delete, key="delete_exp_btn"):
                        db.delete(selected_exp)
                        db.commit()
                        st.success("Expense deleted successfully!")
                        st.rerun()

finally:
    db.close()