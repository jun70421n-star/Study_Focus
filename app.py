import streamlit as st
import sqlite3
from datetime import date, datetime, timedelta
import time

# =========================
# 基本設定
# =========================

st.set_page_config(
    page_title="Study Focus",
    page_icon="📚",
    layout="wide"
)

DB_NAME = "study_focus.db"


# =========================
# データベース
# =========================

def get_connection():
    return sqlite3.connect(DB_NAME)


def create_tables():
    conn = get_connection()
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
    conn.close()


create_tables()


# =========================
# 勉強記録を保存
# =========================

def save_record(subject, minutes, memo=""):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO study_records
    (study_date, subject, minutes, memo)
    VALUES (?, ?, ?, ?)
    """, (
        str(date.today()),
        subject,
        minutes,
        memo
    ))

    conn.commit()
    conn.close()


# =========================
# 勉強記録を削除
# =========================

def delete_record(record_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    DELETE FROM study_records
    WHERE id = ?
    """, (record_id,))

    conn.commit()
    conn.close()


# =========================
# 今日の勉強時間
# =========================

def get_today_minutes():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT COALESCE(SUM(minutes), 0)
    FROM study_records
    WHERE study_date = ?
    """, (str(date.today()),))

    result = cursor.fetchone()[0]

    conn.close()

    return result


# =========================
# 今日の目標
# =========================

def get_today_goal():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT goal_minutes
    FROM daily_goals
    WHERE goal_date = ?
    """, (str(date.today()),))

    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0]

    return 180


def save_goal(minutes):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR REPLACE INTO daily_goals
    (goal_date, goal_minutes)
    VALUES (?, ?)
    """, (
        str(date.today()),
        minutes
    ))

    conn.commit()
    conn.close()


# =========================
# セッション状態
# =========================

if "timer_running" not in st.session_state:
    st.session_state.timer_running = False

if "timer_paused" not in st.session_state:
    st.session_state.timer_paused = False

if "timer_subject" not in st.session_state:
    st.session_state.timer_subject = "英語"

if "timer_total_seconds" not in st.session_state:
    st.session_state.timer_total_seconds = 0

if "timer_remaining_seconds" not in st.session_state:
    st.session_state.timer_remaining_seconds = 0

if "timer_end_time" not in st.session_state:
    st.session_state.timer_end_time = None


# =========================
# タイトル
# =========================

st.title("📚 Study Focus")
st.write("勉強をもっと続けやすくするアプリ")

st.divider()


# =========================
# 今日の勉強状況
# =========================

st.header("📊 今日の勉強状況")

goal_minutes = get_today_goal()
today_minutes = get_today_minutes()

achievement = min(
    int(today_minutes / goal_minutes * 100),
    100
)

remaining = max(goal_minutes - today_minutes, 0)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "🎯 今日の目標",
        f"{goal_minutes} 分"
    )

with col2:
    st.metric(
        "⏱️ 今日の勉強時間",
        f"{today_minutes} 分"
    )

with col3:
    st.metric(
        "📈 目標達成率",
        f"{achievement}%"
    )

st.progress(achievement / 100)

if remaining == 0:
    st.success("🎉 今日の目標達成！すごい！")
else:
    st.info(f"📚 目標まであと {remaining} 分")


# =========================
# 目標設定
# =========================

with st.expander("🎯 今日の目標を変更する"):

    new_goal = st.number_input(
        "目標時間（分）",
        min_value=1,
        max_value=600,
        value=goal_minutes,
        step=10
    )

    if st.button("目標を保存"):
        save_goal(new_goal)
        st.success("🎯 目標を保存しました！")
        st.rerun()


st.divider()


# =========================
# 勉強タイマー
# =========================

st.header("⏱️ 勉強タイマー")

subject = st.selectbox(
    "📚 科目を選択",
    [
        "英語",
        "国語",
        "数学",
        "理科",
        "社会",
        "その他"
    ],
    key="selected_subject"
)

timer_minutes = st.number_input(
    "⏰ 勉強時間（分）",
    min_value=1,
    max_value=600,
    value=25,
    step=5
)

# メモ
timer_memo = st.text_input(
    "📝 勉強メモ（任意）",
    placeholder="例：英語長文ポラリス1を1題"
)


# =========================
# タイマー開始
# =========================

if not st.session_state.timer_running:

    if st.button(
        "▶️ 勉強開始",
        use_container_width=True
    ):

        st.session_state.timer_subject = subject
        st.session_state.timer_memo = timer_memo

        st.session_state.timer_total_seconds = (
            timer_minutes * 60
        )

        st.session_state.timer_remaining_seconds = (
            timer_minutes * 60
        )

        st.session_state.timer_end_time = (
            datetime.now()
            + timedelta(minutes=timer_minutes)
        )

        st.session_state.timer_running = True
        st.session_state.timer_paused = False

        st.rerun()


# =========================
# タイマー動作中
# =========================

if st.session_state.timer_running:

    if not st.session_state.timer_paused:

        remaining_seconds = int(
            (
                st.session_state.timer_end_time
                - datetime.now()
            ).total_seconds()
        )

        st.session_state.timer_remaining_seconds = max(
            remaining_seconds,
            0
        )

    remaining_seconds = (
        st.session_state.timer_remaining_seconds
    )

    minutes_left = remaining_seconds // 60
    seconds_left = remaining_seconds % 60

    st.subheader(
        f"📚 {st.session_state.timer_subject}"
    )

    st.markdown(
        f"""
        <div style="
            text-align:center;
            font-size:70px;
            font-weight:bold;
            padding:20px;
        ">
        {minutes_left:02d}:{seconds_left:02d}
        </div>
        """,
        unsafe_allow_html=True
    )


    # =========================
    # タイマー終了
    # =========================

    if remaining_seconds <= 0:

        save_record(
            st.session_state.timer_subject,
            timer_minutes,
            st.session_state.get(
                "timer_memo",
                "タイマー完了"
            )
        )

        st.session_state.timer_running = False
        st.session_state.timer_paused = False
        st.session_state.timer_end_time = None

        st.success(
            f"🎉 {timer_minutes}分の勉強が完了しました！"
        )

        st.balloons()

        st.rerun()


    # =========================
    # 一時停止・再開
    # =========================

    col1, col2 = st.columns(2)

    with col1:
            if st.button("⏸️ 一時停止"):
            remaining_seconds = int(
                (
                    st.session_state.timer_end_time
                    - datetime.now()
                ).total_seconds()
            )

            st.session_state.timer_remaining_seconds = max(
                remaining_seconds,
                0
            )

            st.session_state.timer_paused = True
            st.rerun()

    with col2:
        if st.button("▶️ 再開"):
            st.session_state.timer_end_time = (
                datetime.now()
                + timedelta(
                    seconds=st.session_state.timer_remaining_seconds
                )
            )

            st.session_state.timer_paused = False
            st.rerun()

       
