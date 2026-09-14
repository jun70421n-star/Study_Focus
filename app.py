
import streamlit as st
import sqlite3
from datetime import date, timedelta

st.set_page_config(
    page_title="Study Focus",
    page_icon="📚",
    layout="wide"
)

conn = sqlite3.connect("study_focus.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS study_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    study_date TEXT NOT NULL,
    subject TEXT NOT NULL,
    minutes INTEGER NOT NULL,
    memo TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS daily_goals (
    goal_date TEXT PRIMARY KEY,
    goal_minutes INTEGER NOT NULL
)
""")

conn.commit()

today = date.today()
today_text = str(today)

cursor.execute("""
SELECT goal_minutes
FROM daily_goals
WHERE goal_date = ?
""", (today_text,))

goal_result = cursor.fetchone()

if goal_result:
    current_goal = goal_result[0]
else:
    current_goal = 180

cursor.execute("""
SELECT SUM(minutes)
FROM study_records
WHERE study_date = ?
""", (today_text,))

study_result = cursor.fetchone()

if study_result[0] is not None:
    today_minutes = study_result[0]
else:
    today_minutes = 0

achievement_rate = today_minutes / current_goal * 100

if achievement_rate > 100:
    achievement_rate = 100

remaining_minutes = current_goal - today_minutes

if remaining_minutes < 0:
    remaining_minutes = 0

st.title("📚 Study Focus")
st.write("勉強をもっと続けやすくするアプリ")

st.divider()

st.subheader("📊 今日の勉強状況")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🎯 今日の目標", f"{current_goal} 分")

with col2:
    st.metric("⏱️ 今日の勉強時間", f"{today_minutes} 分")

with col3:
    st.metric("📈 目標達成率", f"{achievement_rate:.0f}%")

with col4:
    st.metric("🔥 あと", f"{remaining_minutes} 分")

st.progress(achievement_rate / 100)

if remaining_minutes == 0:
    st.success("🎉 今日の目標を達成しました！")
else:
    st.info(f"あと {remaining_minutes} 分勉強すると、今日の目標達成です！")

st.divider()

st.subheader("📊 週間勉強時間")

weekly_data = {}

for i in range(6, -1, -1):

    target_date = today - timedelta(days=i)
    target_text = str(target_date)

    cursor.execute("""
    SELECT SUM(minutes)
    FROM study_records
    WHERE study_date = ?
    """, (target_text,))

    result = cursor.fetchone()

    if result[0] is not None:
        minutes = result[0]
    else:
        minutes = 0

    label = target_date.strftime("%m/%d")
    weekly_data[label] = minutes

st.bar_chart(weekly_data)

st.divider()

st.subheader("📚 科目別勉強時間")

cursor.execute("""
SELECT subject, SUM(minutes)
FROM study_records
GROUP BY subject
ORDER BY SUM(minutes) DESC
""")

subject_records = cursor.fetchall()

subject_data = {}

for record in subject_records:
    subject_data[record[0]] = record[1]

if subject_data:

    st.bar_chart(subject_data)

    st.write("### 科目別の合計")

    for subject, minutes in subject_data.items():
        st.write(f"📚 {subject}：**{minutes}分**")

else:
    st.info("まだ勉強記録がありません。")

st.divider()

st.subheader("🎯 今日の目標を設定")

goal_minutes = st.number_input(
    "目標時間（分）",
    min_value=1,
    max_value=1000,
    value=current_goal,
    step=10
)

if st.button("目標を保存"):

    cursor.execute("""
    INSERT OR REPLACE INTO daily_goals
    (goal_date, goal_minutes)
    VALUES (?, ?)
    """, (today_text, goal_minutes))

    conn.commit()

    st.success(f"今日の目標を {goal_minutes} 分に設定しました！")

conn.close()
