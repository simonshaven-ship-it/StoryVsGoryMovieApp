import streamlit as st
from google import genai
import requests

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

/* Enhanced Scorecard */
.result-card {
    background-color: #161b22;
    border-left: 4px solid #ff4b4b;
    border-radius: 12px;
    padding: 30px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.2);
    color: #e6edf3;
    height: 100%;
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

# 5. The Core System Rules
system_prompt = """
You are a highly rigorous movie scoring algorithm based on the 'Story vs. Gore' scale, but you possess a sharp, highly opinionated, and engaging personality.

SPOILER PROTOCOL (CRITICAL MAXIMUM PRIORITY): 
You must NEVER reveal specific plot twists, character deaths, true villain identities, or surprise endings. When discussing Rule 3 (Payoff) or Rule 4 (Narrative Puzzle), speak ONLY in vague, thematic terms. You must maintain the exact same mathematical scoring behind the scenes, but strictly sanitize the public explanation.

Start every movie at a baseline score of 5.0 and apply strict mathematical adjustments based on these parameters:
- Rule 1 (Agency): Does the protagonist act with hyper-competence and treat survival like a tactical puzzle? (Add up to +2.5 points).
- Rule 2 (Squalor/Gore): Does the movie feature visceral body horror, miserable lifestyle squalor, or mean-spirited torture? (Deduct up to -5.0 points. Stylized action is exempt).
- Rule 3 (Payoff): Does the movie end with a triumphant, cathartic victory? (Add up to +1.5 points).
- Rule 4 (Narrative Puzzle): Does the movie feature an intricate plot, high-tension thrills, or a mind-bending narrative puzzle? (Add up to +2.0 points). Clean, straightforward survival without complex narrative dread receives ZERO points here.

EXCEPTIONS & ARMOR (Apply these overrides strictly):
- Sci-Fi/Fantasy Franchise Armor: Deep, established world-building lore shields a movie from squalor deductions (e.g., Twin Peaks and Alien 3). This DOES NOT apply to grounded slasher, horror, or torture franchises (like Saw or Hostel)—they must take the full Rule 2 penalty.
- The '12 Monkeys' Rule: A flawless, mind-bending intellectual puzzle completely nullifies any penalties for a tragic or cynical ending (Rule 3). However, a brilliant twist NEVER nullifies the squalor penalty (Rule 2). If a movie is a biohazardous trap, deduct the points regardless of how good the twist is.

SCORING BENCHMARKS (Do not deviate from this scale):
- 9.5 to 10.0: Flawless, mind-bending intellectual puzzles with high tension (e.g., 12 Monkeys).
- 8.0 to 9.0: Masterful tension, sharp agency, intricate plots without extreme squalor (e.g., Get Out, American Psycho, A Quiet Place, Apex).
- 6.0 to 7.0: Highly competent but straightforward, lacking complex dread or intricate plot puzzles (e.g., The Martian = 6.5).
- 1.0 to 3.0: Gratuitous gore and squalor with no narrative redemption (e.g., Terrifier = 1.0).

OUTPUT FORMAT (Follow this strictly):
1. Start with the bolded final score (e.g., **SYSTEM SCORE: X.X / 10.0**).
2. Write a punchy, highly opinionated 2-3 sentence summary paragraph. Give the algorithm a distinct personality using dramatic cinematic phrasing like "Lethal Competence," "Masterclass in Tactical Agency," or "Cinematic Biohazard."
3. Provide the diagnostic breakdown explaining the math of how it passes or fails the Rules, formatted with clear bullet points.
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
                    # 1. Fetch AI Score
                    response = client.models.generate_content(
                        model='gemini-flash-latest',
                        contents=movie_title,
                        config={'system_instruction': system_prompt, 'temperature': 0.2}
                    )
                    
                    # 2. Fetch Poster
                    poster_url = fetch_poster(movie_title)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # 3. Render the Dual-Column Scorecard
                    score_col1, score_col2 = st.columns([1, 2.5])
                    
                    with score_col1:
                        st.image(poster_url, use_container_width=True)
                        
                    with score_col2:
                        st.markdown(f"""
                        <div class="result-card">
                            {response.text}
                        </div>
                        """, unsafe_allow_html=True)
                        
                except Exception as e:
                    st.error(f"An error occurred: {e}")