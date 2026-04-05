import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import uuid

FILE_PATH = "tasks.xlsx"

# Initialize file
def init_file():
    if not os.path.exists(FILE_PATH):
        df = pd.DataFrame(columns=[
            "Task ID", "Task Name", "Description", "Doc URL", "Remark",
            "Assigned Date", "Due Date", "Status", "Priority",
            "Hours Spent", "Project", "Last Updated"
        ])
        df.to_excel(FILE_PATH, index=False)

# Load & save
def load_data():
    return pd.read_excel(FILE_PATH)

def save_data(df):
    df.to_excel(FILE_PATH, index=False)

# UI setup
st.set_page_config(page_title="Task Tracker Pro", layout="wide")
st.title("🚀 Task Tracker Pro")

# View selector
view = st.sidebar.radio("Select View", ["Task Manager", "Dashboard"])

init_file()
df = load_data()

# Ensure columns exist
for col in ["Remark", "Hours Spent", "Project"]:
    if col not in df.columns:
        df[col] = 0 if col == "Hours Spent" else ""

# Convert dates
df["Due Date"] = pd.to_datetime(df["Due Date"], errors="coerce")
df["Assigned Date"] = pd.to_datetime(df["Assigned Date"], errors="coerce")

import plotly.express as px

# ================= DASHBOARD VIEW =================
if view == "Dashboard":
    st.subheader("📊 Dashboard Overview")

    # ===================== METRICS =====================
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total", len(df))
    col2.metric("Pending", len(df[df['Status'] == 'Pending']))
    col3.metric("In Progress", len(df[df['Status'] == 'In Progress']))
    col4.metric("Completed", len(df[df['Status'] == 'Completed']))
    st.divider()

    # ===================== CHARTS (SIDE BY SIDE) =====================
    col1, col2 = st.columns(2)


    # -------- STATUS BAR CHART --------
    with col1:
        st.markdown("##### Status Distribution")
        status_counts = df["Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]

        fig_bar = px.bar(
            status_counts,
            x="Status",
            y="Count",
            text="Count",
        )

        fig_bar.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=30, b=20)
        )

        st.plotly_chart(fig_bar, use_container_width=True)

    # -------- PRIORITY DONUT CHART --------
    with col2:
        st.markdown("##### Priority Distribution")

        priority_counts = df["Priority"].value_counts().reset_index()
        priority_counts.columns = ["Priority", "Count"]

        fig_donut = px.pie(
            priority_counts,
            names="Priority",
            values="Count",
            hole=0.5  # 👈 This makes it a donut
        )

        fig_donut.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=30, b=20)
        )

        st.plotly_chart(fig_donut, use_container_width=True)

    # ===================== OVERDUE ALERT =====================
    today = pd.to_datetime(date.today())

    overdue = df[
        (df["Due Date"] < today) & (df["Status"] != "Completed")
    ]

    if not overdue.empty:
        st.error(f"⚠️ {len(overdue)} tasks are overdue!")

        st.markdown("### 🚨 Overdue Tasks")

        st.dataframe(
            overdue[[
                "Task Name",
                "Project",
                "Due Date",
                "Priority",
                "Status"
            ]],
            use_container_width=True
        )

