import streamlit as st
from google import genai
import requests
import json

# 1. Setup the UI Page
st.set_page_config(page_title="Story vs. Gore Predictor", page_icon="🎬", layout="wide")

# 2. Injecting Custom CSS
st.markdown("""
<style>
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
    padding: 12px 24px;
    font-weight: 600;
    transition: all 0.3s ease;
    width: 100%;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(255, 75, 75, 0.4);
    color: white;
}

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

.verdict-card {
    background-color: #161b22;
    border-radius: 12px;
    padding: 24px;
    border: 1px solid #30363d;
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    margin-bottom: 20px;
}

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

.streaming-box {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 15px;
    margin-top: 15px;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# 3. Securely load API Keys
api_key = st.secrets["GEMINI_API_KEY"]
omdb_key = st.secrets["OMDB_API_KEY"]
client = genai.Client(api_key=api_key)

# 4. Helper Function: Fetch Movie Data & Poster from OMDb
def fetch_movie_data(title):
    url = f"http://www.omdbapi.com/?t={title}&apikey={omdb_key}"
    try:
        response = requests.get(url).json()
        if response.get("Response") == "True":
            poster = response.get("Poster") if response.get("Poster") != "N/A" else "https://via.placeholder.com/300x450.png?text=No+Poster+Found"
            rated = response.get("Rated", "N/A")
            genre = response.get("Genre", "N/A")
            return poster, rated, genre
    except:
        pass
    return "https://via.placeholder.com/300x450.png?text=No+Poster+Found", "N/A", "N/A"

# 5. UI Layout & Sidebar Controls (Feature 2: Sliders)
st.markdown("<h1 style='text-align: center; margin-top: 1rem;'>🎬 The Movie Enjoyment Predictor</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #8b949e; font-size: 1.2rem; margin-bottom: 30px;'>Calibrate the rules and test your film library against the board.</p>", unsafe_allow_html=True)

with st.sidebar:
    st.header("🎛️ Algorithm Calibration")
    st.write("Customize how the engine weights its rules for this session.")
    
    gore_tolerance = st.slider("Gore & Squalor Penalty Weight", min_value=0.0, max_value=2.0, value=1.0, step=0.1, 
                               help="Higher values make the algorithm mercilessly punish gritty horror.")
    puzzle_weight = st.slider("Puzzle & Twist Bonus Weight", min_value=0.5, max_value=2.0, value=1.0, step=0.1,
                              help="Higher values heavily reward intricate narrative structures.")
    
    st.markdown("---")
    st.markdown("**About:** Built on Gemini Flash with real-time OMDb metadata integration.")

# Main Input Section wrapped in an st.form (Quota Protection)
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    with st.form("movie_form"):
        movie_title = st.text_input("Search for a film...", placeholder="e.g., The Matrix, 12 Monkeys", label_visibility="collapsed")
        analyze_btn = st.form_submit_button("Run Algorithm")

    if analyze_btn:
        if not movie_title:
            st.warning("Please enter a movie title.")
        else:
            with st.spinner(f"Running {movie_title} through the board (Sliders: Gore x{gore_tolerance}, Puzzle x{puzzle_weight})..."):
                try:
                    # Dynamic System Prompt injecting user slider weights
                    system_prompt = f"""
                    You are a highly rigorous movie scoring algorithm based on the 'Story vs. Gore' scale, possessing a sharp, opinionated personality.
                    
                    USER CALIBRATION MODIFIERS:
                    - Squalor Penalty Multiplier: {gore_tolerance} (Scale the Rule 2 deductions by this factor).
                    - Puzzle Bonus Multiplier: {puzzle_weight} (Scale the Rule 4 bonuses by this factor).

                    SPOILER PROTOCOL (CRITICAL MAXIMUM PRIORITY): 
                    Never reveal specific plot twists, character deaths, or endings. Speak ONLY in vague, thematic terms.

                    SCORING PARAMETERS:
                    Start at 5.0 baseline and adjust:
                    - Rule 1 (Agency): Tactical survival (Add up to +2.5).
                    - Rule 2 (Squalor/Gore): Body horror/miserable grime (Deduct up to -5.0 * {gore_tolerance}).
                    - Rule 3 (Payoff): Triumphant victory (Add up to +1.5).
                    - Rule 4 (Narrative Puzzle): Intricate plot/puzzle (Add up to +2.0 * {puzzle_weight}).

                    EXCEPTIONS:
                    - Sci-Fi Franchise Armor: Twin Peaks, Alien 3 protected from squalor.
                    - '12 Monkeys' Rule: Intellectual puzzle nullifies tragic ending penalty (Rule 3), but NEVER squalor (Rule 2).

                    Return ONLY valid JSON matching this schema:
                    {{
                      "score": 4.5,
                      "summary": "Opinionated 2-3 sentence summary with cinematic phrasing.",
                      "breakdown": [
                        "**Baseline Score**: 5.0",
                        "**Rule 1 (Agency)**: Explanation...",
                        "**Rule 2 (Squalor/Gore)**: Explanation...",
                        "**Rule 3 (Payoff)**: Explanation...",
                        "**Rule 4 (Narrative Puzzle)**: Explanation..."
                      ]
                    }}
                    """

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
                    
                    poster_url, rated, genre = fetch_movie_data(movie_title)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    if score_val >= 8.0:
                        badge_class = "score-badge-green"
                    elif score_val >= 5.0:
                        badge_class = "score-badge-orange"
                    else:
                        badge_class = "score-badge-red"
                        
                    # Render Dual-Column Layout
                    score_col1, score_col2 = st.columns([1, 2.5])
                    
                    with score_col1:
                        st.image(poster_url, use_container_width=True)
                        
                        # Feature 1: Streaming & Metadata Links
                        search_query = movie_title.replace(" ", "+")
                        st.markdown(f"""
                        <div class="streaming-box">
                            <p style="font-size: 0.85rem; color: #8b949e; margin-bottom: 8px;"><b>Rated:</b> {rated} | <b>Genre:</b> {genre}</p>
                            <a href="https://www.justwatch.com/us/search?q={search_query}" target="_blank" style="color: #58a6ff; text-decoration: none; font-size: 0.9rem; font-weight: 600;">🍿 Find Where to Watch</a>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with score_col2:
                        st.markdown(f"""
                        <div class="verdict-card">
                            <div class="{badge_class}">SYSTEM SCORE: {score_val} / 10.0</div>
                            <p style="font-size: 1.05rem; line-height: 1.6; margin-bottom: 0; color: #e6edf3;">{summary_text}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
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