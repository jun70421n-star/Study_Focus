import streamlit as st
import sqlite3
from datetime import date, datetime, timedelta
import pandas as pd


# =========================================================
# 基本設定
# =========================================================

st.set_page_config(
    page_title="Study Focus",
    page_icon="📚",
    layout="wide"
)

DB_NAME = "study_focus.db"

SUBJECTS = [
    "英語",
    "国語",
    "数学",
    "理科",
    "社会",
    "総合問題",
    "面接",
    "その他"
]


# =========================================================
# データベース
# =========================================================

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


# =========================================================
# 勉強記録
# =========================================================

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
        int(minutes),
        memo
    ))

    conn.commit()
    conn.close()


def delete_record(record_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    DELETE FROM study_records
    WHERE id = ?
    """, (record_id,))

    conn.commit()
    conn.close()


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
# 今日の目標
# =========================================================

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
        int(minutes)
    ))

    conn.commit()
    conn.close()


# =========================================================
# 履歴データ
# =========================================================

def get_all_records():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, study_date, subject, minutes, memo
    FROM study_records
    ORDER BY study_date DESC, id DESC
    """)

    records = cursor.fetchall()

    conn.close()

    return records


def get_records_by_period(start_date, end_date):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, study_date, subject, minutes, memo
    FROM study_records
    WHERE study_date BETWEEN ? AND ?
    ORDER BY study_date DESC, id DESC
    """, (
        str(start_date),
        str(end_date)
    ))

    records = cursor.fetchall()

    conn.close()

    return records


def get_period_minutes(start_date, end_date):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT COALESCE(SUM(minutes), 0)
    FROM study_records
    WHERE study_date BETWEEN ? AND ?
    """, (
        str(start_date),
        str(end_date)
    ))

    result = cursor.fetchone()[0]

    conn.close()

    return result


def get_subject_totals(start_date=None, end_date=None):

    conn = get_connection()
    cursor = conn.cursor()

    if start_date is None:

        cursor.execute("""
        SELECT subject, SUM(minutes)
        FROM study_records
        GROUP BY subject
        ORDER BY SUM(minutes) DESC
        """)

    else:

        cursor.execute("""
        SELECT subject, SUM(minutes)
        FROM study_records
        WHERE study_date BETWEEN ? AND ?
        GROUP BY subject
        ORDER BY SUM(minutes) DESC
        """, (
            str(start_date),
            str(end_date)
        ))

    result = cursor.fetchall()

    conn.close()

    return result


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

    rows = cursor.fetchall()

    conn.close()

    if not rows:
        return 0

    study_dates = [
        datetime.strptime(row[0], "%Y-%m-%d").date()
        for row in rows
    ]

    today = date.today()

    if study_dates[0] != today:
        return 0

    streak = 0
    current_day = today

    for study_day in study_dates:

        if study_day == current_day:

            streak += 1
            current_day -= timedelta(days=1)

        elif study_day < current_day:

            break

    return streak


# =========================================================
# 週間データ
# =========================================================

def get_weekly_data():

    data = []

    for i in range(6, -1, -1):

        target_day = date.today() - timedelta(days=i)

        minutes = get_period_minutes(
            target_day,
            target_day
        )

        data.append({
            "日付": target_day.strftime("%m/%d"),
            "勉強時間": minutes
        })

    return data


# =========================================================
# バッジ
# =========================================================

def get_badges():

    total = get_total_minutes()
    streak = get_streak()
    today_minutes = get_today_minutes()
    goal = get_today_goal()

    badges = []

    if total >= 60:
        badges.append(
            ("🌱", "はじめの一歩", "累計1時間")
        )

    if total >= 300:
        badges.append(
            ("🔥", "努力家", "累計5時間")
        )

    if total >= 1000:
        badges.append(
            ("🏆", "1000分突破", "累計1000分")
        )

    if streak >= 3:
        badges.append(
            ("🔥", "3日継続", "3日連続")
        )

    if streak >= 7:
        badges.append(
            ("💎", "1週間継続", "7日連続")
        )

    if today_minutes >= goal:
        badges.append(
            ("🎯", "目標達成", "今日の目標達成")
        )

    return badges


# =========================================================
# セッション状態
# =========================================================

