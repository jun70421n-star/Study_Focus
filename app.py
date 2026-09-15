import streamlit as st
import sqlite3
from datetime import date, datetime, timedelta
import pandas as pd
import calendar

DB_NAME = "study_focus.db"

SUBJECTS = [
    "英語", "国語", "数学", "理科", "社会",
    "総合問題", "面接", "その他"
]

st.set_page_config(
    page_title="Study Focus",
    page_icon="📚",
    layout="wide"
)


# =========================================================
# データベース
# =========================================================

def get_connection():
    return sqlite3.connect(DB_NAME)


def init_database():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS study_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        study_date TEXT NOT NULL,
        subject TEXT NOT NULL,
        minutes INTEGER NOT NULL,
        memo TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS daily_goals (
        goal_date TEXT PRIMARY KEY,
        goal_minutes INTEGER NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS subject_goals (
        subject TEXT PRIMARY KEY,
        goal_minutes INTEGER NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS daily_comments (
        comment_date TEXT PRIMARY KEY,
        comment TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS daily_reflections (
        reflection_date TEXT PRIMARY KEY,
        good TEXT,
        tomorrow TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS app_stats (
        key TEXT PRIMARY KEY,
        value INTEGER NOT NULL
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS target_dates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        target_date TEXT NOT NULL,
        priority TEXT NOT NULL DEFAULT '通常',
        achieved INTEGER NOT NULL DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


init_database()


# =========================================================
# 共通
# =========================================================

def today():
    return date.today()


def today_str():
    return today().isoformat()


def get_total_minutes():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(minutes), 0) FROM study_records")
    value = cur.fetchone()[0]
    conn.close()
    return value


# =========================================================
# 勉強記録
# =========================================================

def save_record(subject, minutes, memo=""):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO study_records
    (study_date, subject, minutes, memo)
    VALUES (?, ?, ?, ?)
    """, (today_str(), subject, int(minutes), memo))
    conn.commit()
    conn.close()


def delete_record(record_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM study_records WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()


def get_all_records():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT id, study_date, subject, minutes, memo
    FROM study_records
    ORDER BY study_date DESC, id DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_period_minutes(start_date, end_date):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT COALESCE(SUM(minutes), 0)
    FROM study_records
    WHERE study_date BETWEEN ? AND ?
    """, (str(start_date), str(end_date)))
    value = cur.fetchone()[0]
    conn.close()
    return value


def get_subject_totals(start_date=None, end_date=None):
    conn = get_connection()
    cur = conn.cursor()

    if start_date is None:
        cur.execute("""
        SELECT subject, SUM(minutes)
        FROM study_records
        GROUP BY subject
        ORDER BY SUM(minutes) DESC
        """)
    else:
        cur.execute("""
        SELECT subject, SUM(minutes)
        FROM study_records
        WHERE study_date BETWEEN ? AND ?
        GROUP BY subject
        ORDER BY SUM(minutes) DESC
        """, (str(start_date), str(end_date)))

    rows = cur.fetchall()
    conn.close()
    return rows


# =========================================================
# 今日の目標
# =========================================================

def get_today_goal():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT goal_minutes
    FROM daily_goals
    WHERE goal_date = ?
    """, (today_str(),))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else 180


def save_goal(minutes):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT OR REPLACE INTO daily_goals
    (goal_date, goal_minutes)
    VALUES (?, ?)
    """, (today_str(), int(minutes)))
    conn.commit()
    conn.close()


# =========================================================
# 科目別目標
# =========================================================

def get_subject_goal(subject):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT goal_minutes
    FROM subject_goals
    WHERE subject = ?
    """, (subject,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else 0


def save_subject_goal(subject, minutes):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT OR REPLACE INTO subject_goals
    (subject, goal_minutes)
    VALUES (?, ?)
    """, (subject, int(minutes)))
    conn.commit()
    conn.close()

# =========================================================
# 目標日
# =========================================================

def get_target_dates():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT id, title, target_date, priority, achieved
    FROM target_dates
    ORDER BY achieved ASC, target_date ASC, id ASC
    """)

    rows = cur.fetchall()
    conn.close()

    return rows


def save_target_date(title, target_date, priority):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO target_dates
    (title, target_date, priority)
    VALUES (?, ?, ?)
    """, (
        title,
        str(target_date),
        priority
    ))

    conn.commit()
    conn.close()


