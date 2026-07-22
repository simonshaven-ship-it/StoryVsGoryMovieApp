import streamlit as st
import streamlit.components.v1 as components
from google import genai
import requests
import json
import urllib.parse
import html
import base64
import re

# 1. Setup the UI Page
st.set_page_config(page_title="Story Vs Gory", page_icon="🎬", layout="wide")

# 2. Injecting Custom CSS
st.markdown("""
<style>
.stApp {
    background-color: #0d1117;
    color: #c9d1d9;
    font-family: 'Inter', sans-serif;
}
[data-testid="stSidebar"] {
    background-color: #161b22;
    border-right: 1px solid #30363d;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] span {
    color: #ffffff !important;
}
[data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
    color: #8b949e !important;
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
.stButton > button, div.stFormSubmitButton > button {
    background: linear-gradient(90deg, #ff4b4b 0%, #ff8f00 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 12px 24px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    width: 100% !important;
}
.stButton > button:hover, div.stFormSubmitButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(255, 75, 75, 0.4);
    color: white !important;
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

# 80s Slasher Fallback Background Generator
def get_slasher_card_background():
    svg_code = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 650" width="400" height="650">
      <defs>
        <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#120508"/>
          <stop offset="50%" stop-color="#1a0206"/>
          <stop offset="100%" stop-color="#08080c"/>
        </linearGradient>
        <linearGradient id="blood" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="#ff4b4b"/>
          <stop offset="100%" stop-color="#600000"/>
        </linearGradient>
      </defs>
      <rect width="400" height="650" fill="url(#bg)"/>
      <path d="M0 480 L400 480 M0 515 L400 515 M0 550 L400 550 M0 585 L400 585 M0 620 L400 620" stroke="#ff4b4b" stroke-width="0.8" opacity="0.25"/>
      <path d="M200 480 L30 650 M200 480 L100 650 M200 480 L200 650 M200 480 L300 650 M200 480 L370 650" stroke="#ff4b4b" stroke-width="0.8" opacity="0.25"/>
      <path d="M30 20 L380 370" stroke="url(#blood)" stroke-width="6" stroke-linecap="round" opacity="0.2"/>
      <path d="M370 20 L20 370" stroke="url(#blood)" stroke-width="4" stroke-linecap="round" opacity="0.15"/>
      <circle cx="200" cy="150" r="120" fill="#ff4b4b" opacity="0.08" filter="blur(40px)"/>
      <circle cx="200" cy="450" r="100" fill="#ff8f00" opacity="0.05" filter="blur(40px)"/>
    </svg>"""
    b64 = base64.b64encode(svg_code.encode('utf-8')).decode('utf-8')
    return f"data:image/svg+xml;base64,{b64}"

# 4. Cached Helper Functions
@st.cache_data(ttl=86400, show_spinner=False)
def fetch_movie_data(title):
    url = f"https://www.omdbapi.com/?t={title}&apikey={omdb_key}"
    fallback = get_slasher_card_background()
    try:
        response = requests.get(url).json()
        if response.get("Response") == "True":
            poster_url = response.get("Poster")
            if not poster_url or poster_url == "N/A" or "http" not in poster_url:
                poster_url = fallback
                poster_b64 = fallback
            else:
                img_resp = requests.get(poster_url)
                if img_resp.status_code == 200:
                    b64_img = base64.b64encode(img_resp.content).decode('utf-8')
                    poster_b64 = f"data:image/jpeg;base64,{b64_img}"
                else:
                    poster_b64 = fallback
            
            rated = response.get("Rated", "N/A")
            genre = response.get("Genre", "N/A")
            return poster_url, poster_b64, rated, genre
    except:
        pass
    return fallback, fallback, "N/A", "N/A"

@st.cache_data(ttl=86400, show_spinner=False)
def cached_gemini_analysis(movie_title, gore_tolerance, puzzle_weight, pacing_weight):
    system_prompt = f"""
    You are an unhinged, ultra-witty film critic and ruthless scoring algorithm. Your style is packed with swagger, dark humor, outrageous roasts, and vivid cinematic metaphors (e.g., "grabs a chainsaw and digs a hole underneath them"). Make the user chuckle and wow them with your razor-sharp commentary.

    CRITICAL TASTE ALIGNMENT:
    You are analyzing films for a viewer who LOVES intricate plots, high-concept narrative puzzles (like 12 Monkeys, Get Out), hyper-competent tactical survival, and triumphant action. 
    They ABSOLUTELY HATE slow, miserable, stomach-turning torture porn, graphic biological cruelty, mean-spirited squalor, and bloated travelogues that drag on forever.

    USER CALIBRATION MODIFIERS:
    - Squalor Penalty Multiplier: {gore_tolerance} (Scale Rule 2 deductions by this factor).
    - Puzzle Bonus Multiplier: {puzzle_weight} (Scale Rule 4 bonuses by this factor).
    - Pacing Penalty Multiplier: {pacing_weight} (Scale Rule 5 deductions by this factor).

    SPOILER PROTOCOL: 
    Never reveal specific plot twists, character deaths, or endings. Speak ONLY in vague, thematic, outrageous terms.

    SCORING PARAMETERS (Start at 5.0 baseline):
    - Rule 1 (Agency): Tactical survival, hyper-competence, improvised blueprints (Add up to +2.5).
    - Rule 2 (Squalor/Gore): Body horror, miserable grime, biological cruelty. (Deduct up to -5.0 * {gore_tolerance}). 
    - Rule 3 (Payoff): Triumphant victory vs. miserable, soul-crushing trauma loops (Add up to +1.5).
    - Rule 4 (Narrative Puzzle): Intricate plot, high-concept narrative architecture (Add up to +2.0 * {puzzle_weight}).
    - Rule 5 (Pacing & Runtime Check): Deduct points (up to -2.0 * {pacing_weight}) for excessive runtime bloat, slow-burn wandering, or meandering travelogues that kill narrative momentum (e.g., epic fantasies heavy on scenic walking).

    EXCEPTIONS & BENCHMARKS (THE 'MERIT OVER FRANCHISE' PROTOCOL):
    - NO SEQUEL ARMOR (THE INDEPENDENT MERIT RULE): Judge every single film and sequel entirely on its own independent DNA. Never assume a sequel inherits the score or tone of its predecessor.
    - THE 'ALIENS' EVOLUTION (Action > Horror): If a film pivots from helpless horror into hyper-competent, tactical action, it earns massive Rule 1 and Rule 3 points. Kinetic adrenaline completely OVERRIDES Rule 2 squalor penalties.
    - THE 'SLOW SLASHER' TAX: If a movie is a slow-burn claustrophobic horror where the cast spends 90% of the runtime helpless, hiding, or dying off (e.g., the original 'Alien'), it gets minimal Rule 1 points. Do not mistake basic final-act survival for tactical warfare. It should score moderately (around 5.0 - 6.0).
    - ATMOSPHERE VS. TORTURE PORN: Do NOT heavily penalize dirty, industrial, or bleak settings (like the rusty prison in 'Alien 3'). Rule 2 penalties are strictly for mean-spirited biological torture and misery, not environmental grime.
    - THE DEFIANT SACRIFICE PROTOCOL (THE 'ALIEN 3' RULE): A tragic ending where the protagonist asserts supreme agency (e.g., Ripley's furnace swan-dive) is a MASSIVE WIN. It completely nullifies Rule 3 tragedy penalties and guarantees a strong score (7.5 - 8.0) because the protagonist owned their fate.
    - THE HIGH-CONCEPT EXEMPTION: Do not penalize violence if it serves a profound psychological or atmospheric narrative puzzle. If the violence is a necessary chess piece in a brilliant mind-bender, it is protected.
    - The '12 Monkeys' Rule: Intellectual puzzles nullify tragic ending penalties, but NEVER torture-porn squalor.
    - CRITICAL CONSENSUS OVERRIDE: Ignore general critical acclaim or Rotten Tomatoes scores. If a universally praised epic drags its feet or features endless travel montages, hammer it with the Pacing Penalty. Conversely, if a panned or niche film matches the tactical, high-concept DNA, reward it.
    - Benchmark comparison: Drop witty side-by-side roasts against benchmark horror/action films where fitting.

    Return ONLY valid JSON matching this schema:
    {{
      "score": 8.5,
      "summary": "A hilarious, swagger-filled roast or praise of the film packed with outrageous metaphors. YOU MUST CONCLUDE THIS SUMMARY WITH THIS EXACT FORMAT: 'You should [watch / avoid] this movie because [insert witty, compelling reason].'",
      "breakdown": [
        "**Baseline Score**: 5.0",
        "**Rule 1 (Agency)**: Witty explanation with swagger and colorful insults/praise...",
        "**Rule 2 (Squalor/Gore)**: Brutally funny description of the squalor (or lack thereof)...",
        "**Rule 3 (Payoff)**: Darkly comedic breakdown of the victory or misery...",
        "**Rule 4 (Narrative Puzzle)**: Sharp, sarcastic commentary on the narrative architecture...",
        "**Rule 5 (Pacing & Runtime)**: Sarcastic commentary on pacing bloat or momentum..."
      ]
    }}
    """
    
    response = client.models.generate_content(
        model='gemini-flash-latest',
        contents=movie_title,
        config={
            'system_instruction': system_prompt,
            'temperature': 0.75,
            'response_mime_type': 'application/json'
        }
    )
    return response.text

# 5. UI Layout & Sidebar Controls
st.markdown("<h1 style='text-align: center; margin-top: 1rem;'>🎬 Story Vs Gory</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #8b949e; font-size: 1.2rem; margin-bottom: 30px;'>Does your movie survive the algorithm?</p>", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Controls")
    
    with st.expander("🎛️ Tweak Model Weights"):
        st.write("Customize how the engine weights its rules for this session.")
        gore_tolerance = st.slider("Gore Penalty Weight", min_value=0.0, max_value=2.0, value=1.0, step=0.1)
        puzzle_weight = st.slider("Puzzle Bonus Weight", min_value=0.5, max_value=2.0, value=1.0, step=0.1)
        pacing_weight = st.slider("Pacing Penalty Weight", min_value=0.0, max_value=2.0, value=1.0, step=0.1)
        st.caption("ℹ️ Note: Auto-updates when tweaking sliders if a movie is already analyzed.")
    
    if 'gore_tolerance' not in locals():
        gore_tolerance = 1.0
    if 'puzzle_weight' not in locals():
        puzzle_weight = 1.0
    if 'pacing_weight' not in locals():
        pacing_weight = 1.0

    st.markdown("---")
    st.subheader("🧹 Cache Management")
    if st.button("Clear AI Analysis Cache"):
        cached_gemini_analysis.clear()
        st.success("AI analysis cache cleared!")

    st.markdown("---")
    st.markdown("<p style='font-size: 0.85rem;'><b>About:</b> Built on Gemini Flash with real-time OMDb integration.</p>", unsafe_allow_html=True)

# Main Input Section
col1, col2, col3 = st.columns([1, 2, 1])

# Initialize session state from URL parameters safely
if "movie_input" not in st.session_state:
    st.session_state.movie_input = st.query_params.get("movie", "")

with col2:
    with st.form("movie_form"):
        movie_title = st.text_input("Search for a film...", key="movie_input", placeholder="e.g., The Matrix, 12 Monkeys", label_visibility="collapsed")
        analyze_btn = st.form_submit_button("Run Algorithm")

    # Handle execution via button click or if session state has a movie
    active_movie = st.session_state.movie_input.strip()
    if analyze_btn or active_movie:
        if analyze_btn:
            st.query_params["movie"] = active_movie
            
        safe_title = html.escape(active_movie)
        search_query = urllib.parse.quote_plus(active_movie)

        progress_box = st.empty()
        
        try:
            progress_box.info(f"🎬 Fetching cinematic data for '{safe_title}'...")
            poster_url, poster_b64, rated, genre = fetch_movie_data(active_movie)
            
            progress_box.info("🧠 Booting up the unhinged AI critic...")
            raw_json = cached_gemini_analysis(active_movie, gore_tolerance, puzzle_weight, pacing_weight)
            
            progress_box.info("⚙️ Crunching the final Story Vs Gory score...")
            clean_json = raw_json.strip()
            if clean_json.startswith("```"):
                clean_json = clean_json.strip("`").replace("json\n", "", 1).strip()
                
            data = json.loads(clean_json)
            
            score_val = float(data.get("score", 5.0))
            summary_text = html.escape(data.get("summary", ""))
            breakdown_list = [html.escape(item) for item in data.get("breakdown", [])]
            
            # Regex to rip out just the final quippy verdict for the share card
            verdict_match = re.search(r"(You should .*? this movie because.*)", summary_text, re.IGNORECASE)
            short_summary = verdict_match.group(1) if verdict_match else summary_text.split('.')[-2] + "."
            
            progress_box.empty()
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if score_val >= 8.0:
                badge_class = "score-badge-green"
            elif score_val >= 5.0:
                badge_class = "score-badge-orange"
            else:
                badge_class = "score-badge-red"
                
            score_col1, score_col2 = st.columns([1, 2.5])
            
            with score_col1:
                st.image(poster_url, use_container_width=True)
                
                st.markdown(f"""
                <div class="streaming-box">
                    <p style="font-size: 0.85rem; color: #8b949e; margin-bottom: 8px;"><b>Rated:</b> {rated} | <b>Genre:</b> {genre}</p>
                    <a href="[https://www.justwatch.com/us/search?q=](https://www.justwatch.com/us/search?q=){search_query}" target="_blank" style="color: #58a6ff; text-decoration: none; font-size: 0.9rem; font-weight: 600;">🍿 Find Where to Watch</a>
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
                
                st.markdown(f"""<div class="breakdown-card">
<h4 style="margin-top: 0; margin-bottom: 16px; color: #ffffff;">🔍 Diagnostic Breakdown</h4>
<ul>
{breakdown_html}
</ul>
</div>""", unsafe_allow_html=True)

                # --- SHARE CARD WITH POSTER BACKGROUND & FALLBACK ---
                        with st.expander("✨ Generate Shareable Verdict Card", expanded=True):
                            wrapped_export_html = f"""
                            <!DOCTYPE html>
                            <html>
                            <head>
                            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap" rel="stylesheet">
                            <style>
                            body {{ 
                                margin: 0; 
                                padding: 20px; 
                                font-family: 'Inter', sans-serif; 
                                background-color: transparent; 
                                display: flex; 
                                flex-direction: column; 
                                align-items: center; 
                            }}
                            .capture-wrapper {{
                                padding: 10px;
                                background-color: #0d1117;
                                border-radius: 20px;
                            }}
                            .wrapped-container {{
                                position: relative;
                                background-image: linear-gradient(to bottom, rgba(13, 17, 23, 0.4), rgba(13, 17, 23, 0.95)), url('{poster_b64}');
                                background-size: cover;
                                background-position: center;
                                border: 2px solid #ff4b4b;
                                border-radius: 16px;
                                padding: 40px 30px;
                                text-align: center;
                                box-shadow: 0 10px 40px rgba(255, 75, 75, 0.2);
                                width: 100%;
                                max-width: 380px;
                                box-sizing: border-box;
                                overflow: hidden;
                            }}
                            .wrapped-header {{
                                font-size: 0.85rem;
                                text-transform: uppercase;
                                letter-spacing: 3px;
                                color: #ff8f00;
                                font-weight: 900;
                                margin-bottom: 15px;
                                text-shadow: 0 2px 4px rgba(0,0,0,0.8);
                            }}
                            .wrapped-title {{
                                font-size: 2rem;
                                font-weight: 900;
                                color: #ffffff;
                                margin-bottom: 20px;
                                line-height: 1.1;
                                text-shadow: 0 2px 10px rgba(0,0,0,0.8);
                            }}
                            .wrapped-score-box {{
                                background: rgba(0, 0, 0, 0.75);
                                backdrop-filter: blur(10px);
                                -webkit-backdrop-filter: blur(10px);
                                border: 2px solid #ff4b4b;
                                border-radius: 16px;
                                padding: 25px;
                                margin: 20px 0;
                                box-shadow: 0 10px 30px rgba(0,0,0,0.5);
                            }}
                            .wrapped-score {{
                                font-size: 4.5rem;
                                font-weight: 900;
                                color: #ff4b4b;
                                line-height: 1;
                                text-shadow: 0 0 20px rgba(255, 75, 75, 0.4);
                            }}
                            .wrapped-quote {{
                                font-size: 1.1rem;
                                color: #e6edf3;
                                font-style: italic;
                                font-weight: 700;
                                line-height: 1.4;
                                margin-top: 20px;
                                text-shadow: 0 2px 5px rgba(0,0,0,0.8);
                            }}
                            .wrapped-footer {{
                                margin-top: 35px;
                                padding-top: 15px;
                                border-top: 1px solid rgba(255, 255, 255, 0.1);
                                font-size: 0.75rem;
                                color: #8b949e;
                                font-weight: 800;
                                letter-spacing: 2px;
                            }}
                            .wrapped-url {{
                                font-size: 0.85rem;
                                color: #58a6ff;
                                font-weight: 600;
                                letter-spacing: 0px;
                                margin-top: 5px;
                            }}
                            .download-btn {{
                                background: linear-gradient(90deg, #ff4b4b 0%, #ff8f00 100%);
                                color: white;
                                border: none;
                                border-radius: 8px;
                                padding: 14px 28px;
                                font-weight: 800;
                                cursor: pointer;
                                font-size: 1rem;
                                margin-top: 25px;
                                font-family: 'Inter', sans-serif;
                                box-shadow: 0 4px 12px rgba(255, 75, 75, 0.4);
                                transition: transform 0.2s;
                            }}
                            .download-btn:disabled {{
                                background: #30363d;
                                color: #8b949e;
                                cursor: not-allowed;
                                box-shadow: none;
                            }}
                            .download-btn:hover:not(:disabled) {{
                                transform: translateY(-2px);
                            }}
                            </style>
                            </head>
                            <body>
                            
                            <div class="capture-wrapper" id="wrapped-capture-area">
                                <div class="wrapped-container">
                                    <div class="wrapped-header">Algorithm Verdict</div>
                                    <div class="wrapped-title">{safe_title}</div>
                                    <div class="wrapped-score-box">
                                        <div style="font-size: 0.75rem; color: #8b949e; margin-bottom: 5px; font-weight: 800; letter-spacing: 1px;">FINAL RATING</div>
                                        <div class="wrapped-score">{score_val}</div>
                                        <div style="font-size: 0.85rem; color: #ffffff; font-weight: 800; margin-top: 5px;">/ 10.0</div>
                                    </div>
                                    <div class="wrapped-quote">"{short_summary}"</div>
                                    <div class="wrapped-footer">
                                        STORY VS GORY<br>
                                        <div class="wrapped-url">storyvsgorymovierater.streamlit.app/?movie={search_query}</div>
                                    </div>
                                </div>
                            </div>
                            
                            <button class="download-btn" id="dl-button" disabled>⏳ Loading Engine...</button>

                            <script src="https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js"></script>
                            <script>
                            // Automatically enable button the moment html2canvas is ready
                            const checkLib = setInterval(() => {{
                                if (typeof html2canvas !== 'undefined') {{
                                    const btn = document.getElementById('dl-button');
                                    btn.disabled = false;
                                    btn.innerText = '📸 Download Image';
                                    clearInterval(checkLib);
                                }}
                            }}, 100);

                            function downloadWrapped() {{
                                const target = document.getElementById('wrapped-capture-area');
                                const btn = document.getElementById('dl-button');
                                
                                if (target) {{
                                    btn.innerText = '📸 Generating...';
                                    btn.style.opacity = '0.7';
                                    
                                    html2canvas(target, {{ 
                                        backgroundColor: '#0d1117',
                                        scale: 3,
                                        useCORS: true,
                                        allowTaint: true
                                    }}).then(canvas => {{
                                        const link = document.createElement('a');
                                        link.download = 'StoryVsGory_{search_query}.png';
                                        link.href = canvas.toDataURL('image/png');
                                        link.click();
                                        
                                        btn.innerText = '📸 Download Image';
                                        btn.style.opacity = '1';
                                    }}).catch(err => {{
                                        console.error('Error generating image:', err);
                                        btn.innerText = '❌ Error - Try Again';
                                        btn.style.opacity = '1';
                                    }});
                                }}
                            }}
                            </script>
                            </body>
                            </html>
                            """
                            components.html(wrapped_export_html, height=850)
                    
        except json.JSONDecodeError:
            progress_box.empty()
            st.warning("⚠️ The AI got a little too wild with its swagger and broke its own formatting! Please click **'Clear AI Analysis Cache'** in the sidebar and try running it again.")
        except Exception as e:
            progress_box.empty()
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                st.warning("⚠️ The movie algorithm backend is currently experiencing heavy traffic. Please give it a moment and try running it again!")
            else:
                st.error(f"An error occurred: {e}")