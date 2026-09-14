import streamlit as st
import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pandas as pd


# =========================================================
# 基本設定
# =========================================================

st.set_page_config(
    page_title="Study Focus",
    page_icon="📚",
    layout="wide"
)

JST = ZoneInfo("Asia/Tokyo")
DB_NAME = "study_focus.db"


# =========================================================
# データベース
# =========================================================

def get_connection():
    return sqlite3.connect(DB_NAME)


def init_database():
    conn = get_connection()
    cursor = conn.cursor()

    # 勉強記録
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS study_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        study_date TEXT NOT NULL,
        subject TEXT NOT NULL,
        minutes INTEGER NOT NULL,
        memo TEXT
    )
    """)

    # 毎日の目標
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_goals (
        goal_date TEXT PRIMARY KEY,
        goal_minutes INTEGER NOT NULL
    )
    """)

    # 科目別目標
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subject_goals (
        subject TEXT PRIMARY KEY,
        goal_minutes INTEGER NOT NULL
    )
    """)

    # 毎日のコメント
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_comments (
        comment_date TEXT PRIMARY KEY,
        comment TEXT
    )
    """)

    conn.commit()
    conn.close()


init_database()


# =========================================================
# 日付
# =========================================================

def today():
    return datetime.now(JST).date()


def today_string():
    return today().isoformat()


# =========================================================
# 勉強記録関連
# =========================================================

def save_record(study_date, subject, minutes, memo=""):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO study_records
    (study_date, subject, minutes, memo)
    VALUES (?, ?, ?, ?)
    """, (
        study_date,
        subject,
        minutes,
        memo
    ))

    conn.commit()
    conn.close()


def get_today_minutes():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT COALESCE(SUM(minutes), 0)
    FROM study_records
    WHERE study_date = ?
    """, (today_string(),))

    result = cursor.fetchone()[0]

    conn.close()

    return result


def get_subject_minutes():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT subject, SUM(minutes)
    FROM study_records
    GROUP BY subject
    ORDER BY SUM(minutes) DESC
    """)

    records = cursor.fetchall()

    conn.close()

    return records


def get_weekly_minutes():
    data = []

    for i in range(6, -1, -1):
        day = today() - timedelta(days=i)
        day_string = day.isoformat()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT COALESCE(SUM(minutes), 0)
        FROM study_records
        WHERE study_date = ?
        """, (day_string,))

        minutes = cursor.fetchone()[0]

        conn.close()

        data.append({
            "日付": day.strftime("%m/%d"),
            "勉強時間": minutes
        })

    return data


def get_recent_records(limit=20):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, study_date, subject, minutes, memo
    FROM study_records
    ORDER BY study_date DESC, id DESC
    LIMIT ?
    """, (limit,))

    records = cursor.fetchall()

    conn.close()

    return records


def delete_record(record_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    DELETE FROM study_records
    WHERE id = ?
    """, (record_id,))

    conn.commit()
    conn.close()


# =========================================================
# 毎日の目標
# =========================================================

def get_today_goal():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT goal_minutes
    FROM daily_goals
    WHERE goal_date = ?
    """, (today_string(),))

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
        today_string(),
        minutes
    ))

    conn.commit()
    conn.close()


# =========================================================
# 科目別目標
# =========================================================

SUBJECTS = [
    "英語",
    "国語",
    "数学",
    "地理",
    "総合問題",
    "面接",
    "その他"
]


def get_subject_goal(subject):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT goal_minutes
    FROM subject_goals
    WHERE subject = ?
    """, (subject,))

    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0]

    return 0


def save_subject_goal(subject, minutes):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR REPLACE INTO subject_goals
    (subject, goal_minutes)
    VALUES (?, ?)
    """, (
        subject,
        minutes
    ))

    conn.commit()
    conn.close()


# =========================================================
# コメント
# =========================================================

def get_today_comment():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT comment
    FROM daily_comments
    WHERE comment_date = ?
    """, (today_string(),))

    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0]

    return ""