def update_target_achieved(target_id, achieved):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    UPDATE target_dates
    SET achieved = ?
    WHERE id = ?
    """, (
        int(achieved),
        target_id
    ))

    conn.commit()
    conn.close()


def delete_target_date(target_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    DELETE FROM target_dates
    WHERE id = ?
    """, (target_id,))

    conn.commit()
    conn.close()

# =========================================================
# コメント・振り返り
# =========================================================

def get_comment():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT comment FROM daily_comments
    WHERE comment_date = ?
    """, (today_str(),))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else ""


def save_comment(comment):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT OR REPLACE INTO daily_comments
    (comment_date, comment)
    VALUES (?, ?)
    """, (today_str(), comment))
    conn.commit()
    conn.close()


def get_reflection():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT good, tomorrow
    FROM daily_reflections
    WHERE reflection_date = ?
    """, (today_str(),))
    row = cur.fetchone()
    conn.close()
    return row if row else ("", "")


def save_reflection(good, tomorrow):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT OR REPLACE INTO daily_reflections
    (reflection_date, good, tomorrow)
    VALUES (?, ?, ?)
    """, (today_str(), good, tomorrow))
    conn.commit()
    conn.close()


# =========================================================
# 連続日数・最高記録
# =========================================================

def get_study_dates():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT DISTINCT study_date
    FROM study_records
    WHERE minutes > 0
    ORDER BY study_date DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return {
        datetime.strptime(row[0], "%Y-%m-%d").date()
        for row in rows
    }


def get_streak():
    dates = get_study_dates()
    if today() not in dates:
        return 0

    streak = 0
    current = today()

    while current in dates:
        streak += 1
        current -= timedelta(days=1)

    return streak


def get_max_streak():
    dates = get_study_dates()
    if not dates:
        return 0

    max_streak = 0
    current_streak = 0
    previous = None

    for d in sorted(dates):
        if previous is not None and d == previous + timedelta(days=1):
            current_streak += 1
        else:
            current_streak = 1

        max_streak = max(max_streak, current_streak)
        previous = d

    return max_streak


# =========================================================
# バッジ
# =========================================================

def get_badges():
    total = get_total_minutes()
    streak = get_streak()
    max_streak = get_max_streak()
    today_minutes = get_period_minutes(today(), today)
    goal = get_today_goal()

    badges = [
        ("🌱", "はじめの一歩", "初めて勉強を記録する", total >= 1),
        ("⏱️", "1時間突破", "累計60分", total >= 60),
        ("🔥", "努力家", "累計300分", total >= 300),
        ("🏆", "1000分突破", "累計1000分", total >= 1000),
        ("💎", "5000分突破", "累計5000分", total >= 5000),
        ("🔥", "3日継続", "3日連続", max_streak >= 3),
        ("💎", "1週間継続", "7日連続", max_streak >= 7),
        ("👑", "30日継続", "30日連続", max_streak >= 30),
        ("🎯", "今日の目標達成", "今日の目標を達成", today_minutes >= goal),
    ]

    return badges


# =========================================================
# 週間データ・カレンダー
# =========================================================

def get_weekly_data():
    rows = []
    for i in range(6, -1, -1):
        d = today() - timedelta(days=i)
        rows.append({
            "日付": d.strftime("%m/%d"),
            "勉強時間": get_period_minutes(d, d)
        })
    return rows


def get_month_data(year, month):
    days = calendar.monthrange(year, month)[1]
    rows = []

    for day in range(1, days + 1):
        d = date(year, month, day)
        rows.append({
            "日付": d,
            "勉強時間": get_period_minutes(d, d)
        })

    return rows


