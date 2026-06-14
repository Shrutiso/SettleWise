

# SettleWise – Project Scope, Data Quality Analysis & Database Design

---

# 📌 Project Overview

SettleWise is an AI-assisted shared expense management platform built using Streamlit, Python, SQLite, Pandas, and SQLAlchemy.

The system helps roommates, friends, travel groups, families, and teams manage shared expenses through intelligent expense tracking, settlement optimization, CSV imports, anomaly detection, reporting, and AI-generated financial insights.

The primary objective of SettleWise is to simplify expense sharing while ensuring data accuracy, transparency, and financial accountability.

---

# 🎯 Project Objectives

The system was developed to:

- Simplify shared expense tracking
- Eliminate manual balance calculations
- Reduce settlement complexity
- Support bulk expense imports through CSV files
- Detect and prevent invalid financial data
- Improve transparency among group members
- Maintain a complete audit trail of imports
- Generate meaningful financial insights

---

# ✅ Features Included In Scope

## 👤 User Management

The platform supports:

- User Registration
- User Login
- Session Management
- Duplicate User Prevention
- Secure Authentication

Each user is uniquely identified using their email address and cannot register multiple accounts using the same email.

---

## 👥 Group Management

Users can:

- Create Expense Groups
- Add Members
- Remove Members
- Delete Groups
- View Group Expenses
- Manage Multiple Groups

Examples:

- Roommates
- Family Expenses
- Goa Trip Expenses
- Office Team Expenses

---

## 💰 Expense Management

Users can:

- Add Expenses
- Edit Expenses
- Delete Expenses
- View Expense History
- Track Expense Participants

Expense details include:

- Description
- Amount
- Date
- Currency
- Paid By
- Split Method

---

## ⚖️ Expense Splitting Methods

SettleWise supports multiple real-world splitting strategies.

### Equal Split

Every participant pays the same amount.

Example:

Expense = ₹4,000

Members = 4

Each member owes ₹1,000

---

### Percentage Split

Expenses are divided using percentages.

Example:

Aisha = 40%

Rohan = 30%

Priya = 20%

Dev = 10%

---

### Share-Based Split

Expenses are distributed using weighted shares.

Example:

Aisha = 2 shares

Rohan = 1 share

Priya = 1 share

---

### Unequal Split

Users manually specify exact amounts.

Example:

Aisha = ₹700

Rohan = ₹500

Priya = ₹300

---

## 📊 Balance Engine

The balance engine calculates:

- Total Paid
- Total Owed
- Net Balance
- Amount Receivable
- Amount Payable

for every member in a group.

---

## 🤝 Settlement Optimization

The settlement engine minimizes the number of transactions required to clear debts.

Instead of:

A → B

B → C

C → D

The system calculates:

A → D

This reduces transaction complexity and improves usability.

---

## 📂 CSV Import System

SettleWise allows bulk expense imports through CSV files.

Features include:

- File Upload
- Data Preview
- Validation Checks
- Import Summary
- Approval Workflow
- Database Import

---

## 🚨 Anomaly Detection System

Before data enters the database, SettleWise validates every record and detects anomalies.

Detected anomaly categories include:

### Missing Required Fields

Required fields:

- date
- description
- paid_by
- amount
- currency
- split_type

Example:

date = 01-01-2026

description = Rent

paid_by = NULL

Severity:

HIGH

---

### Negative Amounts

Example:

Amount = -30

Severity:

HIGH

Reason:

May represent invalid expenses or refunds that require review.

---

### Zero Amount Expenses

Example:

Amount = 0

Severity:

MEDIUM

Reason:

Expense exists but has no financial impact.

---

### Name Variations

Example:

priya

Priya

rohan

Rohan

Severity:

MEDIUM

Reason:

Can create duplicate identities during calculations.

---

### Possible Duplicate Expenses

Example:

Dinner at Marina Bites

dinner - marina bites

Severity:

MEDIUM

Reason:

May lead to double counting.

---

### Missing Currency

Example:

Currency field is empty.

Severity:

HIGH

Reason:

Financial calculations require valid currency information.

---

# 📊 Dataset Analysis Results

The sample CSV dataset used during development contained several real-world anomalies.

Detected Issues:

| Row | Issue |
|------|--------|
| 11 | Missing paid_by |
| 12 | Missing split_type |
| 26 | Missing currency |
| 24 | Negative amount |
| 29 | Zero amount |
| 7 | Name variation (priya) |
| 25 | Name variation (rohan) |
| 4 | Possible duplicate expense |