if "timer_running" not in st.session_state:
    st.session_state.timer_running = False

if "timer_paused" not in st.session_state:
    st.session_state.timer_paused = False

if "timer_subject" not in st.session_state:
    st.session_state.timer_subject = "英語"

if "timer_memo" not in st.session_state:
    st.session_state.timer_memo = ""

if "timer_total_seconds" not in st.session_state:
    st.session_state.timer_total_seconds = 0

if "timer_remaining_seconds" not in st.session_state:
    st.session_state.timer_remaining_seconds = 0

if "timer_end_time" not in st.session_state:
    st.session_state.timer_end_time = None


# =========================================================
# タイトル
# =========================================================

st.title("📚 Study Focus")

st.write(
    "勉強をもっと続けやすくするアプリ"
)

st.divider()


# =========================================================
# サイドバー
# =========================================================

with st.sidebar:

    st.header("⚙️ 設定")

    st.subheader("🏠 ダッシュボード")

    dashboard_items = [
        "🎯 今日の目標",
        "⏱️ 今日の勉強時間",
        "📊 目標達成率",
        "🔥 連続勉強日数",
        "📈 週間グラフ",
        "📚 科目別時間",
        "🏆 バッジ",
        "📝 最近の記録"
    ]

    selected_items = st.multiselect(
        "表示する項目",
        dashboard_items,
        default=dashboard_items
    )


# =========================================================
# 今日のデータ
# =========================================================

goal_minutes = get_today_goal()
today_minutes = get_today_minutes()

if goal_minutes > 0:

    achievement = min(
        int(today_minutes / goal_minutes * 100),
        100
    )

else:

    achievement = 0

remaining = max(
    goal_minutes - today_minutes,
    0
)


# =========================================================
# 今日のダッシュボード
# =========================================================

st.header("🏠 今日のダッシュボード")


if "🎯 今日の目標" in selected_items:

    st.subheader("🎯 今日の目標")

    col1, col2 = st.columns([3, 1])

    with col1:

        new_goal = st.number_input(
            "目標時間（分）",
            min_value=1,
            max_value=1000,
            value=int(goal_minutes),
            step=10
        )

    with col2:

        st.write("")
        st.write("")

        if st.button(
            "💾 保存",
            use_container_width=True
        ):

            save_goal(new_goal)

            st.success(
                "目標を保存しました！"
            )

            st.rerun()


# =========================================================
# メトリクス
# =========================================================

metric_labels = []
metric_values = []


if "⏱️ 今日の勉強時間" in selected_items:

    metric_labels.append("⏱️ 今日の勉強時間")
    metric_values.append(f"{today_minutes} 分")


if "📊 目標達成率" in selected_items:

    metric_labels.append("📊 目標達成率")
    metric_values.append(f"{achievement}%")


if "🔥 連続勉強日数" in selected_items:

    metric_labels.append("🔥 連続勉強日数")
    metric_values.append(f"{get_streak()} 日")


if metric_labels:

    cols = st.columns(len(metric_labels))

    for i in range(len(metric_labels)):

        with cols[i]:

            st.metric(
                metric_labels[i],
                metric_values[i]
            )


if "📊 目標達成率" in selected_items:

    st.progress(
        achievement / 100
    )

    if remaining == 0:

        st.success(
            "🎉 今日の目標達成！"
        )

    else:

        st.info(
            f"📚 目標まであと {remaining} 分"
        )


# =========================================================
# 週間グラフ
# =========================================================

if "📈 週間グラフ" in selected_items:

    st.divider()

    st.subheader(
        "📈 過去7日間の勉強時間"
    )

    weekly_data = get_weekly_data()

    weekly_df = pd.DataFrame(
        weekly_data
    )

    st.bar_chart(
        weekly_df.set_index("日付")
    )


# =========================================================
# 科目別時間
# =========================================================

if "📚 科目別時間" in selected_items:

    st.divider()

    st.subheader(
        "📚 科目別勉強時間"
    )

    subject_data = get_subject_totals()

    if subject_data:

        subject_df = pd.DataFrame(
            subject_data,
            columns=[
                "科目",
                "勉強時間"
            ]
        )

        st.bar_chart(
            subject_df.set_index("科目")
        )

    else:

        st.info(
            "まだ勉強記録がありません。"
        )


