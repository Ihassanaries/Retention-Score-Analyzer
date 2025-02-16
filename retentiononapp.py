import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import openai

# App Title
st.title("🎬 Retention Score Analyzer")
st.write("Analyze audience retention for one video or compare two videos.")

# Sidebar Upload Options
st.sidebar.header("Upload Retention Data")
uploaded_file1 = st.sidebar.file_uploader("Upload Retention Data (CSV) for Your Video", type=["csv"])
uploaded_file2 = st.sidebar.file_uploader("Upload Retention Data (CSV) for Competitor's Video (Optional)", type=["csv"])

# Function to Analyze Retention for One Video
def analyze_single_video(df, video_label="Your Video"):
    # Ensure required columns exist
    required_columns = ["timestamp", "retention_percentage"]
    if not all(col in df.columns for col in required_columns):
        st.error(f"{video_label} CSV must contain columns: timestamp, retention_percentage")
        return

    st.success(f"✅ Data uploaded successfully for {video_label}")

    # Calculate Retention Metrics
    avg_retention = np.mean(df["retention_percentage"])
    early_dropoff = df[df["timestamp"] < 30]["retention_percentage"].mean()
    final_retention = df[df["timestamp"] > (df["timestamp"].max() * 0.9)]["retention_percentage"].mean()

    st.metric(f"📊 {video_label} Retention Score", f"{avg_retention:.2f}%")
    st.metric(f"⚠️ {video_label} Early Drop-Off Rate", f"{early_dropoff:.2f}%")
    st.metric(f"🎬 {video_label} Final Retention Strength", f"{final_retention:.2f}%")

    # Retention Graph
    fig = px.line(df, x="timestamp", y="retention_percentage", title=f"🔍 {video_label} Audience Retention Over Time")
    st.plotly_chart(fig)

    # Drop-Off Detection
    df["dropoff"] = df["retention_percentage"].diff().fillna(0)
    dropoff_points = df[df["dropoff"] < -10]

    if not dropoff_points.empty:
        st.write(f"### ⚠️ High Drop-Off Points Detected in {video_label}")
        st.write(dropoff_points)
    else:
        st.success(f"No major drop-off points detected in {video_label}")

    # Top Retention Points
    top_retention = df.nlargest(3, "retention_percentage")
    st.write(f"### 🔥 Top 3 High-Retention Moments in {video_label}")
    st.write(top_retention)

    # Chapter-Based Retention Analysis
    df["chapter"] = pd.cut(df["timestamp"], bins=5, labels=["Intro", "Early", "Mid", "Late", "Ending"])
    chapter_avg = df.groupby("chapter")["retention_percentage"].mean()

    st.write(f"### 📌 {video_label} Chapter-Based Retention Performance")
    st.bar_chart(chapter_avg)

    # AI-Powered Fix Suggestions
    prompt = f"""
    Analyze the retention data for {video_label}:
    - Average Retention Score: {avg_retention:.2f}%
    - Early Drop-Off: {early_dropoff:.2f}%
    - Final Retention: {final_retention:.2f}%
    - High Drop-Off Points: {dropoff_points.to_dict(orient="records")}
    - High Retention Moments: {top_retention.to_dict(orient="records")}
    - Chapter-based retention: {chapter_avg.to_dict()}

    Provide improvement strategies such as better hooks, pacing adjustments, pattern interrupters, and content tweaks.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are a YouTube retention expert."},
                  {"role": "user", "content": prompt}]
    )

    st.write(f"### 🤖 AI Suggestions for {video_label}")
    st.write(response["choices"][0]["message"]["content"])

# **Single Video Mode** (If only one file is uploaded)
if uploaded_file1 and not uploaded_file2:
    df1 = pd.read_csv(uploaded_file1)
    analyze_single_video(df1)

# **Comparison Mode** (If two files are uploaded)
elif uploaded_file1 and uploaded_file2:
    df1 = pd.read_csv(uploaded_file1)
    df2 = pd.read_csv(uploaded_file2)

    st.write("## **Comparing Two Videos: Yours vs. Competitor**")

    # Analyze both videos separately
    analyze_single_video(df1, "Your Video")
    analyze_single_video(df2, "Competitor's Video")

    # **Retention Comparison Graph**
    fig = px.line(title="🔍 Retention Comparison: Your Video vs. Competitor")
    fig.add_scatter(x=df1["timestamp"], y=df1["retention_percentage"], mode='lines', name="Your Video", line=dict(color="blue"))
    fig.add_scatter(x=df2["timestamp"], y=df2["retention_percentage"], mode='lines', name="Competitor's Video", line=dict(color="red"))
    st.plotly_chart(fig)

    # Retention Metrics Comparison
    avg_retention_1 = np.mean(df1["retention_percentage"])
    avg_retention_2 = np.mean(df2["retention_percentage"])

    col1, col2 = st.columns(2)
    with col1:
        st.metric("📊 Your Video Retention Score", f"{avg_retention_1:.2f}%")
    with col2:
        st.metric("📊 Competitor's Retention Score", f"{avg_retention_2:.2f}%")

    # Drop-Off & High-Retention Moments Comparison
    dropoff_1 = df1[df1["dropoff"] < -10]
    dropoff_2 = df2[df2["dropoff"] < -10]

    st.write("### ⚠️ High Drop-Off Points (Your Video)")
    st.write(dropoff_1)

    st.write("### ⚠️ High Drop-Off Points (Competitor's Video)")
    st.write(dropoff_2)

    top_retention_1 = df1.nlargest(3, "retention_percentage")
    top_retention_2 = df2.nlargest(3, "retention_percentage")

    st.write("### 🔥 Top 3 High-Retention Moments (Your Video)")
    st.write(top_retention_1)

    st.write("### 🔥 Top 3 High-Retention Moments (Competitor's Video)")
    st.write(top_retention_2)

    # AI-Powered Strategy Suggestion for Video Comparison
    prompt = f"""
    Compare the retention data of these two videos:
    - Your Video:
      - Average Retention Score: {avg_retention_1:.2f}%
      - High Drop-Off Points: {dropoff_1.to_dict(orient="records")}
    - Competitor's Video:
      - Average Retention Score: {avg_retention_2:.2f}%
      - High Drop-Off Points: {dropoff_2.to_dict(orient="records")}

    Provide an in-depth analysis of what the competitor is doing better and what improvements should be made to increase retention in your video.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are a YouTube retention expert."},
                  {"role": "user", "content": prompt}]
    )

    st.write("### 🤖 AI Suggestions for Competitive Advantage")
    st.write(response["choices"][0]["message"]["content"])
