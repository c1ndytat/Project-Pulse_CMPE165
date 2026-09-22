# Project Pulse

**Course:** CMPE 165: Software Engineering Process Management

**Semester:** Fall 2026

**Team Members:** Ayana Ahuja, Gonul Koker, Cindy Tat, Rachel Tran

## Project overview

Project Pulse is a shared workspace to help college students manage
group projects. It brings task ownership, blockers, and project decisions into
one place instead of spreading important information across multiple platforms.

The prototype is intentionally small and focuses on reliable, meaningful
interactions:

- Create tasks with an owner, status, priority, due date, and notes.
- Update a task's status and notes as work progresses.
- Log blockers and mark them resolved.
- Record decisions with their rationale and decision owner.
- View a dashboard summarizing progress, open blockers, and decisions.

## How to run

### Prerequisites

- Python 3.10 or newer
- `pip`

### Installation and execution

```bash
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
streamlit run app.py
```

The app creates `project_pulse.db` in the project directory on first launch.
This local SQLite file stores the prototype's tasks, blockers, and decisions.
It is intentionally ignored by Git because it contains local runtime data.

### Reproducing the Monte Carlo simulation (report Part J)

The project report includes a Monte Carlo simulation of the product's
four-year NPV. To reproduce it, run:

```bash
python monte_carlo.py
```

The script runs 10,000 trials with a fixed random seed, so it produces the same
results every time. It prints a summary to the terminal and saves the trial data
(`mc_trials.csv`) and three charts (`mc_histogram.png`, `mc_pilot_gate.png`,
`mc_sensitivity.png`) in the project directory.

## Tech stack

- **Frontend and application:** Python, Streamlit
- **Persistence:** SQLite through Python's standard-library `sqlite3` module
- **Analysis (Monte Carlo simulation):** NumPy, Matplotlib
- **Deployment:** Local development prototype

## System architecture

```text
app.py                 Streamlit UI, validation, and application logic
monte_carlo.py         Monte Carlo simulation of 4-year NPV (report Part J)
requirements.txt       Python dependencies
project_pulse.db       Local SQLite database created at runtime (not committed)
```

The application uses a small data-access layer in `app.py`. User input is
validated before writes, SQL values are parameterized, and the UI reloads data
after each successful change so the dashboard stays current.

## AI-Assisted Development

1. **Tools used:** GitHub Copilot / Copilot SDK in VS Code was used as an
   AI-assisted coding tool.
2. **What AI helped build:** The AI helped scaffold the Streamlit interface,
   design the SQLite tables, add form validation, and connect create/update
   interactions to the dashboard.
3. **Example requiring modification:** The initial prototype direction used
   in-memory lists, which would lose tasks whenever the app restarted. The
   team modified that approach to use SQLite so records persist between runs.
4. **Human team decision:** The team chose to keep the scope focused on tasks,
   blockers, and decisions rather than adding authentication, chat, or a
   full scheduling system. This makes the prototype achievable in two weeks
   and directly supports the assignment's project-management objective.
