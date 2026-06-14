

# AI Usage Disclosure – SettleWise

## Overview

SettleWise was developed using an AI-assisted software development workflow. Artificial Intelligence tools were used to accelerate development, debugging, documentation, interface improvements, data validation logic, and deployment support.

AI tools acted as development assistants throughout the project lifecycle. All final implementation decisions, business logic, testing, validation, and deployment activities were performed and verified by the project author.

---

# AI Tools Used

## ChatGPT

ChatGPT was the primary AI assistant used throughout the project.

### Areas of Assistance

* Streamlit application development
* SQLite database integration
* Expense management workflows
* CSV import functionality
* Anomaly detection logic
* Settlement calculations
* Dashboard design improvements
* Documentation generation
* GitHub repository preparation
* Deployment troubleshooting

### Example Tasks

* Creating anomaly detection modules
* Designing database schemas
* Writing CRUD operations
* Building import validation workflows
* Debugging Streamlit application errors
* Generating project documentation

---

## Google Gemini

Gemini was used as a secondary research and troubleshooting assistant.

### Areas of Assistance

* Streamlit deployment troubleshooting
* UI improvement suggestions
* Alternative implementation approaches
* Error diagnosis
* Performance optimization ideas

### Example Tasks

* Deployment debugging
* Streamlit Cloud issue investigation
* Dashboard enhancement suggestions
* Database connection troubleshooting

---

# How AI Was Used

AI tools were used for:

✅ Code explanations

✅ Architecture suggestions

✅ Bug fixing assistance

✅ SQL query guidance

✅ Data validation strategies

✅ UI/UX recommendations

✅ Documentation drafting

✅ Deployment support

✅ Workflow optimization

AI-generated outputs were reviewed and modified before being integrated into the final project.

---

# Human Contributions

The following activities were completed directly by the project author:

* Project idea formulation
* Problem statement analysis
* Requirement gathering
* Feature planning
* Database design decisions
* Application customization
* CSV dataset preparation
* Testing and debugging
* Streamlit deployment
* UI refinement
* GitHub repository management
* Final validation and verification

All production code and final project behavior were manually reviewed before acceptance.

---

# Examples of AI Mistakes and Corrections

## Case 1 – Incorrect Database Import Path

### AI Suggestion

The AI initially suggested importing database modules using:

```python
from database import database
```

### Problem

The actual project structure required:

```python
from database.database import SessionLocal
```

### Resolution

The import paths were corrected based on the project directory structure.

### Outcome

Database connectivity was restored successfully.

---

## Case 2 – Streamlit Deployment Failure

### AI Suggestion

The application was deployed assuming all required packages would be installed automatically.

### Problem

The deployed application failed with:

```text
ModuleNotFoundError: No module named 'plotly'
```

### Resolution

The missing dependency was manually added to:

```text
requirements.txt
```

```text
streamlit
pandas
sqlalchemy
plotly
numpy
python-dateutil
pytz
```

### Outcome

The deployment dependencies were resolved.

---

## Case 3 – CSV Import Validation Logic

### AI Suggestion

Initial anomaly detection only checked:

* Missing values
* Negative amounts

### Problem

The uploaded dataset contained additional inconsistencies:

* Name variations
* Duplicate transactions
* Missing currency values
* Missing split types

### Resolution

The anomaly detector was expanded to identify:

* Missing fields
* Duplicate expenses
* Name standardization issues
* Negative amounts
* Zero-value expenses

### Outcome

The import validation became significantly more robust.

---

# Validation Process

Every AI-generated output underwent manual verification.

The validation process included:

1. Reviewing generated code.
2. Running functionality tests.
3. Checking database operations.
4. Verifying anomaly detection results.
5. Testing Streamlit pages.
6. Validating deployment behavior.
7. Comparing outputs against project requirements.

No AI-generated code was merged into the final project without testing.

---

# Responsible AI Usage

SettleWise follows responsible AI-assisted development practices:

* Human oversight for all generated content.
* Manual validation before deployment.
* Transparent disclosure of AI involvement.
* Independent decision-making by the project author.
* Continuous testing and verification.

AI tools accelerated development but did not replace software engineering judgment.

---

# Benefits Gained from AI Assistance

The use of AI helped:

* Reduce development time
* Improve documentation quality
* Accelerate debugging
* Explore multiple implementation approaches
* Improve code readability
* Enhance user interface design
* Streamline deployment troubleshooting

while maintaining full human supervision throughout the project lifecycle.

---

# Transparency Statement

SettleWise was developed using a combination of:

* Human-driven software engineering
* AI-assisted development tools
* Manual testing and debugging
* Independent design and implementation decisions

Although AI tools contributed suggestions and draft implementations, all final architecture, code integration, testing, deployment, and project outcomes remain the responsibility of the project author.

---

# Author

**Shruti Somvanshi**

SettleWise – Smart Expense Management & Anomaly Detection Platform

Built using Python, Streamlit, SQLite, Pandas, and AI-assisted development practices to deliver a reliable and transparent shared expense management solution.
