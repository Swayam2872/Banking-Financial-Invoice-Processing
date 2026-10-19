# Banking & Financial Invoice Processing using Agentic AI

A college project: four simple agents (plain Python functions) process a synthetic invoice and decide
whether it is **Verified**, **Flagged** or **Incomplete**. A human always makes the final approval.

> **Honest note:** the agents use fixed if-else rules. There is no LLM, no OCR, no database and no real payment.

## Repository structure
```
├── agents.py          # sample data, 4 agents, process_invoice() orchestrator
├── app.py             # Streamlit dashboard (display only)
├── test_agents.py     # 9 tests (6 required cases + 3 safety tests)
├── requirements.txt   # streamlit
└── docs/
    ├── Presentation.pptx
    ├── Project_Report.docx
    └── architecture.mmd   # Mermaid diagram
```

## Run (Windows Command Prompt)
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
python test_agents.py
```

## Agents
| Agent | Job |
|---|---|
| Planner | Creates the task list |
| Document | Reads structured invoice fields (no OCR) |
| Validation | Runs 5 checks: fields, total, duplicate, payment record, payment amount |
| Critic | Final decision: VERIFIED / FLAGGED / INCOMPLETE |

## Push to GitHub
```
git init
git add .
git commit -m "Invoice processing with agentic AI"
git branch -M main
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```
