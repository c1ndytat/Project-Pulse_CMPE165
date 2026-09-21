from datetime import date
from pathlib import Path
import sqlite3

import streamlit as st


DATABASE_PATH = Path(__file__).with_name("project_pulse.db")
STATUSES = ("Not started", "In progress", "Blocked", "Done")
PRIORITIES = ("Low", "Medium", "High")


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --pulse-blue: #2563eb;
            --pulse-purple: #7c3aed;
            --pulse-ink: #172033;
            --pulse-muted: #64748b;
            --pulse-surface: #f8faff;
        }

        body,
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] > section {
            background: #ffffff;
            color: var(--pulse-ink);
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        h1 {
            color: var(--pulse-blue);
            letter-spacing: -0.04em;
        }

        h2, h3 {
            color: var(--pulse-ink);
        }

        [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #dbe4ff;
            border-radius: 14px;
            padding: 14px;
            box-shadow: 0 3px 12px rgba(37, 99, 235, 0.08);
        }

        [data-testid="stMetricValue"] {
            color: var(--pulse-purple);
        }

        [data-testid="stVerticalBlockBorderWrapper"] {
            background: #ffffff;
            border-color: #dbe4ff;
            border-radius: 14px;
            box-shadow: 0 3px 12px rgba(37, 99, 235, 0.06);
        }

        .stProgress > div > div > div > div {
            background-image: linear-gradient(90deg, var(--pulse-blue), var(--pulse-purple));
        }

        .stButton > button[kind="primary"],
        .stFormSubmitButton > button {
            background: linear-gradient(90deg, var(--pulse-blue), var(--pulse-purple));
            border: none;
            color: white;
        }

        .stButton > button[kind="primary"]:hover,
        .stFormSubmitButton > button:hover {
            border: none;
            color: white;
            filter: brightness(1.08);
        }

        @media (prefers-color-scheme: dark) {
            :root {
                --pulse-ink: #e5e7eb;
                --pulse-muted: #a5b4fc;
                --pulse-surface: #151a2b;
            }

            body,
            .stApp,
            [data-testid="stAppViewContainer"],
            [data-testid="stAppViewContainer"] > section {
                background: #17112b;
                color: var(--pulse-ink);
            }

            h1 {
                color: #93c5fd;
            }

            h2, h3, p, label, [data-testid="stMarkdownContainer"] {
                color: var(--pulse-ink);
            }

            [data-testid="stMetric"],
            [data-testid="stVerticalBlockBorderWrapper"] {
                background: #21183d;
                border-color: #373b68;
                box-shadow: 0 3px 14px rgba(0, 0, 0, 0.22);
            }

            [data-testid="stMetricLabel"],
            [data-testid="stCaptionContainer"] {
                color: #cbd5e1;
            }

            [data-testid="stMetricValue"] {
                color: #c4b5fd;
            }

            input, textarea, [data-baseweb="select"] > div {
                background-color: #20263b;
                color: var(--pulse-ink);
                border-color: #4c5280;
            }

            .stProgress > div > div {
                background-color: #303653;
            }
        }

        html[data-theme="light"] body,
        body[data-theme="light"],
        html[data-theme="light"] .stApp,
        body[data-theme="light"] .stApp,
        .stApp[data-theme="light"] {
            background: #ffffff !important;
            color: #172033 !important;
        }

        html[data-theme="dark"] body,
        body[data-theme="dark"],
        html[data-theme="dark"] .stApp,
        body[data-theme="dark"] .stApp,
        .stApp[data-theme="dark"] {
            background: #17112b !important;
            color: #e5e7eb !important;
        }

        html[data-theme="dark"] [data-testid="stAppViewContainer"],
        body[data-theme="dark"] [data-testid="stAppViewContainer"],
        html[data-theme="dark"] [data-testid="stAppViewContainer"] > section,
        body[data-theme="dark"] [data-testid="stAppViewContainer"] > section {
            background: #17112b !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                owner TEXT NOT NULL,
                status TEXT NOT NULL,
                priority TEXT NOT NULL,
                due_date TEXT,
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS blockers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                owner TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Open',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                decision TEXT NOT NULL,
                made_by TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


def fetch_rows(table: str):
    if table not in {"tasks", "blockers", "decisions"}:
        raise ValueError("Unsupported table")
    with get_connection() as connection:
        return connection.execute(f"SELECT * FROM {table} ORDER BY id DESC").fetchall()


def add_task(title: str, owner: str, status: str, priority: str, due_date: date, notes: str) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO tasks (title, owner, status, priority, due_date, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title.strip(), owner.strip(), status, priority, due_date.isoformat(), notes.strip()),
        )


def update_task(task_id: int, status: str, notes: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "UPDATE tasks SET status = ?, notes = ? WHERE id = ?",
            (status, notes.strip(), task_id),
        )


def add_blocker(description: str, owner: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO blockers (description, owner) VALUES (?, ?)",
            (description.strip(), owner.strip()),
        )


def resolve_blocker(blocker_id: int) -> None:
    with get_connection() as connection:
        connection.execute("UPDATE blockers SET status = 'Resolved' WHERE id = ?", (blocker_id,))


def add_decision(question: str, decision: str, made_by: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO decisions (question, decision, made_by) VALUES (?, ?, ?)",
            (question.strip(), decision.strip(), made_by.strip()),
        )


def render_dashboard(tasks, blockers, decisions) -> None:
    completed = sum(task["status"] == "Done" for task in tasks)
    open_blockers = sum(blocker["status"] == "Open" for blocker in blockers)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total tasks", len(tasks))
    col2.metric("Completed", completed)
    col3.metric("Open blockers", open_blockers)
    col4.metric("Decisions logged", len(decisions))

    st.subheader("Task progress")
    if not tasks:
        st.info("No tasks yet. Add the first task from the Tasks tab.")
        return
    status_counts = {status: sum(task["status"] == status for task in tasks) for status in STATUSES}
    completed_ratio = status_counts["Done"] / len(tasks)
    st.write(f"**Overall completion: {completed_ratio:.0%}**")
    st.progress(completed_ratio)

    progress_columns = st.columns(len(STATUSES))
    for column, status in zip(progress_columns, STATUSES):
        count = status_counts[status]
        percentage = count / len(tasks)
        column.metric(status, count, f"{percentage:.0%} of tasks")
        column.progress(percentage)

    st.subheader("Recent tasks")
    for task in tasks[:5]:
        due = task["due_date"] or "No due date"
        status_position = STATUSES.index(task["status"]) / (len(STATUSES) - 1)
        with st.container(border=True):
            title_column, status_column = st.columns([3, 1])
            title_column.markdown(f"**{task['title']}**")
            status_column.markdown(f"**{task['status']}**")
            owner_column, due_column = st.columns(2)
            owner_column.caption(f"Owner\n\n{task['owner']}")
            due_column.caption(f"Due date\n\n{due}")
            st.progress(status_position, text=f"Progress: {task['status']}")


def render_tasks(tasks) -> None:
    st.subheader("Add a task")
    with st.form("new_task", clear_on_submit=True):
        title = st.text_input("Task title")
        owner = st.text_input("Owner")
        col1, col2, col3 = st.columns(3)
        status = col1.selectbox("Status", STATUSES)
        priority = col2.selectbox("Priority", PRIORITIES, index=1)
        due_date = col3.date_input("Due date", value=date.today())
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Create task", type="primary")
        if submitted:
            if not title.strip() or not owner.strip():
                st.error("Task title and owner are required.")
            else:
                add_task(title, owner, status, priority, due_date, notes)
                st.success("Task created.")
                st.rerun()

    st.subheader("Update a task")
    if not tasks:
        st.info("Create a task to enable updates.")
        return
    task_options = {f"#{task['id']} — {task['title']}": task for task in tasks}
    selected_label = st.selectbox("Choose a task", list(task_options))
    selected = task_options[selected_label]
    with st.form("update_task"):
        updated_status = st.selectbox(
            "New status", STATUSES, index=STATUSES.index(selected["status"])
        )
        updated_notes = st.text_area("Notes", value=selected["notes"])
        if st.form_submit_button("Save update"):
            update_task(selected["id"], updated_status, updated_notes)
            st.success("Task updated.")
            st.rerun()


def render_blockers(blockers) -> None:
    st.subheader("Log a blocker")
    with st.form("new_blocker", clear_on_submit=True):
        description = st.text_area("What is blocking the team?")
        owner = st.text_input("Person responsible for follow-up")
        if st.form_submit_button("Log blocker", type="primary"):
            if not description.strip() or not owner.strip():
                st.error("Blocker description and owner are required.")
            else:
                add_blocker(description, owner)
                st.success("Blocker logged.")
                st.rerun()

    st.subheader("Current blockers")
    if not blockers:
        st.success("No blockers have been logged.")
        return
    for blocker in blockers:
        with st.container(border=True):
            st.write(f"**{blocker['description']}**")
            st.caption(f"Owner: {blocker['owner']} · Status: {blocker['status']}")
            if blocker["status"] == "Open" and st.button("Mark resolved", key=f"resolve-{blocker['id']}"):
                resolve_blocker(blocker["id"])
                st.rerun()


def render_decisions(decisions) -> None:
    st.subheader("Record a project decision")
    with st.form("new_decision", clear_on_submit=True):
        question = st.text_input("Question or issue considered")
        decision = st.text_area("Decision made and rationale")
        made_by = st.text_input("Decision owner")
        if st.form_submit_button("Record decision", type="primary"):
            if not question.strip() or not decision.strip() or not made_by.strip():
                st.error("Question, decision, and decision owner are required.")
            else:
                add_decision(question, decision, made_by)
                st.success("Decision recorded.")
                st.rerun()

    st.subheader("Decision log")
    if not decisions:
        st.info("No decisions have been recorded.")
        return
    for item in decisions:
        with st.container(border=True):
            st.write(f"**{item['question']}**")
            st.write(item["decision"])
            st.caption(f"Recorded by {item['made_by']} · {item['created_at']}")


def main() -> None:
    st.set_page_config(page_title="Project Pulse", page_icon="📌", layout="wide")
    apply_theme()
    initialize_database()
    tasks = fetch_rows("tasks")
    blockers = fetch_rows("blockers")
    decisions = fetch_rows("decisions")

    st.title("📌 Project Pulse")
    st.caption("One shared workspace for tasks, blockers, and important project decisions.")
    tabs = st.tabs(["Dashboard", "Tasks", "Blockers", "Decision log"])
    with tabs[0]:
        render_dashboard(tasks, blockers, decisions)
    with tabs[1]:
        render_tasks(tasks)
    with tabs[2]:
        render_blockers(blockers)
    with tabs[3]:
        render_decisions(decisions)


if __name__ == "__main__":
    main()