# =========================================================
# バッジ
# =========================================================

if "🏆 バッジ" in selected_items:

    st.divider()

    st.subheader(
        "🏆 獲得バッジ"
    )

    badges = get_badges()

    if badges:

        cols = st.columns(
            min(len(badges), 3)
        )

        for i, badge in enumerate(badges):

            icon = badge[0]
            name = badge[1]
            description = badge[2]

            with cols[i % len(cols)]:

                st.success(
                    f"{icon} **{name}**\n\n"
                    f"{description}"
                )

    else:

        st.info(
            "勉強を続けるとバッジを獲得できます！"
        )


# =========================================================
# タイマー
# =========================================================

st.divider()

st.header("⏱️ 勉強タイマー")


# タイマー開始前

if not st.session_state.timer_running:

    col1, col2 = st.columns(2)

    with col1:

        subject = st.selectbox(
            "📚 科目",
            SUBJECTS
        )

    with col2:

        timer_minutes = st.number_input(
            "⏰ 勉強時間（分）",
            min_value=1,
            max_value=600,
            value=25,
            step=5
        )

    timer_memo = st.text_input(
        "📝 勉強メモ（任意）",
        placeholder="例：英語長文ポラリス1を1題"
    )

    if st.button(
        "▶️ 勉強開始",
        type="primary",
        use_container_width=True
    ):

        st.session_state.timer_subject = subject

        st.session_state.timer_memo = timer_memo

        st.session_state.timer_total_seconds = (
            int(timer_minutes) * 60
        )

        st.session_state.timer_remaining_seconds = (
            int(timer_minutes) * 60
        )

        st.session_state.timer_end_time = (
            datetime.now()
            + timedelta(
                minutes=int(timer_minutes)
            )
        )

        st.session_state.timer_running = True
        st.session_state.timer_paused = False

        st.rerun()


# =========================================================
# タイマー動作中
# =========================================================

else:

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

    minutes_left = (
        remaining_seconds // 60
    )

    seconds_left = (
        remaining_seconds % 60
    )

    st.subheader(
        f"📚 {st.session_state.timer_subject}"
    )

    if st.session_state.timer_paused:

        st.warning(
            "⏸️ 一時停止中"
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

    # 終了

    if remaining_seconds <= 0:

        elapsed_minutes = (
            st.session_state.timer_total_seconds
            // 60
        )

        save_record(
            st.session_state.timer_subject,
            elapsed_minutes,
            st.session_state.timer_memo
        )

        st.session_state.timer_running = False
        st.session_state.timer_paused = False
        st.session_state.timer_end_time = None

        st.success(
            f"🎉 {elapsed_minutes}分の勉強を記録しました！"
        )

        st.balloons()

        st.rerun()

    # ボタン

    col1, col2, col3 = st.columns(3)

    with col1:

        if not st.session_state.timer_paused:

            if st.button(
                "⏸️ 一時停止",
                use_container_width=True
            ):

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

        if st.session_state.timer_paused:

            if st.button(
                "▶️ 再開",
                use_container_width=True
            ):

                st.session_state.timer_end_time = (
                    datetime.now()
                    + timedelta(
                        seconds=st.session_state.timer_remaining_seconds
                    )
                )

                st.session_state.timer_paused = False

                st.rerun()

    with col3:

        if st.button(
            "🛑 終了して保存",
            use_container_width=True
        ):

            elapsed_seconds = (
                st.session_state.timer_total_seconds
                - st.session_state.timer_remaining_seconds
            )

            elapsed_minutes = max(
                elapsed_seconds // 60,
                1
            )

            save_record(
                st.session_state.timer_subject,
                elapsed_minutes,
                st.session_state.timer_memo
            )

            st.session_state.timer_running = False
            st.session_state.timer_paused = False
            st.session_state.timer_end_time = None

            st.success(
                f"📝 {elapsed_minutes}分を記録しました！"
            )

            st.rerun()


# =========================================================
# 勉強履歴・分析
# =========================================================

st.divider()

st.header("📊 勉強履歴・分析")


tab1, tab2, tab3 = st.tabs([
    "📊 分析",
    "📅 履歴",
    "🔎 検索"
])


# =========================================================
# 分析
# =========================================================

with tab1:

    st.subheader(
        "📊 勉強時間の分析"
    )

    today = date.today()

    week_start = (
        today - timedelta(days=6)
    )

    month_start = today.replace(
        day=1
    )

    week_minutes = get_period_minutes(
        week_start,
        today
    )

    month_minutes = get_period_minutes(
        month_start,
        today
    )

    total_minutes = get_total_minutes()

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "今日",
            f"{today_minutes}分"
        )

    with col2:

        st.metric(
            "今週",
            f"{week_minutes}分"
        )

    with col3:

        st.metric(
            "今月",
            f"{month_minutes}分"
        )

    with col4:

        st.metric(
            "累計",
            f"{total_minutes}分"
        )

    st.divider()

    st.subheader(
        "📈 今週の勉強時間"
    )

    weekly_data = get_weekly_data()

    weekly_df = pd.DataFrame(
        weekly_data
    )

    st.bar_chart(
        weekly_df.set_index("日付")
    )

    st.subheader(
        "📚 今月の科目別勉強時間"
    )

    month_subjects = get_subject_totals(
        month_start,
        today
    )

    if month_subjects:

        month_df = pd.DataFrame(
            month_subjects,
            columns=[
                "科目",
                "勉強時間"
            ]
        )

        st.bar_chart(
            month_df.set_index("科目")
        )

    else:

        st.info(
            "今月の勉強記録はありません。"
        )


