import streamlit as st
from google import genai
import requests
import json

# 1. Setup the UI Page
st.set_page_config(page_title="Story vs. Gore Predictor", page_icon="🎬", layout="wide")

# 2. Injecting Custom CSS
st.markdown("""
<style>
/* Dark cinematic background and typography */
.stApp {
    background-color: #0d1117;
    color: #c9d1d9;
    font-family: 'Inter', sans-serif;
}

h1, h2, h3 {
    color: #ffffff !important;
    font-weight: 800 !important;
    letter-spacing: -1px;
}

.stTextInput > div > div > input {
    background-color: #161b22;
    color: #ffffff;
    border-radius: 8px;
    border: 1px solid #30363d;
    padding: 12px;
}

.stButton > button {
    background: linear-gradient(90deg, #ff4b4b 0%, #ff8f00 100%);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-weight: 600;
    transition: all 0.3s ease;
    width: 100%;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(255, 75, 75, 0.4);
    color: white;
}

/* Score Pill Badges */
.score-badge-red {
    background: rgba(248, 81, 73, 0.15);
    color: #f85149;
    border: 1px solid #f85149;
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 1.4rem;
    font-weight: 800;
    display: inline-block;
    margin-bottom: 12px;
}

.score-badge-orange {
    background: rgba(210, 153, 34, 0.15);
    color: #d29922;
    border: 1px solid #d29922;
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 1.4rem;
    font-weight: 800;
    display: inline-block;
    margin-bottom: 12px;
}

.score-badge-green {
    background: rgba(46, 160, 67, 0.15);
    color: #3fb950;
    border: 1px solid #3fb950;
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 1.4rem;
    font-weight: 800;
    display: inline-block;
    margin-bottom: 12px;
}

/* Summary Verdict Card */
.verdict-card {
    background-color: #161b22;
    border-radius: 12px;
    padding: 24px;
    border: 1px solid #30363d;
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    margin-bottom: 20px;
}

/* Diagnostic Breakdown Card */
.breakdown-card {
    background-color: #161b22;
    border-left: 4px solid #ff4b4b;
    border-radius: 8px;
    padding: 24px;
    border-top: 1px solid #30363d;
    border-right: 1px solid #30363d;
    border-bottom: 1px solid #30363d;
}

.breakdown-card ul {
    margin-bottom: 0;
    padding-left: 20px;
}

.breakdown-card li {
    margin-bottom: 12px;
    line-height: 1.5;
}
</style>
""", unsafe_allow_html=True)

# 3. Securely load API Keys
api_key = st.secrets["GEMINI_API_KEY"]
omdb_key = st.secrets["OMDB_API_KEY"]
client = genai.Client(api_key=api_key)

# 4. Helper Function: Fetch Poster
def fetch_poster(title):
    url = f"http://www.omdbapi.com/?t={title}&apikey={omdb_key}"
    try:
        response = requests.get(url).json()
        if response.get("Response") == "True" and response.get("Poster") != "N/A":
            return response.get("Poster")
    except:
        pass
    return "https://via.placeholder.com/300x450.png?text=No+Poster+Found"