def save_today_comment(comment):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR REPLACE INTO daily_comments
    (comment_date, comment)
    VALUES (?, ?)
    """, (
        today_string(),
        comment
    ))

    conn.commit()
    conn.close()


# =========================================================
# 連続勉強日数
# =========================================================

def get_streak():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT DISTINCT study_date
    FROM study_records
    WHERE minutes > 0
    ORDER BY study_date DESC
    """)

    dates = [datetime.strptime(row[0], "%Y-%m-%d").date()
             for row in cursor.fetchall()]

    conn.close()

    if not dates:
        return 0

    current = today()
    streak = 0

    for study_day in dates:
        if study_day == current - timedelta(days=streak):
            streak += 1
        elif study_day < current - timedelta(days=streak):
            break

    return streak


# =========================================================
# バッジ
# =========================================================

def get_badges():
    total_minutes = get_total_minutes()
    streak = get_streak()

    badges = []

    if total_minutes >= 60:
        badges.append(("🌱", "はじめの一歩", "累計1時間達成"))

    if total_minutes >= 300:
        badges.append(("🔥", "努力家", "累計5時間達成"))

    if total_minutes >= 1000:
        badges.append(("🏆", "1000分突破", "累計1000分達成"))

    if streak >= 3:
        badges.append(("🔥", "3日継続", "3日連続で勉強"))

    if streak >= 7:
        badges.append(("💎", "1週間継続", "7日連続で勉強"))

    if get_today_minutes() >= get_today_goal():
        badges.append(("🎯", "目標達成", "今日の目標を達成"))

    return badges