# =========================================================
# 全履歴
# =========================================================

with tab2:

    st.subheader(
        "📅 勉強履歴"
    )

    records = get_all_records()

    if not records:

        st.info(
            "まだ勉強記録がありません。"
        )

    else:

        for record in records:

            record_id = record[0]
            study_date = record[1]
            subject = record[2]
            minutes = record[3]
            memo = record[4]

            col1, col2, col3, col4 = st.columns(
                [1.4, 1, 1, 0.8]
            )

            with col1:

                st.write(
                    f"📅 {study_date}"
                )

            with col2:

                st.write(
                    f"📚 {subject}"
                )

            with col3:

                st.write(
                    f"⏱️ {minutes}分"
                )

            with col4:

                if st.button(
                    "🗑️ 削除",
                    key=f"delete_{record_id}"
                ):

                    delete_record(
                        record_id
                    )

                    st.rerun()

            if memo:

                st.caption(
                    f"📝 {memo}"
                )

            st.divider()


# =========================================================
# 検索
# =========================================================

with tab3:

    st.subheader(
        "🔎 勉強記録を検索"
    )

    col1, col2 = st.columns(2)

    with col1:

        search_start = st.date_input(
            "開始日",
            value=date.today() - timedelta(days=30)
        )

    with col2:

        search_end = st.date_input(
            "終了日",
            value=date.today()
        )

    search_subject = st.selectbox(
        "科目",
        ["すべて"] + SUBJECTS
    )

    search_records = get_records_by_period(
        search_start,
        search_end
    )

    if search_subject != "すべて":

        search_records = [
            record
            for record in search_records
            if record[2] == search_subject
        ]

    search_total = sum(
        record[3]
        for record in search_records
    )

    st.metric(
        "🔎 検索結果の合計",
        f"{search_total}分"
    )

    if search_records:

        for record in search_records:

            record_id = record[0]
            study_date = record[1]
            subject = record[2]
            minutes = record[3]
            memo = record[4]

            st.write(
                f"📅 **{study_date}**　"
                f"📚 **{subject}**　"
                f"⏱️ **{minutes}分**"
            )

            if memo:

                st.caption(
                    f"📝 {memo}"
                )

            st.divider()

    else:

        st.info(
            "条件に一致する記録はありません。"
        )


# =========================================================
# 最近の記録
# =========================================================

if "📝 最近の記録" in selected_items:

    st.divider()

    st.subheader(
        "📝 最近の勉強記録"
    )

    recent_records = get_all_records()[:5]

    if recent_records:

        for record in recent_records:

            st.write(
                f"📅 {record[1]}　"
                f"📚 {record[2]}　"
                f"⏱️ {record[3]}分"
            )

            if record[4]:

                st.caption(
                    f"📝 {record[4]}"
                )

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
