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
YOUTUBE_API_KEY = "AIzaSyCID6TRLIk4krNLu5BpUkDXpTfhbQaZScs"

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
st.title("📊 YouTube Retention Score Analyzer")
st.write("🔍 Paste a YouTube link below to analyze audience engagement and get **easy-to-understand insights**.")

# Sidebar Inputs
st.sidebar.header("Enter YouTube Video Link")
video_url1 = st.sidebar.text_input("📌 Enter Your Video URL")

if video_url1:
    df1, views1, likes1 = extract_retention_data(video_url1)

    if df1 is not None:
        avg_retention = np.mean(df1["retention_percentage"])
        early_dropoff = df1[df1["timestamp"] < 30]["retention_percentage"].mean()
        final_retention = df1[df1["timestamp"] > (df1["timestamp"].max() * 0.9)]["retention_percentage"].mean()

        # **💡 Beginner-Friendly Explanations**
        st.subheader("📊 Your Video Analysis (With Easy Explanation)")

        # **📌 Retention Score**
        st.write(f"**📈 Average Retention Score: {avg_retention:.2f}%**")
        st.write("➡️ This tells how many viewers, on average, **stay watching your video** until the end. Higher is better!")

        # **⚠️ Early Drop-Off Rate**
        st.write(f"**⚠️ Early Drop-Off Rate: {early_dropoff:.2f}%**")
        if early_dropoff > 40:
            st.warning("🚨 Many viewers **leave within the first 30 seconds**! Consider making your intro more engaging.")
        elif early_dropoff > 20:
            st.info("🔹 Some viewers **drop off early**. You can improve this with a strong hook!")
        else:
            st.success("✅ Your intro is **keeping viewers engaged**. Keep it up!")

        # **🎬 Final Retention Strength**
        st.write(f"**📌 Final Retention Strength: {final_retention:.2f}%**")
        if final_retention < 10:
            st.warning("🚨 Most viewers **don’t finish your video**. Try making your content more engaging throughout.")
        elif final_retention < 30:
            st.info("🔹 Some people watch till the end, but there’s room for improvement.")
        else:
            st.success("✅ Great! Many viewers are **watching until the end**.")

        # **👀 Views & 👍 Likes**
        st.write(f"👀 **Total Views:** {views1}")
        st.write(f"👍 **Total Likes:** {likes1}")

        # **📊 Retention Graph**
        st.subheader("📊 Your Video's Audience Retention")
        fig = px.line(df1, x="timestamp", y="retention_percentage", title="Viewer Retention Over Time")
        st.plotly_chart(fig)

        # **💡 AI-Powered Suggestions**
        st.subheader("🤖 Smart AI Suggestions to Improve Retention")
        prompt = f"""
        My video has:
        - **Average Retention Score**: {avg_retention:.2f}%
        - **Early Drop-Off**: {early_dropoff:.2f}%
        - **Final Retention**: {final_retention:.2f}%
        - **Total Views**: {views1}
        - **Total Likes**: {likes1}

        Based on these numbers, **what are 3 simple strategies I can use to improve retention and keep viewers engaged longer?**
        """

        client = openai.OpenAI(api_key="YOUR_OPENAI_API_KEY")  # Add your API key here

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "system", "content": "You are an expert YouTube consultant."},
              {"role": "user", "content": prompt}]
)


        st.write("### 📌 AI Suggestions to Improve")
        st.write(response["choices"][0]["message"]["content"])