# 5. Core System Prompt (JSON Structured Output)
system_prompt = """
You are a highly rigorous movie scoring algorithm based on the 'Story vs. Gore' scale, possessing a sharp, highly opinionated, and engaging personality.

SPOILER PROTOCOL (CRITICAL MAXIMUM PRIORITY): 
You must NEVER reveal specific plot twists, character deaths, true villain identities, or surprise endings. Speak ONLY in vague, thematic terms.

SCORING PARAMETERS:
Start every movie at a baseline score of 5.0 and apply strict mathematical adjustments:
- Rule 1 (Agency): Does protagonist act with hyper-competence and treat survival like a tactical puzzle? (Add up to +2.5).
- Rule 2 (Squalor/Gore): Visceral body horror, miserable lifestyle squalor, or torture? (Deduct up to -5.0. Stylized action exempt).
- Rule 3 (Payoff): Triumphant, cathartic victory? (Add up to +1.5).
- Rule 4 (Narrative Puzzle): Intricate plot, high-tension thrills, or mind-bending puzzle? (Add up to +2.0).

EXCEPTIONS:
- Sci-Fi/Fantasy Franchise Armor: Deep world-building lore shields a movie from squalor deductions (e.g., Twin Peaks, Alien 3). DOES NOT apply to grounded slasher/horror (Saw, Hostel).
- The '12 Monkeys' Rule: Flawless intellectual puzzle nullifies penalties for tragic ending (Rule 3), but NEVER nullifies squalor penalties (Rule 2).

OUTPUT REQUIREMENT:
Return ONLY a valid JSON object matching this schema exactly:
{
  "score": 4.5,
  "summary": "Punchy, opinionated 2-3 sentence summary paragraph with cinematic phrasing (e.g., 'Lethal Competence', 'Cinematic Biohazard').",
  "breakdown": [
    "**Baseline Score**: 5.0",
    "**Rule 1 (Agency)**: +1.0 Points. Explanation...",
    "**Rule 2 (Squalor/Gore)**: -3.5 Points. Explanation...",
    "**Rule 3 (Payoff)**: +0.0 Points. Explanation...",
    "**Rule 4 (Narrative Puzzle)**: +2.0 Points. Explanation..."
  ]
}
"""

# 6. UI Layout
st.markdown("<h1 style='text-align: center; margin-top: 2rem;'>🎬 The Movie Enjoyment Predictor</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #8b949e; font-size: 1.2rem; margin-bottom: 40px;'>Based on the <b>Story vs. Gore</b> scale. Does your movie survive the algorithm?</p>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    movie_title = st.text_input("Search for a film...", placeholder="e.g., The Matrix, 12 Monkeys", label_visibility="collapsed")
    analyze_btn = st.button("Analyze Movie")

    if analyze_btn:
        if not movie_title:
            st.warning("Please enter a movie title.")
        else:
            with st.spinner(f"Running {movie_title} through the board..."):
                try:
                    # Request JSON format from Gemini
                    response = client.models.generate_content(
                        model='gemini-flash-latest',
                        contents=movie_title,
                        config={
                            'system_instruction': system_prompt,
                            'temperature': 0.2,
                            'response_mime_type': 'application/json'
                        }
                    )
                    
                    data = json.loads(response.text)
                    score_val = float(data.get("score", 5.0))
                    summary_text = data.get("summary", "")
                    breakdown_list = data.get("breakdown", [])
                    
                    poster_url = fetch_poster(movie_title)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # Determine Badge Color
                    if score_val >= 8.0:
                        badge_class = "score-badge-green"
                    elif score_val >= 5.0:
                        badge_class = "score-badge-orange"
                    else:
                        badge_class = "score-badge-red"
                        
                    # 3. Render Dual-Column Layout
                    score_col1, score_col2 = st.columns([1, 2.5])
                    
                    with score_col1:
                        st.image(poster_url, use_container_width=True)
                        
                    with score_col2:
                        # Top Panel: Score Badge & Personality Verdict
                        st.markdown(f"""
                        <div class="verdict-card">
                            <div class="{badge_class}">SYSTEM SCORE: {score_val} / 10.0</div>
                            <p style="font-size: 1.05rem; line-height: 1.6; margin-bottom: 0; color: #e6edf3;">{summary_text}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Bottom Panel: Diagnostic Breakdown
                        breakdown_html = "".join([f"<li>{item}</li>" for item in breakdown_list])
                        st.markdown(f"""
                        <div class="breakdown-card">
                            <h4 style="margin-top: 0; margin-bottom: 16px; color: #ffffff;">🔍 Diagnostic Breakdown</h4>
                            <ul>
                                {breakdown_html}
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)
                        
                except Exception as e:
                    st.error(f"An error occurred: {e}")