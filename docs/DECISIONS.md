

# Decision Log – SettleWise

This document records the major technical, architectural, and workflow decisions made during the development of SettleWise.

The purpose of this document is to explain what decisions were made, which alternatives were considered, and why the final approach was chosen.

---

# Project Vision

The initial goal of SettleWise was to build a shared expense management platform that could help users:

* Track group expenses
* Calculate balances
* Generate settlements
* Import expense data from CSV files

As development progressed, the project expanded into a complete expense analysis and anomaly detection system capable of validating imported financial records before they enter the database.

---

# Decision 1: Choosing Streamlit as the Application Framework

## Options Considered

### Option A

React + FastAPI

### Option B

Django

### Option C ✅ Chosen

Streamlit

## Reasoning

The primary focus of SettleWise was:

* Expense management logic
* Data processing
* CSV analysis
* Settlement calculations

rather than building a highly customized frontend.

Streamlit allowed rapid development using Python while providing interactive dashboards and data visualizations.

## Trade-Off

Reduced frontend flexibility compared to React, but significantly faster development and deployment.

---

# Decision 2: Using SQLite Instead of PostgreSQL

## Options Considered

### PostgreSQL

Advantages:

* Scalable
* Production-ready
* Multi-user support

### SQLite ✅ Chosen

Advantages:

* Lightweight
* No server setup required
* Easy deployment
* Suitable for project scale

## Reasoning

SettleWise is primarily a portfolio and learning project focused on workflow design and data validation.

SQLite provided all required functionality while keeping deployment simple.

---

# Decision 3: Supporting CSV Import

## Original Approach

Users manually entered expenses through forms.

## Problem

Manual entry becomes impractical when:

* Importing historical expenses
* Processing large datasets
* Migrating data from other systems

## Final Decision ✅

Implement CSV import functionality.

## Benefits

* Faster onboarding
* Bulk expense processing
* Better usability

---

# Decision 4: Creating an Anomaly Detection Engine

## Initial Approach

Imported records were accepted without validation.

## Problem

Real-world datasets contain:

* Missing values
* Duplicate entries
* Incorrect names
* Invalid amounts
* Missing currencies

During testing, the sample CSV contained several of these issues.

## Final Decision ✅

Build a dedicated anomaly detection module.

## Implemented Checks

* Missing required fields
* Negative amounts
* Zero-value expenses
* Duplicate transactions
* Name variations
* Currency validation

## Result

Improved data quality and prevented invalid records from entering the database.

---

# Decision 5: Standardizing User Names

## Problem

The imported CSV contained multiple representations of the same person.

Examples:

* Priya
* priya
* Priya S

and

* Rohan
* rohan

These variations could create incorrect balance calculations.

## Final Decision ✅

Detect and flag name inconsistencies during import.

## Result

Improved accuracy of group balances and settlements.

---

# Decision 6: Adding Settlement Optimization

## Original Design

Display balances only.

## Problem

Users still needed to manually determine who should pay whom.

## Final Decision ✅

Generate settlement recommendations automatically.

## Example

Instead of multiple unnecessary transfers:

* A pays B
* B pays C
* C pays D

SettleWise calculates the minimum number of transactions required.

## Result

Simplified debt settlement process.

---

# Decision 7: Import Review Before Database Insertion

## Original Workflow

CSV Upload
↓
Store Data

## Problem

Invalid records could be permanently inserted.

## Final Workflow ✅

CSV Upload
↓
Validate Data
↓
Detect Anomalies
↓
Review Results
↓
Approve Import
↓
Store in Database

## Result

Improved reliability and transparency.

---

# Decision 8: Maintaining Anomaly History

## Problem

Once anomalies were fixed, there was no audit trail.

## Final Decision ✅

Store anomaly information in a dedicated database table.

## Benefits

* Auditability
* Traceability
* Better reporting

---

# Decision 9: Building a Multi-Page Application

## Original Idea

Single-page application.

## Problem

As features increased, the interface became cluttered.

## Final Decision ✅

Separate functionality into dedicated pages:

* Dashboard
* Import Data
* Anomaly Center
* Expenses
* Groups
* Reports
* Balances
* Settlements
* Settings

## Result

Improved navigation and user experience.

---

# Decision 10: Using KPI Cards for Insights

## Problem

Tables alone made important information difficult to identify quickly.

## Final Decision ✅

Introduce dashboard KPI cards displaying:

* Total Records
* Total Expenses
* Total Anomalies
* High Severity Issues
* Settlement Statistics

## Result

Users can immediately understand system status.

---

# Decision 11: Streamlit Cloud Deployment

## Options Considered

### Local Desktop Only

### Cloud Deployment ✅

## Reasoning

A deployed application allows:

* Easy access
* Portfolio demonstration
* Public sharing

## Challenges Encountered

During deployment:

* Missing Plotly dependency
* Import path errors
* Database module resolution issues

These were resolved through dependency management and project restructuring.

---

# Decision 12: Documentation Strategy

## Initial State

Minimal documentation.

## Problem

As project complexity increased, project understanding became difficult.

## Final Decision ✅

Create dedicated documentation files:

* README.md
* SCOPE.md
* DECISIONS.md
* AI_USAGE.md
* IMPORT_REPORT.md

## Result

Improved transparency, maintainability, and project evaluation readiness.

---

# Key Lessons Learned

Throughout development several important lessons emerged:

* Data validation is as important as expense tracking.
* Real-world CSV files are rarely clean.
* User workflows matter more than individual features.
* Settlement recommendations add significant user value.
* Documentation becomes critical as project complexity grows.
* Deployment introduces challenges not visible during local development.

---

# Final Outcome

SettleWise evolved from a simple expense tracker into a complete expense management and anomaly detection platform.

The final system combines:

* Expense Tracking
* Group Management
* Balance Calculation
* Settlement Optimization
* CSV Import Processing
* Anomaly Detection
* Reporting
* Auditability

while remaining lightweight, maintainable, and deployable using Streamlit and SQLite.

---

# Author

**Shruti Somvanshi**

SettleWise – Smart Shared Expense Management & Anomaly Detection Platform