def get_total_minutes():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT COALESCE(SUM(minutes), 0)
    FROM study_records
    """)

    result = cursor.fetchone()[0]

    conn.close()

    return result


# =========================================================
# タイマー用Session State
# =========================================================

defaults = {
    "timer_running": False,
    "timer_paused": False,
    "timer_subject": "英語",
    "timer_total_seconds": 0,
    "timer_remaining_seconds": 0,
    "timer_end_time": None,
    "timer_saved": False
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# ヘッダー
# =========================================================

st.title("📚 Study Focus")
st.caption("勉強をもっと続けやすくするアプリ")

st.divider()


# =========================================================
# サイドバー
# =========================================================

with st.sidebar:

    st.header("⚙️ 設定")

    st.subheader("🏠 ダッシュボード表示")

    widget_options = {
        "🎯 今日の目標": "goal",
        "⏱️ 今日の勉強時間": "today",
        "📊 目標達成率": "rate",
        "🔥 連続勉強日数": "streak",
        "💬 今日のコメント": "comment",
        "📈 週間勉強グラフ": "weekly",
        "📚 科目別勉強時間": "subjects",
        "🏆 バッジ": "badges",
        "📝 最近の勉強記録": "records"
    }

    selected_widgets = st.multiselect(
        "表示する項目を選択",
        list(widget_options.keys()),
        default=list(widget_options.keys())
    )

    st.divider()

    st.info(
        "💡 表示したいダッシュボード項目を自由に選べます。"
    )


# =========================================================
# 今日のデータ
# =========================================================

today_minutes = get_today_minutes()
today_goal = get_today_goal()

if today_goal > 0:
    achievement_rate = min(
        int(today_minutes / today_goal * 100),
        100
    )
else:
    achievement_rate = 0


# =========================================================
# ダッシュボード
# =========================================================

st.header("🏠 今日のダッシュボード")

# 今日の目標
if "🎯 今日の目標" in selected_widgets:

    st.subheader("🎯 今日の目標")

    col1, col2 = st.columns([2, 1])

    with col1:
        new_goal = st.number_input(
            "今日の目標時間（分）",
            min_value=1,
            max_value=1000,
            value=int(today_goal),
            step=10
        )

    with col2:
        if st.button("💾 目標を保存"):
            save_goal(new_goal)
            st.success("目標を保存しました！")
            st.rerun()


# メトリクス
metric_items = []

if "⏱️ 今日の勉強時間" in selected_widgets:
    metric_items.append(("⏱️ 今日の勉強時間", f"{today_minutes} 分"))

if "📊 目標達成率" in selected_widgets:
    metric_items.append(("📊 目標達成率", f"{achievement_rate}%"))

if "🔥 連続勉強日数" in selected_widgets:
    metric_items.append(("🔥 連続勉強日数", f"{get_streak()} 日"))

if metric_items:

    cols = st.columns(len(metric_items))

    for col, (label, value) in zip(cols, metric_items):
        with col:
            st.metric(label, value)


# 達成率
if "📊 目標達成率" in selected_widgets:

    st.progress(
        achievement_rate / 100,
        text=f"今日の目標達成率：{achievement_rate}%"
    )

    if achievement_rate >= 100:
        st.success("🎉 今日の目標を達成しました！")
    else:
        remaining = max(today_goal - today_minutes, 0)
        st.info(f"あと {remaining} 分で今日の目標達成です。")


# =========================================================
# 今日のコメント
# =========================================================

if "💬 今日のコメント" in selected_widgets:

    st.divider()
    st.subheader("💬 今日のコメント")

    current_comment = get_today_comment()

    comment = st.text_area(
        "今日の勉強について一言",
        value=current_comment,
        placeholder="例：英語長文を頑張った！",
        height=100
    )

    if st.button("💾 コメントを保存"):
        save_today_comment(comment)
        st.success("コメントを保存しました！")


# =========================================================
# 週間グラフ
# =========================================================

if "📈 週間勉強グラフ" in selected_widgets:

    st.divider()
    st.subheader("📈 過去7日間の勉強時間")

    weekly_data = get_weekly_minutes()

    weekly_df = pd.DataFrame(weekly_data)

    st.bar_chart(
        weekly_df.set_index("日付")
    )


# =========================================================
# 科目別勉強時間
# =========================================================

if "📚 科目別勉強時間" in selected_widgets:

    st.divider()
    st.subheader("📚 科目別勉強時間")

    subject_data = get_subject_minutes()

    if subject_data:

        subject_df = pd.DataFrame(
            subject_data,
            columns=["科目", "勉強時間"]
        )

        st.bar_chart(
            subject_df.set_index("科目")
        )

    else:
        st.info("まだ勉強記録がありません。")


# =========================================================
# バッジ
# =========================================================

if "🏆 バッジ" in selected_widgets:

    st.divider()
    st.subheader("🏆 獲得バッジ")

    badges = get_badges()

    if badges:

        badge_cols = st.columns(
            min(len(badges), 3)
        )

        for i, (icon, name, description) in enumerate(badges):

            with badge_cols[i % len(badge_cols)]:

                st.success(
                    f"{icon} **{name}**\n\n{description}"
                )

    else:
        st.info(
            "まだバッジを獲得していません。\n"
            "勉強を記録してバッジを集めよう！"
        )


# =========================================================
# タイマー
# =========================================================

st.divider()
st.header("⏱️ 勉強タイマー")


@st.fragment(run_every="1s")
def timer_area():

    # -----------------------------------------------------
    # タイマーが動いている場合
    # -----------------------------------------------------

    if st.session_state.timer_running:

        if not st.session_state.timer_paused:

            remaining = int(
                (
                    st.session_state.timer_end_time
                    - datetime.now(JST)
                ).total_seconds()
            )

            st.session_state.timer_remaining_seconds = max(
                remaining,
                0
            )

            # 時間終了
            if remaining <= 0:

                if not st.session_state.timer_saved:

                    total_minutes = (
                        st.session_state.timer_total_seconds
                        // 60
                    )

                    if total_minutes > 0:

                        save_record(
                            today_string(),
                            st.session_state.timer_subject,
                            total_minutes,
                            "タイマーで記録"
                        )

                    st.session_state.timer_saved = True

                st.session_state.timer_running = False
                st.session_state.timer_paused = False

                st.success(
                    "🎉 タイマー終了！勉強記録を保存しました！"
                )

                return

    # -----------------------------------------------------
    # タイマー表示
    # -----------------------------------------------------

    if st.session_state.timer_running:

        remaining_seconds = st.session_state.timer_remaining_seconds

        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60

        st.markdown(
            f"""
            <div style="
                text-align:center;
                font-size:70px;
                font-weight:bold;
                padding:20px;
            ">
            {minutes:02d}:{seconds:02d}
            </div>
            """,
            unsafe_allow_html=True
        )

        st.write(
            f"📚 科目：**{st.session_state.timer_subject}**"
        )

        col1, col2, col3 = st.columns(3)

        # 一時停止
        with col1:

            if not st.session_state.timer_paused:

                if st.button(
                    "⏸️ 一時停止",
                    use_container_width=True
                ):

                    remaining_seconds = int(
                        (
                            st.session_state.timer_end_time
                            - datetime.now(JST)
                        ).total_seconds()
                    )

                    st.session_state.timer_remaining_seconds = max(
                        remaining_seconds,
                        0
                    )

                    st.session_state.timer_paused = True

                    st.rerun()

            else:

                st.write("⏸️ 一時停止中")

        # 再開
        with col2:

            if st.session_state.timer_paused:

                if st.button(
                    "▶️ 再開",
                    use_container_width=True
                ):

                    st.session_state.timer_end_time = (
                        datetime.now(JST)
                        + timedelta(
                            seconds=st.session_state.timer_remaining_seconds
                        )
                    )

                    st.session_state.timer_paused = False

                    st.rerun()

        # 終了
        with col3:

            if st.button(
                "🛑 終了して保存",
                use_container_width=True
            ):

                elapsed_seconds = (
                    st.session_state.timer_total_seconds
                    - st.session_state.timer_remaining_seconds
                )

                elapsed_minutes = elapsed_seconds // 60

                if elapsed_minutes > 0:

                    save_record(
                        today_string(),
                        st.session_state.timer_subject,
                        elapsed_minutes,
                        "タイマーで記録"
                    )

                st.session_state.timer_running = False
                st.session_state.timer_paused = False
                st.session_state.timer_saved = True

                st.success(
                    f"📝 {elapsed_minutes}分を記録しました！"
                )

                st.rerun()

    # -----------------------------------------------------
    # タイマー開始前
    # -----------------------------------------------------

    else:

        col1, col2 = st.columns(2)

        with col1:

            timer_subject = st.selectbox(
                "📚 科目",
                SUBJECTS
            )

        with col2:

            timer_minutes = st.number_input(
                "⏱️ 勉強時間（分）",
                min_value=1,
                max_value=600,
                value=30,
                step=5
            )

        if st.button(
            "▶️ 勉強開始",
            type="primary",
            use_container_width=True
        ):

            st.session_state.timer_running = True
            st.session_state.timer_paused = False
            st.session_state.timer_subject = timer_subject

            st.session_state.timer_total_seconds = (
                timer_minutes * 60
            )

            st.session_state.timer_remaining_seconds = (
                timer_minutes * 60
            )

            st.session_state.timer_end_time = (
                datetime.now(JST)
                + timedelta(minutes=timer_minutes)
            )

            st.session_state.timer_saved = False

            st.rerun()


timer_area()


# =========================================================
# 科目別目標
# =========================================================

st.divider()
st.header("🎯 科目別目標")

subject_goal_subject = st.selectbox(
    "科目を選択",
    SUBJECTS,
    key="subject_goal_subject"
)

current_subject_goal = get_subject_goal(
    subject_goal_subject
)

new_subject_goal = st.number_input(
    "この科目の目標時間（分）",
    min_value=0,
    max_value=10000,
    value=int(current_subject_goal),
    step=10
)

if st.button("💾 科目別目標を保存"):

    save_subject_goal(
        subject_goal_subject,
        new_subject_goal
    )

    st.success(
        f"{subject_goal_subject}の目標を保存しました！"
    )


# =========================================================
# 最近の勉強記録
# =========================================================

if "📝 最近の勉強記録" in selected_widgets:

    st.divider()
    st.header("📝 最近の勉強記録")

    records = get_recent_records()

    if records:

        for record in records:

            record_id = record[0]
            study_date = record[1]
            subject = record[2]
            minutes = record[3]
            memo = record[4]

            col1, col2, col3, col4 = st.columns(
                [1.3, 1, 1, 0.7]
            )

            with col1:
                st.write(f"📅 {study_date}")

            with col2:
                st.write(f"📚 {subject}")

            with col3:
                st.write(f"⏱️ {minutes}分")

            with col4:

                if st.button(
                    "削除",
                    key=f"delete_{record_id}"
                ):

                    delete_record(record_id)

                    st.success("記録を削除しました。")

                    st.rerun()

            if memo:
                st.caption(f"📝 {memo}")

    else:

        st.info(
            "まだ勉強記録がありません。"
        )


# =========================================================
# フッター
# =========================================================

st.divider()

st.caption(
    "📚 Study Focus | 勉強を記録して、継続を見える化しよう。"
)