# =========================================================
# タイマー
# =========================================================

for key, default in {
    "timer_running": False,
    "timer_paused": False,
    "timer_subject": "英語",
    "timer_memo": "",
    "timer_total_seconds": 0,
    "timer_remaining_seconds": 0,
    "timer_end_time": None
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# =========================================================
# タイトル
# =========================================================

st.title("📚 Study Focus")
st.caption("勉強をもっと続けやすくするアプリ")
st.divider()


# =========================================================
# サイドバー
# =========================================================

with st.sidebar:
    st.header("⚙️ 設定")

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
        "ホームに表示する項目",
        dashboard_items,
        default=dashboard_items
    )


# =========================================================
# ダッシュボード
# =========================================================

today_minutes = get_period_minutes(today(), today)
goal_minutes = get_today_goal()

achievement = (
    min(int(today_minutes / goal_minutes * 100), 100)
    if goal_minutes > 0 else 0
)

st.header("🏠 今日のダッシュボード")
# =========================================================
# 🎯 MY GOALS
# =========================================================

st.subheader("🎯 MY GOALS")

st.caption(
    "勉強・部活・試験・イベントなど、自分で決めた目標日を登録できます。"
)

targets = get_target_dates()

if targets:

    for target_id, title, target_date_text, priority, achieved in targets:

        target_date_value = datetime.strptime(
            target_date_text,
            "%Y-%m-%d"
        ).date()

        days_left = (target_date_value - today()).days

        # 目標の状態
        if achieved:
            status_text = "🎉 達成！"

        elif days_left > 0:
            status_text = f"あと {days_left} 日"

        elif days_left == 0:
            status_text = "🔥 今日が目標日！"

        else:
            status_text = f"{abs(days_left)}日経過"

        # 優先度
        if priority == "最重要":
            badge = "🔴 最重要"
            border = "#e53935"

        elif priority == "重要":
            badge = "🟠 重要"
            border = "#fb8c00"

        else:
            badge = "🔵 通常"
            border = "#1976d2"

        # 目標カード
        st.markdown(
            f"""
            <div style="
                border: 3px solid {border};
                border-radius: 16px;
                padding: 18px;
                margin: 10px 0;
                background: rgba(128,128,128,0.06);
            ">

                <div style="
                    font-size: 15px;
                    font-weight: bold;
                ">
                    {badge}
                </div>

                <div style="
                    font-size: 24px;
                    font-weight: 700;
                    margin-top: 5px;
                ">
                    🎯 {title}
                </div>

                <div style="
                    font-size: 17px;
                    margin-top: 6px;
                ">
                    目標日：
                    <strong>
                        {target_date_value.strftime("%Y/%m/%d")}
                    </strong>
                </div>

                <div style="
                    font-size: 32px;
                    font-weight: 900;
                    margin-top: 8px;
                ">
                    {status_text}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

        col1, col2 = st.columns(2)

        with col1:

            new_achieved = st.checkbox(
                "🎉 達成済みにする",
                value=bool(achieved),
                key=f"achieved_{target_id}"
            )

            if new_achieved != bool(achieved):

                update_target_achieved(
                    target_id,
                    new_achieved
                )

                st.rerun()

        with col2:

            if st.button(
                "🗑️ この目標を削除",
                key=f"delete_target_{target_id}",
                use_container_width=True
            ):

                delete_target_date(target_id)

                st.rerun()

else:

    st.info(
        "まだ目標がありません。「＋ 目標を追加」から登録できます。"
    )


# =========================================================
# 目標追加
# =========================================================

with st.expander("＋ 目標を追加"):

    target_title = st.text_input(
        "目標名",
        placeholder="例：英単語1900語を完成させる"
    )

    target_date = st.date_input(
        "目標日",
        value=today() + timedelta(days=30)
    )

    target_priority = st.selectbox(
        "重要度",
        [
            "最重要",
            "重要",
            "通常"
        ]
    )

    if st.button(
        "🎯 この目標を追加",
        type="primary",
        use_container_width=True
    ):

        if not target_title.strip():

            st.error("目標名を入力してください。")

        else:

            save_target_date(
                target_title.strip(),
                target_date,
                target_priority
            )

            st.success("目標を追加しました！")

            st.rerun()
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
        if st.button("💾 目標を保存", use_container_width=True):
            save_goal(new_goal)
            st.success("保存しました！")
            st.rerun()


metrics = []

if "⏱️ 今日の勉強時間" in selected_items:
    metrics.append(("⏱️ 今日", f"{today_minutes}分"))

if "📊 目標達成率" in selected_items:
    metrics.append(("📊 達成率", f"{achievement}%"))

if "🔥 連続勉強日数" in selected_items:
    metrics.append(("🔥 現在の連続日数", f"{get_streak()}日"))

if metrics:
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics):
        with col:
            st.metric(label, value)


if "📊 目標達成率" in selected_items:
    st.progress(achievement / 100)

    if today_minutes >= goal_minutes:
        st.success("🎉 今日の目標達成！")
    else:
        st.info(f"あと {goal_minutes - today_minutes} 分で達成です。")


# =========================================================
# 週間グラフ
# =========================================================

if "📈 週間グラフ" in selected_items:
    st.divider()
    st.subheader("📈 過去7日間")

    weekly_df = pd.DataFrame(get_weekly_data())
    st.bar_chart(weekly_df.set_index("日付"))


# =========================================================
# 科目別
# =========================================================

if "📚 科目別時間" in selected_items:
    st.divider()
    st.subheader("📚 科目別勉強時間")

    data = get_subject_totals()

    if data:
        df = pd.DataFrame(data, columns=["科目", "勉強時間"])
        st.bar_chart(df.set_index("科目"))
    else:
        st.info("まだ記録がありません。")


# =========================================================
# バッジ
# =========================================================

if "🏆 バッジ" in selected_items:
    st.divider()
    st.subheader("🏆 バッジ")

    badges = get_badges()
    cols = st.columns(3)

    for i, (icon, name, condition, achieved) in enumerate(badges):
        with cols[i % 3]:
            if achieved:
                st.success(f"{icon} **{name}**\n\n{condition}")
            else:
                st.info(f"🔒 **{name}**\n\n{condition}")


# =========================================================
# タイマー
# =========================================================

st.divider()
st.header("⏱️ 勉強タイマー")

if not st.session_state.timer_running:

    col1, col2 = st.columns(2)

    with col1:
        subject = st.selectbox("📚 科目", SUBJECTS)

    with col2:
        timer_minutes = st.number_input(
            "⏰ 時間（分）",
            min_value=1,
            max_value=600,
            value=25,
            step=5
        )

    timer_memo = st.text_input(
        "📝 メモ（任意）",
        placeholder="例：英語長文を1題"
    )

    if st.button(
        "▶️ 勉強開始",
        type="primary",
        use_container_width=True
    ):
        st.session_state.timer_subject = subject
        st.session_state.timer_memo = timer_memo
        st.session_state.timer_total_seconds = int(timer_minutes) * 60
        st.session_state.timer_remaining_seconds = int(timer_minutes) * 60
        st.session_state.timer_end_time = (
            datetime.now() + timedelta(minutes=int(timer_minutes))
        )
        st.session_state.timer_running = True
        st.session_state.timer_paused = False
        st.rerun()

else:

    if not st.session_state.timer_paused:
        remaining = int(
            (
                st.session_state.timer_end_time
                - datetime.now()
            ).total_seconds()
        )
        st.session_state.timer_remaining_seconds = max(remaining, 0)

    remaining = st.session_state.timer_remaining_seconds
    mm = remaining // 60
    ss = remaining % 60

    st.write(f"📚 科目：**{st.session_state.timer_subject}**")

    if st.session_state.timer_paused:
        st.warning("⏸️ 一時停止中")

    st.markdown(
        f"""
        <div style="
            text-align:center;
            font-size:72px;
            font-weight:bold;
            padding:20px;
        ">
        {mm:02d}:{ss:02d}
        </div>
        """,
        unsafe_allow_html=True
    )

    if remaining <= 0:
        elapsed = st.session_state.timer_total_seconds // 60

        if elapsed > 0:
            save_record(
                st.session_state.timer_subject,
                elapsed,
                st.session_state.timer_memo
            )

        st.session_state.timer_running = False
        st.session_state.timer_paused = False
        st.session_state.timer_end_time = None

        st.success(f"🎉 {elapsed}分を記録しました！")
        st.balloons()
        st.rerun()

    col1, col2, col3 = st.columns(3)

    with col1:
        if not st.session_state.timer_paused:
            if st.button("⏸️ 一時停止", use_container_width=True):
                remaining = int(
                    (
                        st.session_state.timer_end_time
                        - datetime.now()
                    ).total_seconds()
                )
                st.session_state.timer_remaining_seconds = max(
                    remaining, 0
                )
                st.session_state.timer_paused = True
                st.rerun()

    with col2:
        if st.session_state.timer_paused:
            if st.button("▶️ 再開", use_container_width=True):
                st.session_state.timer_end_time = (
                    datetime.now()
                    + timedelta(
                        seconds=st.session_state.timer_remaining_seconds
                    )
                )
                st.session_state.timer_paused = False
                st.rerun()

    with col3:
        if st.button("🛑 終了して保存", use_container_width=True):
            elapsed_seconds = (
                st.session_state.timer_total_seconds
                - st.session_state.timer_remaining_seconds
            )
            elapsed_minutes = max(elapsed_seconds // 60, 1)

            save_record(
                st.session_state.timer_subject,
                elapsed_minutes,
                st.session_state.timer_memo
            )

            st.session_state.timer_running = False
            st.session_state.timer_paused = False
            st.session_state.timer_end_time = None

            st.success(f"📝 {elapsed_minutes}分を記録しました！")
            st.rerun()


# =========================================================
# 科目別目標
# =========================================================

st.divider()
st.header("🎯 科目別目標")

col1, col2 = st.columns(2)

with col1:
    goal_subject = st.selectbox(
        "科目",
        SUBJECTS,
        key="goal_subject"
    )

with col2:
    current = get_subject_goal(goal_subject)
    subject_goal = st.number_input(
        "目標時間（分）",
        min_value=0,
        max_value=10000,
        value=int(current),
        step=10
    )

if st.button("💾 科目別目標を保存"):
    save_subject_goal(goal_subject, subject_goal)
    st.success(f"{goal_subject}の目標を保存しました！")


# =========================================================
# 今日の振り返り
# =========================================================

st.divider()
st.header("💬 今日の振り返り")

old_comment = get_comment()
good_old, tomorrow_old = get_reflection()

comment = st.text_area(
    "今日の一言",
    value=old_comment,
    placeholder="今日の気分や勉強について一言"
)

good = st.text_area(
    "✅ 今日できたこと",
    value=good_old,
    placeholder="例：英語長文を2題できた"
)

tomorrow = st.text_area(
    "📌 明日やること",
    value=tomorrow_old,
    placeholder="例：総合問題の図表問題を30分やる"
)

if st.button("💾 振り返りを保存"):
    save_comment(comment)
    save_reflection(good, tomorrow)
    st.success("振り返りを保存しました！")


# =========================================================
# カレンダー
# =========================================================

st.divider()
st.header("📅 勉強カレンダー")

selected_month = st.date_input(
    "確認する月",
    value=today(),
    key="calendar_month"
)

year = selected_month.year
month = selected_month.month

month_data = get_month_data(year, month)

calendar_df = pd.DataFrame(month_data)
calendar_df["日付"] = pd.to_datetime(calendar_df["日付"])
calendar_df["日"] = calendar_df["日付"].dt.day

if calendar_df["勉強時間"].sum() > 0:
    st.bar_chart(
        calendar_df.set_index("日")
        [["勉強時間"]]
    )
else:
    st.info("この月にはまだ勉強記録がありません。")

study_days = sum(
    minutes > 0
    for minutes in calendar_df["勉強時間"]
)

month_total = int(calendar_df["勉強時間"].sum())

col1, col2 = st.columns(2)

with col1:
    st.metric("📅 勉強した日数", f"{study_days}日")

with col2:
    st.metric("⏱️ 月間勉強時間", f"{month_total}分")


# =========================================================
# 履歴・分析
# =========================================================

st.divider()
st.header("📊 履歴・分析")

tab1, tab2, tab3 = st.tabs([
    "📊 分析",
    "📅 履歴",
    "🔎 検索"
])


with tab1:

    today_date = today()
    week_start = today_date - timedelta(days=6)
    month_start = today_date.replace(day=1)

    week_total = get_period_minutes(
        week_start,
        today_date
    )

    month_total = get_period_minutes(
        month_start,
        today_date
    )

    total = get_total_minutes()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("今日", f"{today_minutes}分")

    with col2:
        st.metric("今週", f"{week_total}分")

    with col3:
        st.metric("今月", f"{month_total}分")

    with col4:
        st.metric("累計", f"{total}分")

    st.subheader("🔥 継続記録")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "現在の連続日数",
            f"{get_streak()}日"
        )

    with col2:
        st.metric(
            "最高連続日数",
            f"{get_max_streak()}日"
        )


with tab2:

    records = get_all_records()

    if not records:
        st.info("まだ勉強記録がありません。")

    for record in records:

        record_id, study_date, subject, minutes, memo = record

        col1, col2, col3, col4 = st.columns(
            [1.4, 1, 1, 0.7]
        )

        with col1:
            st.write(f"📅 {study_date}")

        with col2:
            st.write(f"📚 {subject}")

        with col3:
            st.write(f"⏱️ {minutes}分")

        with col4:
            if st.button(
                "🗑️",
                key=f"delete_history_{record_id}"
            ):
                delete_record(record_id)
                st.rerun()

        if memo:
            st.caption(f"📝 {memo}")

        st.divider()


with tab3:

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "開始日",
            value=today() - timedelta(days=30),
            key="search_start"
        )

    with col2:
        end_date = st.date_input(
            "終了日",
            value=today(),
            key="search_end"
        )

    search_subject = st.selectbox(
        "科目",
        ["すべて"] + SUBJECTS,
        key="search_subject"
    )

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT id, study_date, subject, minutes, memo
    FROM study_records
    WHERE study_date BETWEEN ? AND ?
    ORDER BY study_date DESC, id DESC
    """, (str(start_date), str(end_date)))

    results = cur.fetchall()
    conn.close()

    if search_subject != "すべて":
        results = [
            r for r in results
            if r[2] == search_subject
        ]

    result_total = sum(r[3] for r in results)

    st.metric(
        "🔎 検索結果の合計",
        f"{result_total}分"
    )

    if results:
        for record in results:
            st.write(
                f"📅 **{record[1]}**　"
                f"📚 **{record[2]}**　"
                f"⏱️ **{record[3]}分**"
            )

            if record[4]:
                st.caption(f"📝 {record[4]}")

            st.divider()
    else:
        st.info("条件に一致する記録はありません。")


# =========================================================
# 最近の記録
# =========================================================

if "📝 最近の記録" in selected_items:

    st.divider()
    st.subheader("📝 最近の勉強記録")

    recent = get_all_records()[:5]

    if recent:
        for record in recent:
            st.write(
                f"📅 {record[1]}　"
                f"📚 {record[2]}　"
                f"⏱️ {record[3]}分"
            )

            if record[4]:
                st.caption(f"📝 {record[4]}")
    else:
        st.info("まだ記録がありません。")


# =========================================================
# フッター
# =========================================================

st.divider()

st.caption(
    "📚 Study Focus | 勉強を記録して、継続を見える化しよう。"
)