# ================= TASK MANAGER VIEW =================
if view == "Task Manager":

    # Add task
    st.sidebar.header("➕ Add Task")

    with st.sidebar.form("task_form"):
        task_name = st.text_input("Task Name")
        description = st.text_area("Description")
        doc_url = st.text_input("Doc URL")
        project = st.text_input("Project")
        due_date = st.date_input("Due Date")
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        submit = st.form_submit_button("Add Task")

    if submit and task_name:
        new_task = {
            "Task ID": str(uuid.uuid4()),
            "Task Name": task_name,
            "Description": description,
            "Doc URL": doc_url,
            "Remark": "",
            "Assigned Date": datetime.now(),
            "Due Date": due_date,
            "Status": "Pending",
            "Priority": priority,
            "Hours Spent": 0,
            "Project": project,
            "Last Updated": datetime.now()
        }

        df = pd.concat([df, pd.DataFrame([new_task])], ignore_index=True)
        save_data(df)
        st.success("Task Added Successfully!")
        st.rerun()

    # Overall Tasks Summary
    st.subheader("Overall Tasks Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Tasks", len(df))
    col2.metric("Pending", len(df[df['Status'] == 'Pending']))
    col3.metric("In Progress", len(df[df['Status'] == 'In Progress']))
    col4.metric("Completed", len(df[df['Status'] == 'Completed']))

    # Filters
    st.subheader("🔍 Filters")

    col1, col2, col3 = st.columns(3)

    status_filter = col1.selectbox("Status", ["All", "Pending", "In Progress", "Completed"])
    priority_filter = col2.selectbox("Priority", ["All", "Low", "Medium", "High"])
    search = col3.text_input("Search Task")

    filtered_df = df.copy()

    if status_filter != "All":
        filtered_df = filtered_df[filtered_df["Status"] == status_filter]

    if priority_filter != "All":
        filtered_df = filtered_df[filtered_df["Priority"] == priority_filter]

    if search:
        filtered_df = filtered_df[
            filtered_df["Task Name"].str.contains(search, case=False, na=False)
        ]

    # # Overall Tasks Summary
    # st.subheader("Overall Tasks Summary")
    # col1, col2, col3, col4 = st.columns(4)
    # col1.metric("Total Tasks", len(df))
    # col2.metric("Pending", len(df[df['Status'] == 'Pending']))
    # col3.metric("In Progress", len(df[df['Status'] == 'In Progress']))
    # col4.metric("Completed", len(df[df['Status'] == 'Completed']))

    # Task list
    st.subheader("📋 Tasks")

    if filtered_df.empty:
        st.info("No tasks found")
    else:
        for _, row in filtered_df.iterrows():
            task_id = row["Task ID"]

            with st.expander(f"{row['Task Name']} ({row['Status']})"):

                st.write(f"**Project:** {row['Project']}")
                st.write(f"**Description:** {row['Description']}")
                st.markdown(f"[📄 Open Document]({row['Doc URL']})")
                st.write(f"**Priority:** {row['Priority']}")
                st.write(f"**Due Date:** {row['Due Date']}")
                st.write(f"**Hours Spent:** {row['Hours Spent']}")

                # Status color
                if row["Status"] == "Completed":
                    st.success("Completed")
                elif row["Status"] == "In Progress":
                    st.warning("In Progress")
                else:
                    st.error("Pending")

                new_status = st.selectbox(
                    "Update Status",
                    ["Pending", "In Progress", "Completed"],
                    index=["Pending", "In Progress", "Completed"].index(row["Status"]),
                    key=f"status_{task_id}"
                )

                remark_input = st.text_area(
                    "Add Work Log",
                    key=f"remark_{task_id}"
                )

                hours = st.number_input(
                    "Hours Worked",
                    min_value=0.0,
                    step=0.5,
                    key=f"hours_{task_id}"
                )

                colu1, colu2 = st.columns(2)

                if colu1.button("Update", key=f"update_{task_id}"):
                    log = f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {remark_input}"

                    df.loc[df["Task ID"] == task_id, "Remark"] = (
                        str(row.get("Remark", "")) + "\n" + log
                    )

                    df.loc[df["Task ID"] == task_id, "Status"] = new_status
                    df.loc[df["Task ID"] == task_id, "Hours Spent"] += hours
                    df.loc[df["Task ID"] == task_id, "Last Updated"] = datetime.now()

                    save_data(df)
                    st.success("Updated Successfully!")
                    st.rerun()

                if colu2.button("Delete", key=f"delete_{task_id}"):
                    df = df[df["Task ID"] != task_id]
                    save_data(df)
                    st.warning("Task Deleted")
                    st.rerun()

                st.text_area(
                    "📜 Work History",
                    value=row.get("Remark", ""),
                    height=150,
                    key=f"history_{task_id}"
                )

    # Download
    st.download_button(
        "📥 Download CSV",
        df.to_csv(index=False),
        "tasks.csv"
    )
