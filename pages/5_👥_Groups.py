import streamlit as st
import os
from datetime import date
from database.database import SessionLocal
from database.models import Group, User, GroupMember, Expense
from utils.helpers import inject_css, require_auth, sidebar_branding, get_page_config

st.set_page_config(**get_page_config("Group Management"))

inject_css()
sidebar_branding()
require_auth()

st.title("👥 Group & Member Management")
st.caption("Manage shared expense groups, group members, and memberships")
st.divider()

db = SessionLocal()

try:
    groups = db.query(Group).all()
    users = db.query(User).all()

    tab_overview, tab_create, tab_memberships = st.tabs([
        "📋 Groups & Members Overview", 
        "➕ Create Group / User", 
        "🔗 Manage Memberships"
    ])

    # ==================================================
    # TAB 1: OVERVIEW & ACTIONS (Rename, Delete)
    # ==================================================
    with tab_overview:
        st.subheader("Existing Groups")
        if not groups:
            st.info("No groups found. Go to the 'Create' tab to add a new group.")
        else:
            for g in groups:
                # Get member counts
                active_member_count = db.query(GroupMember).filter(
                    GroupMember.group_id == g.id,
                    GroupMember.status == "ACTIVE"
                ).count()
                
                expense_count = db.query(Expense).filter(Expense.group_id == g.id).count()
                
                with st.expander(f"📁 {g.name} — ({active_member_count} active members, {expense_count} expenses)"):
                    # Inline rename form
                    col_rename, col_delete = st.columns([6, 4])
                    
                    with col_rename:
                        st.markdown("**Rename Group**")
                        new_name = st.text_input("New Name", value=g.name, key=f"rename_input_{g.id}")
                        if st.button("Save New Name", key=f"rename_btn_{g.id}"):
                            if not new_name.strip():
                                st.error("Group name cannot be empty.")
                            else:
                                existing = db.query(Group).filter(Group.name == new_name.strip(), Group.id != g.id).first()
                                if existing:
                                    st.error("A group with this name already exists.")
                                else:
                                    g.name = new_name.strip()
                                    db.commit()
                                    st.success("Group renamed successfully!")
                                    st.rerun()
                                    
                    with col_delete:
                        st.markdown("**Delete Group (Critical)**")
                        st.warning("Deletes group, all memberships, and expenses!")
                        confirm = st.checkbox("Confirm Deletion", key=f"confirm_del_{g.id}")
                        if st.button("🗑️ Delete Group", type="primary", disabled=not confirm, key=f"del_btn_{g.id}"):
                            db.delete(g)
                            db.commit()
                            st.success(f"Group '{g.name}' deleted successfully!")
                            st.rerun()

        st.divider()
        st.subheader("Active Group Memberships")
        memberships = db.query(GroupMember).filter(GroupMember.status == "ACTIVE").all()
        if memberships:
            rows = []
            for m in memberships:
                rows.append({
                    "Group": m.group.name if m.group else "N/A",
                    "Member": m.user.name if m.user else "N/A",
                    "Joined Date": m.joined_on
                })
            st.dataframe(rows, width="stretch", height=300)
        else:
            st.info("No active memberships.")

    # ==================================================
    # TAB 2: CREATE GROUP & CREATE USER
    # ==================================================
    with tab_create:
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            st.subheader("Create New Group")
            new_group_name = st.text_input("Group Name", placeholder="e.g. Europe Trip, Roommates")
            if st.button("Create Group", key="create_group_btn", width="stretch"):
                if not new_group_name.strip():
                    st.error("Group name cannot be empty.")
                else:
                    existing = db.query(Group).filter(Group.name == new_group_name.strip()).first()
                    if existing:
                        st.warning("Group already exists.")
                    else:
                        g = Group(name=new_group_name.strip())
                        db.add(g)
                        db.commit()
                        st.success(f"Group '{new_group_name.strip()}' created successfully!")
                        st.rerun()
                        
        with col_c2:
            st.subheader("Create User (Expense Participant)")
            new_user_name = st.text_input("User Name", placeholder="e.g. Rohan, Priya")
            if st.button("Create User", key="create_user_btn", width="stretch"):
                if not new_user_name.strip():
                    st.error("User name cannot be empty.")
                else:
                    existing = db.query(User).filter(User.name == new_user_name.strip()).first()
                    if existing:
                        st.warning("User already exists.")
                    else:
                        u = User(name=new_user_name.strip())
                        db.add(u)
                        db.commit()
                        st.success(f"User '{new_user_name.strip()}' created successfully!")
                        st.rerun()

    # ==================================================
    # TAB 3: MANAGE MEMBERSHIPS
    # ==================================================
    with tab_memberships:
        col_m1, col_m2 = st.columns(2)
        
        with col_m1:
            st.subheader("Add Member To Group")
            if groups and users:
                sel_group = st.selectbox(
                    "Select Group",
                    groups,
                    format_func=lambda x: x.name,
                    key="add_mem_grp"
                )
                sel_user = st.selectbox(
                    "Select User",
                    users,
                    format_func=lambda x: x.name,
                    key="add_mem_user"
                )
                join_date = st.date_input("Join Date", value=date.today(), key="add_mem_date")
                
                if st.button("Add Member", key="add_mem_btn", width="stretch"):
                    existing_membership = db.query(GroupMember).filter(
                        GroupMember.group_id == sel_group.id,
                        GroupMember.user_id == sel_user.id,
                        GroupMember.status == "ACTIVE"
                    ).first()
                    
                    if existing_membership:
                        st.warning("User already belongs to this group.")
                    else:
                        m = GroupMember(
                            group_id=sel_group.id,
                            user_id=sel_user.id,
                            joined_on=join_date,
                            status="ACTIVE"
                        )
                        db.add(m)
                        db.commit()
                        st.success(f"Added '{sel_user.name}' to '{sel_group.name}' successfully!")
                        st.rerun()
            else:
                st.info("Please create groups and users first.")
                
        with col_m2:
            st.subheader("Member Exit")
            active_m = db.query(GroupMember).filter(GroupMember.status == "ACTIVE").all()
            if not active_m:
                st.info("No active memberships to end.")
            else:
                options = {
                    m.id: f"{m.user.name} in {m.group.name}"
                    for m in active_m if m.user and m.group
                }
                
                sel_m_id = st.selectbox(
                    "Select Membership to Exit",
                    options=list(options.keys()),
                    format_func=lambda x: options[x],
                    key="exit_mem_select"
                )
                
                leave_date = st.date_input("Leave Date", value=date.today(), key="exit_mem_date")
                
                if st.button("Mark Member as Left", key="exit_mem_btn", width="stretch"):
                    m_record = db.query(GroupMember).filter(GroupMember.id == sel_m_id).first()
                    if m_record:
                        m_record.status = "LEFT"
                        m_record.left_on = leave_date
                        db.commit()
                        st.success("Member marked as left.")
                        st.rerun()

finally:
    db.close()