import streamlit as st
import yt_dlp
import numpy as np
import pandas as pd
import plotly.express as px
import openai
import re
from bs4 import BeautifulSoup
import requests
import googleapiclient.discovery

# YouTube API Key (Replace with your own)
YOUTUBE_API_KEY = "a453e8a05dcdc9f0e0b06674cf51f196a91f0112"

# Function to extract video ID from URL
def extract_video_id(url):
    """Extracts the Video ID from a YouTube URL."""
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, url)
    return match.group(1) if match else None

# Function to fetch video data from YouTube API
def get_video_data(video_id):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    request = youtube.videos().list(
        part="statistics,contentDetails",
        id=video_id
    )
    response = request.execute()

    if "items" in response and len(response["items"]) > 0:
        item = response["items"][0]
        stats = item.get("statistics", {})
        return {
            "views": stats.get("viewCount", "N/A"),
            "likes": stats.get("likeCount", "N/A"),
            "duration": item["contentDetails"]["duration"]
        }
    return None

# Function to extract retention data using Web Scraping
def extract_retention_data(video_url):
    video_id = extract_video_id(video_url)
    api_data = get_video_data(video_id)

    views = api_data["views"] if api_data else "N/A"
    likes = api_data["likes"] if api_data else "N/A"

    try:
        response = requests.get(video_url)
        soup = BeautifulSoup(response.text, "html.parser")
        script_tags = soup.find_all("script")

        for script in script_tags:
            if "var ytInitialData" in script.text:
                raw_data = script.text
                numbers = re.findall(r"\d+\.\d+", raw_data)
                retention_data = np.array(numbers[-50:], dtype=np.float32)

                timestamps = np.linspace(0, len(retention_data) * 5, len(retention_data))
                df = pd.DataFrame({"timestamp": timestamps, "retention_percentage": retention_data})

                return df, views, likes
    except Exception as e:
        st.error(f"Error fetching retention data: {str(e)}")
        return None, views, likes

# Streamlit UI
st.title("🎬 Retention Score Analyzer (YouTube Link Version)")
st.write("Paste YouTube video links to analyze and compare retention data automatically.")

# Sidebar Inputs
st.sidebar.header("Enter YouTube Video Links")
video_url1 = st.sidebar.text_input("📌 Enter Your Video URL")
video_url2 = st.sidebar.text_input("🎯 Enter Competitor's Video URL (Optional)")

# Single Video Analysis
if video_url1 and not video_url2:
    st.write("## 📊 Your Video Analysis")
    df1, views1, likes1 = extract_retention_data(video_url1)

    if df1 is not None:
        avg_retention = np.mean(df1["retention_percentage"])
        early_dropoff = df1[df1["timestamp"] < 30]["retention_percentage"].mean()
        final_retention = df1[df1["timestamp"] > (df1["timestamp"].max() * 0.9)]["retention_percentage"].mean()

        st.metric("📊 Average Retention Score", f"{avg_retention:.2f}%")
        st.metric("⚠️ Early Drop-Off Rate", f"{early_dropoff:.2f}%")
        st.metric("🎬 Final Retention Strength", f"{final_retention:.2f}%")
        st.metric("👀 Views", views1)
        st.metric("👍 Likes", likes1)

        # Retention Graph
        fig = px.line(df1, x="timestamp", y="retention_percentage", title="Your Video's Audience Retention")
        st.plotly_chart(fig)

# Compare Two Videos
elif video_url1 and video_url2:
    st.write("## 🔍 Comparing Your Video vs. Competitor's Video")

    df1, views1, likes1 = extract_retention_data(video_url1)
    df2, views2, likes2 = extract_retention_data(video_url2)

    if df1 is not None and df2 is not None:
        avg_retention_1 = np.mean(df1["retention_percentage"])
        avg_retention_2 = np.mean(df2["retention_percentage"])

        col1, col2 = st.columns(2)
        with col1:
            st.metric("📊 Your Video Retention Score", f"{avg_retention_1:.2f}%")
            st.metric("👀 Views", views1)
            st.metric("👍 Likes", likes1)
        with col2:
            st.metric("📊 Competitor's Retention Score", f"{avg_retention_2:.2f}%")
            st.metric("👀 Views", views2)
            st.metric("👍 Likes", likes2)

        # Retention Graph Comparison
        fig = px.line(title="🔍 Retention Comparison: Your Video vs. Competitor")
        fig.add_scatter(x=df1["timestamp"], y=df1["retention_percentage"], mode='lines', name="Your Video", line=dict(color="blue"))
        fig.add_scatter(x=df2["timestamp"], y=df2["retention_percentage"], mode='lines', name="Competitor's Video", line=dict(color="red"))
        st.plotly_chart(fig)

        # AI Suggestions
        prompt = f"""
        Compare retention data for two videos:
        - Your Video: {avg_retention_1:.2f}%
        - Competitor's Video: {avg_retention_2:.2f}%

        Provide an in-depth analysis of what the competitor is doing better and what improvements should be made to increase retention in your video.
        """
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are a YouTube retention expert."},
                      {"role": "user", "content": prompt}]
        )

        st.write("### 🤖 AI-Powered Retention Improvement Suggestions")
        st.write(response["choices"][0]["message"]["content"])
