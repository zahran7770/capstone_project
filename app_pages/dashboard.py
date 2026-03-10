import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from database.db import SessionLocal
from database.models import Transaction, Limit, SentimentFeedback
from utils.sentiment_feedback import save_feedback



def _sentiment_label(compound: float) -> str:
    """Map VADER compound score to a simple label."""
    if compound >= 0.05:
        return "Positive"
    if compound <= -0.05:
        return "Negative"
    return "Neutral"


def _mood_from_score(score: float) -> tuple[str, str]:
    """Return (emoji, label) for a single overall “mood” score. Score in [-1, 1]."""
    if score >= 0.35:
        return "😄", "Very Positive"
    if score >= 0.05:
        return "🙂", "Positive"
    if score > -0.05:
        return "😐", "Neutral"
    if score > -0.35:
        return "🙁", "Negative"
    return "😣", "Very Negative"


def _date_window(time_range: str) -> tuple[date | None, date | None]:
    """Return (start_date, end_date) inclusive. For All Time returns (None, None)."""
    end = date.today()
    if time_range == "Daily":
        return end, end
    if time_range == "Weekly":
        return end - timedelta(days=7), end
    if time_range == "Monthly":
        return end.replace(day=1), end
    return None, None  # All Time



def dashboard_page():
    # =========================
    # PROTECT PAGE
    # =========================
    if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
        st.warning("Please login first.")
        st.stop()

    user_id = st.session_state.get("user_id")
    if not user_id:
        st.error("Missing user_id. Please login again.")
        st.stop()
        # =========================
        # BUTTON STYLING (FINTECH STYLE)
        # =========================
        st.markdown(
            """
            <style>
            div.stButton > button {
                border-radius: 10px;
                font-weight: 600;
                height: 42px;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

    # =========================
    # HEADER
    # =========================
    st.caption("Track your spending. Stay in control.")
    st.markdown(f"### 👋 Welcome, {st.session_state.get('username', 'User')}")

    # =========================
    # FINTECH-STYLE DATE FILTER
    # =========================
    st.markdown("## 📅 Date Filter")

    # Initialize default filter values once
    if "start_date" not in st.session_state:
        st.session_state["start_date"] = date.today() - timedelta(days=30)

    if "end_date" not in st.session_state:
        st.session_state["end_date"] = date.today()

    # Quick range buttons
    b1, b2, b3, b4, b5 = st.columns(5)

    with b1:
        if st.button("Last 7 Days", use_container_width=True):
            st.session_state["start_date"] = date.today() - timedelta(days=7)
            st.session_state["end_date"] = date.today()

    with b2:
        if st.button("Last 30 Days", use_container_width=True):
            st.session_state["start_date"] = date.today() - timedelta(days=30)
            st.session_state["end_date"] = date.today()

    with b3:
        if st.button("This Month", use_container_width=True):
            st.session_state["start_date"] = date.today().replace(day=1)
            st.session_state["end_date"] = date.today()

    with b4:
        if st.button("This Year", use_container_width=True):
            st.session_state["start_date"] = date(date.today().year, 1, 1)
            st.session_state["end_date"] = date.today()

    with b5:
        if st.button("All Time", use_container_width=True):
            st.session_state["start_date"] = date(2000, 1, 1)
            st.session_state["end_date"] = date.today()

    # Manual date pickers
    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "Start Date",
            value=st.session_state["start_date"],
            key="dashboard_start_date",
        )

    with col2:
        end_date = st.date_input(
            "End Date",
            value=st.session_state["end_date"],
            key="dashboard_end_date",
        )

    # Save manual edits back into session
    st.session_state["start_date"] = start_date
    st.session_state["end_date"] = end_date

    # Safety check
    if start_date > end_date:
        st.error("Start Date cannot be after End Date.")
        st.stop()

    st.caption(f"Showing data from **{start_date}** to **{end_date}**")

    # =========================
    # LOAD DATA FROM DB
    # =========================
    db = SessionLocal()
    try:
        # Base query: all transactions for this user
        txs = (
            db.query(Transaction)
            .filter(
                Transaction.user_id == user_id,
                Transaction.date >= start_date,
                Transaction.date <= end_date,
            )
            .order_by(Transaction.date.desc())
            .all()
        )

        # Limits (optional) for budget alerts
        limits = db.query(Limit).filter(Limit.user_id == user_id).all()

        # Feedback for accuracy KPI
        feedback_rows = db.query(SentimentFeedback).filter(SentimentFeedback.user_id == user_id).all()
    finally:
        db.close()

    st.caption(f"Loaded {len(txs)} transactions from database.")

    # =========================
    # BUILD DATAFRAME (include id + sentiment fields)
    # =========================
    df = pd.DataFrame(
        [
            {
                "id": t.id,
                "date": t.date,
                "description": t.description,
                "amount": float(t.amount),
                "category": t.category or "Other",
                "source": getattr(t, "source", None),
                "sentiment_label": getattr(t, "sentiment_label", None),
                "sentiment_score": getattr(t, "sentiment_score", None),
            }
            for t in txs
        ]
    )

    if df.empty:
        st.info("No transactions found for this period. Upload a statement to see your dashboard.")
        return

    # =========================
    # KPIs (calculated)
    # =========================
    # Assumption: spending = negative amounts (adjust if your CSV uses positive for spend)
    spend_df = df[df["amount"] < 0].copy()
    spend_df["spend"] = spend_df["amount"].abs()

    today = date.today()

    today_spend = spend_df[spend_df["date"] == today]["spend"].sum()
    week_ago = today - timedelta(days=7)
    week_spend = spend_df[(spend_df["date"] >= week_ago) & (spend_df["date"] <= today)]["spend"].sum()
    month_start = today.replace(day=1)
    month_spend = spend_df[(spend_df["date"] >= month_start) & (spend_df["date"] <= today)]["spend"].sum()
    all_time_spend = spend_df["spend"].sum()

    monthly_budget = sum(l.monthly_limit for l in limits) if limits else 0.0
    remaining = (monthly_budget - month_spend) if monthly_budget else 0.0

    selected_label = "Selected Period"
    selected_spend = spend_df["spend"].sum()

    st.markdown("## Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(selected_label, f"${selected_spend:,.2f}")
    col2.metric("This Week", f"${week_spend:,.2f}")
    col3.metric("This Month", f"${month_spend:,.2f}")
    col4.metric("Remaining Budget", f"${remaining:,.2f}" if monthly_budget else "Set limits")

    # =========================
    # Sentiment Accuracy KPI (from feedback)
    # =========================
    if feedback_rows:
        correct = sum(1 for f in feedback_rows if int(f.is_correct) == 1)
        acc = correct / len(feedback_rows)
        st.metric("Sentiment Accuracy (from your feedback)", f"{acc * 100:.1f}%")
    else:
        st.info("No sentiment feedback yet. Use 👍/👎 below to measure accuracy.")

    # =========================
    # ALERT SECTION (based on limits)
    # =========================
    if monthly_budget > 0:
        if month_spend > monthly_budget:
            st.error("🚨 You have exceeded your monthly budget!")
        elif month_spend > monthly_budget * 0.8:
            st.warning("⚠️ You have used more than 80% of your budget.")
        else:
            st.success("✅ Budget is under control.")
    else:
        st.info("Set category limits to enable budget alerts and remaining budget calculations.")

    # =========================
    # CHARTS (real)
    # =========================
    st.markdown("## Spending Insights")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("By Category")
        if spend_df.empty:
            st.info("No spending transactions (negative amounts) found in this period.")
        else:
            cat_totals = spend_df.groupby("category")["spend"].sum().reset_index()

            fig = px.pie(
                cat_totals,
                names="category",
                values="spend",
                hole=0.5,  # donut style
                title="Spending by Category"
            )

            st.plotly_chart(fig, use_container_width=True)

    with chart_col2:
        st.subheader("Spending Trend")
        if spend_df.empty:
            st.info("No spending trend available.")
        else:
            daily_trend = spend_df.groupby("date")["spend"].sum().sort_index()
            st.line_chart(daily_trend)

    # =========================
    # RECENT TRANSACTIONS (real)
    # =========================
    st.markdown("## Recent Transactions")
    recent = df.sort_values("date", ascending=False).head(10).copy()
    recent["Amount"] = recent["amount"].map(lambda x: f"${x:,.2f}")
    recent.rename(columns={"date": "Date", "description": "Description", "category": "Category"}, inplace=True)
    st.dataframe(recent[["Date", "Description", "Category", "Amount"]], use_container_width=True, height=280)

    # =========================
    # ✅ FEEDBACK PANEL (inserted here)
    # =========================
    st.markdown("## ✅ Help Us Improve Sentiment")
    st.caption("Quickly confirm if the predicted sentiment looks right for the transaction description.")

    # Use the latest 5 transactions shown to the user
    feedback_df = df.sort_values("date", ascending=False).head(5).copy()

    # If sentiment wasn't saved yet for older rows, compute it on the fly (display only)
    analyzer = SentimentIntensityAnalyzer()

    for _, row in feedback_df.iterrows():
        tx_id = int(row["id"])
        desc = str(row["description"])
        predicted = row.get("sentiment_label")

        # If missing in DB, compute a display prediction
        if not predicted or predicted == "None":
            comp = analyzer.polarity_scores(desc)["compound"]
            predicted = _sentiment_label(comp)

        c1, c2, c3 = st.columns([4, 1, 1])

        with c1:
            st.write(f"**{desc}**")
            st.caption(f"Predicted sentiment: `{predicted}`")

        with c2:
            if st.button("👍 Correct", key=f"ok_{tx_id}"):
                save_feedback(user_id, tx_id, predicted, predicted)
                st.success("Feedback saved 👍")
                st.rerun()

        with c3:
            if st.button("👎 Wrong", key=f"bad_{tx_id}"):
                st.session_state[f"show_label_{tx_id}"] = True

        # If user clicked wrong: show selector + submit
        if st.session_state.get(f"show_label_{tx_id}", False):
            correct_label = st.selectbox(
                f"Correct label for transaction {tx_id}",
                ["Positive", "Neutral", "Negative"],
                key=f"label_{tx_id}",
            )
            if st.button("Submit", key=f"submit_{tx_id}"):
                save_feedback(user_id, tx_id, predicted, correct_label)
                st.success("Correct label saved ✅")
                st.session_state[f"show_label_{tx_id}"] = False
                st.rerun()

    # =========================
    # SENTIMENT ANALYSIS (dashboard section)
    # =========================
    st.markdown("## 🧠 Money Mood (Sentiment Analysis)")
    st.caption("Sentiment is calculated from transaction descriptions for the selected period.")

    # If sentiment is already stored, use it; otherwise compute it
    if df["sentiment_score"].notna().any():
        # Use stored values where possible
        scored_df = df.copy()
        # Fill missing scores on the fly
        for i, r in scored_df[scored_df["sentiment_score"].isna()].iterrows():
            comp = analyzer.polarity_scores(str(r["description"]))["compound"]
            scored_df.at[i, "sentiment_score"] = comp
            scored_df.at[i, "sentiment_label"] = _sentiment_label(comp)

        scored_df.rename(
            columns={
                "date": "Date",
                "description": "Description",
                "amount": "Amount",
                "sentiment_label": "Sentiment",
                "sentiment_score": "Score",
            },
            inplace=True,
        )
    else:
        # Compute everything if nothing stored
        rows = []
        for _, r in df.iterrows():
            comp = analyzer.polarity_scores(str(r["description"]))["compound"]
            rows.append(
                {
                    "Date": r["date"],
                    "Description": r["description"],
                    "Amount": r["amount"],
                    "Sentiment": _sentiment_label(comp),
                    "Score": round(comp, 3),
                }
            )
        scored_df = pd.DataFrame(rows)

    avg_compound = float(scored_df["Score"].mean()) if not scored_df.empty else 0.0
    emoji, mood_label = _mood_from_score(avg_compound)
    mood_meter = (avg_compound + 1) / 2

    pos = int((scored_df["Sentiment"] == "Positive").sum())
    neu = int((scored_df["Sentiment"] == "Neutral").sum())
    neg = int((scored_df["Sentiment"] == "Negative").sum())

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Mood Score", f"{avg_compound:.2f}")
    k2.metric("Positive", str(pos))
    k3.metric("Neutral", str(neu))
    k4.metric("Negative", str(neg))

    st.markdown(f"### {emoji} Overall mood: **{mood_label}**")
    st.progress(mood_meter)

    left, right = st.columns([1.2, 1])

    with left:
        st.subheader("Sentiment Breakdown")
        sentiment_data = {
            "Sentiment": ["Positive", "Neutral", "Negative"],
            "Count": [pos, neu, neg]
        }

        sent_df = pd.DataFrame(sentiment_data)

        fig = px.pie(
            sent_df,
            names="Sentiment",
            values="Count",
            hole=0.4,
            title="Sentiment Breakdown"
        )

        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Highlights")
        worst = scored_df.sort_values("Score").head(2)
        best = scored_df.sort_values("Score", ascending=False).head(2)

        st.markdown("**Most negative:**")
        for _, row in worst.iterrows():
            st.write(f"• {row['Description']} ({row['Score']:.2f})")

        st.markdown("**Most positive:**")
        for _, row in best.iterrows():
            st.write(f"• {row['Description']} ({row['Score']:.2f})")

    with st.expander("Show sentiment per transaction"):
        scored_df_display = scored_df.copy()
        scored_df_display["Amount"] = scored_df_display["Amount"].map(lambda x: f"${x:,.2f}")
        st.dataframe(scored_df_display[["Date", "Description", "Amount", "Sentiment", "Score"]],
                     use_container_width=True, height=300)