---

## Severity Summary

HIGH Severity Issues = 4

MEDIUM Severity Issues = 4

Total Anomalies Detected = 8

---

# 📋 Import Validation Workflow

```text
Upload CSV
     │
     ▼
Preview Data
     │
     ▼
Schema Validation
     │
     ▼
Data Validation
     │
     ▼
Anomaly Detection
     │
     ▼
Severity Classification
     │
     ▼
Review Screen
     │
     ▼
Approve Import
     │
     ▼
Store In Database
     │
     ▼
Update Balances
     │
     ▼
Generate Reports
```

---

# 📈 Reporting Module

SettleWise generates the following reports:

### Expense Report

Contains:

- Total Expenses
- Expense Breakdown
- Category Analysis

---

### Balance Report

Contains:

- Member Balances
- Amount Owed
- Amount Receivable

---

### Settlement Report

Contains:

- Recommended Payments
- Settlement Status
- Completed Settlements

---

### Import Report

Contains:

- Imported File Name
- Import Time
- Total Records
- Anomalies Found
- Actions Taken

---

# 🤖 AI Insights Module

The AI Insights section analyzes:

- Spending Trends
- Highest Expenses
- Group Expense Patterns
- Settlement Suggestions
- Data Quality Issues

The purpose is to help users better understand their financial behavior and identify potential problems within imported datasets.

---

# ❌ Features Currently Out Of Scope

The following features are intentionally excluded from the current version:

- UPI Integration
- Bank Account Integration
- Credit Card Processing
- Cryptocurrency Support
- Real-Time Currency Conversion
- Mobile Application
- Machine Learning Predictions
- Cloud Multi-Tenant Architecture

---

# 🗄️ Database Design

The application uses SQLite as its primary storage engine.

---

## Users Table

Stores registered users.

| Column | Type |
|----------|----------|
| id | INTEGER |
| username | TEXT |
| email | TEXT |
| password_hash | TEXT |

---

## Groups Table

Stores expense groups.

| Column | Type |
|----------|----------|
| id | INTEGER |
| name | TEXT |

---

## Group Members Table

Stores group membership history.

| Column | Type |
|----------|----------|
| id | INTEGER |
| group_id | INTEGER |
| user_id | INTEGER |
| joined_on | DATE |
| left_on | DATE |

---

## Expenses Table

Stores expense records.

| Column | Type |
|----------|----------|
| id | INTEGER |
| title | TEXT |
| amount | REAL |
| currency | TEXT |
| expense_date | DATE |
| paid_by | INTEGER |
| split_type | TEXT |

---

## Expense Participants Table

Stores participant shares.

| Column | Type |
|----------|----------|
| id | INTEGER |
| expense_id | INTEGER |
| user_id | INTEGER |
| share_amount | REAL |

---

## Settlements Table

Stores settlement transactions.

| Column | Type |
|----------|----------|
| id | INTEGER |
| payer_id | INTEGER |
| receiver_id | INTEGER |
| amount | REAL |
| settlement_date | DATE |

---

## Import Logs Table

Stores CSV import history.

| Column | Type |
|----------|----------|
| id | INTEGER |
| file_name | TEXT |
| total_rows | INTEGER |
| imported_rows | INTEGER |
| anomalies_found | INTEGER |

---

## Anomalies Table

Stores anomaly records.

| Column | Type |
|----------|----------|
| id | INTEGER |
| row_number | INTEGER |
| anomaly_type | TEXT |
| severity | TEXT |
| description | TEXT |
| action_taken | TEXT |

---

# 🔄 System Architecture

```text
Users
   │
   ▼
Groups
   │
   ▼
Expenses
   │
   ▼
Expense Participants
   │
   ▼
Balance Engine
   │
   ▼
Settlement Engine
   │
   ▼
Reports


CSV Import
   │
   ▼
Validation
   │
   ▼
Anomaly Detection
   │
   ▼
Approval Workflow
   │
   ▼
Database
```

---

# 📈 Expected Outcomes

By combining expense tracking, settlement optimization, anomaly detection, reporting, and AI insights, SettleWise aims to:

- Improve financial transparency
- Reduce manual calculations
- Prevent invalid data imports
- Maintain accurate balances
- Simplify debt settlements
- Increase user trust through validation and auditability

The platform provides a complete workflow for managing shared expenses while ensuring data quality and financial correctness.
