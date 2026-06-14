# 💰 SettleWise – Smart Shared Expense Management System

🔗 **Live Demo:** https://settlewise-expense-app.streamlit.app/

SettleWise is a modern Streamlit-based expense management platform designed to simplify shared expenses among roommates, friends, families, travel groups, and teams.

The platform provides intelligent expense tracking, balance calculation, settlement optimization, CSV-based imports, anomaly detection, approval workflows, reporting, and AI-powered financial insights through an interactive dashboard.

---

## 📌 Problem Statement

Managing shared expenses manually often leads to:

* Confusion about who paid what
* Difficulty calculating balances
* Unequal expense-sharing requirements
* Duplicate or incorrect expense records
* Time-consuming settlement calculations
* Lack of transparency in imported financial data
* Poor visibility into spending trends

SettleWise solves these problems by automating expense tracking, split calculations, settlement generation, anomaly detection, and reporting in a single platform.

---

# ✨ Features

## 👤 User Authentication

* User Registration
* Secure Login System
* Unique Email Validation
* Duplicate User Prevention
* Session Management
* Logout Functionality

---

## 👥 Group Management

* Create Expense Groups
* Add Members
* Remove Members
* View Group Details
* Group Expense Summary

---

## 💰 Expense Management

* Add Expenses Manually
* Edit Existing Expenses
* Delete Expenses
* Expense History Tracking
* Multi-Currency Support

---

## ⚖️ Multiple Expense Splitting Methods

### Equal Split

Split equally among participants.

### Percentage Split

Split by custom percentages.

### Exact Amount Split

Specify exact amounts for each participant.

### Share-Based Split

Allocate expenses based on share units.

---

## 📊 Balance Dashboard

* Member-wise Balance Tracking
* Total Group Spending
* Payable Amounts
* Receivable Amounts
* Balance Visualization

---

## 🤝 Settlement Optimization

Automatically calculates:

* Who should pay whom
* Recommended transactions
* Debt simplification
* Minimum transaction settlements

---

## 📂 CSV Import System

Upload expense data using CSV files.

### Import Workflow

* Upload CSV
* Validate Data
* Detect Anomalies
* Review Import
* Approve Import
* Store Records

---

## 🔍 Advanced Anomaly Detection

Automatically detects:

### Data Quality Issues

* Missing Fields
* Empty Values
* Invalid Currency
* Invalid Dates
* Future Dates

### Financial Issues

* Negative Expenses
* Zero Amount Expenses
* Duplicate Records
* Outlier Transactions

### User Issues

* Name Variations
* Duplicate Users
* Invalid Members

---

## ✅ Approval Workflow

Before importing:

* Review flagged records
* Approve valid records
* Reject problematic records
* Track import history

---

## 🤖 AI-Powered Insights

Generate intelligent observations including:

* Highest spender
* Spending trends
* Expense categories
* Settlement recommendations
* Group activity summaries
* Financial health indicators

---

## 📈 Reporting & Analytics

Generate:

* Expense Reports
* Balance Reports
* Settlement Reports
* Import Reports
* Anomaly Reports
* Audit Reports

---

# 🖥️ Tech Stack

## Frontend

* Streamlit
* HTML
* CSS

## Backend

* Python

## Database

* SQLite

## Data Processing

* Pandas
* NumPy

## ORM

* SQLAlchemy

## Visualization

* Plotly

## Reporting

* CSV Export
* Markdown Reports

---

# 📂 Project Structure

```text
SettleWise
│
├── app.py
├── requirements.txt
├── expenses.db
│
├── database
│   ├── __init__.py
│   ├── database.py
│   ├── models.py
│   ├── crud.py
│   └── init_db.py
│
├── services
│   ├── anomaly_detector.py
│   ├── import_service.py
│   ├── settlement_service.py
│   ├── report_service.py
│   └── ai_insights.py
│
├── pages
│   ├── Dashboard.py
│   ├── Import_Data.py
│   ├── Anomaly_Center.py
│   ├── Expenses.py
│   ├── Groups.py
│   ├── Reports.py
│   ├── Balances.py
│   ├── Settlements.py
│   └── Settings.py
│
├── uploads
├── styles
├── utils
│
└── docs
    ├── README.md
    ├── SCOPE.md
    ├── DECISIONS.md
    ├── AI_USAGE.md
    └── Import_Report.md
```

---

# ⚙️ System Workflow

```text
Expense Added
      │
      ▼
Select Split Method
      │
      ▼
Calculate Shares
      │
      ▼
Update Balances
      │
      ▼
Generate Settlements
      │
      ▼
Generate Reports
```

---

# 📂 CSV Import Workflow

```text
Upload CSV
      │
      ▼
Validate Records
      │
      ▼
Detect Anomalies
      │
      ▼
Review Issues
      │
      ▼
Approve Import
      │
      ▼
Store in Database
      │
      ▼
Update Expenses & Balances
```

---

# 🚀 Installation

## Clone Repository

```bash
git clone https://github.com/somvanshishruti7/SettleWise.git

cd SettleWise
```

## Create Virtual Environment

### Windows

```bash
python -m venv venv

venv\Scripts\activate
```

### Linux / macOS

```bash
python -m venv venv

source venv/bin/activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Initialize Database

```bash
python -m database.init_db
```

## Run Application

```bash
streamlit run app.py
```

Application URL:

```text
http://localhost:8501
```

---

# 📋 Requirements

```text
streamlit
pandas
numpy
sqlalchemy
plotly
python-dateutil
pytz
```

---

# 📊 Reports Generated

* Expense Summary Report
* Balance Report
* Settlement Report
* Import Audit Report
* Anomaly Detection Report

---

# 🔮 Future Enhancements

* OCR Receipt Scanning
* Real-Time Currency Conversion
* AI Expense Categorization
* Email Notifications
* Mobile Responsive Design
* Cloud Database Support
* Multi-Group Collaboration
* Advanced Financial Analytics

---

# 💼 Use Cases

* Roommate Expense Tracking
* Travel Expense Management
* Family Expense Sharing
* Team Expense Tracking
* Event Budget Management
* Student Group Projects

---

# 👩‍💻 Author

**Shruti Somvanshi**

Built as a modern expense-sharing platform that combines automation, anomaly detection, intelligent settlements, and AI-powered insights into a single user-friendly application.

---

# ⭐ Support

If you found this project useful:

⭐ Star the repository

🍴 Fork the project

🚀 Contribute improvements

📢 Share it with others

Your support helps improve SettleWise and encourages future development.
