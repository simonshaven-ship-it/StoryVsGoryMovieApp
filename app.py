import streamlit as st
from google import genai

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

/* Crisp Headers */
h1, h2, h3 {
    color: #ffffff !important;
    font-weight: 800 !important;
    letter-spacing: -1px;
}

/* Customizing the text input box */
.stTextInput > div > div > input {
    background-color: #161b22;
    color: #ffffff;
    border-radius: 8px;
    border: 1px solid #30363d;
    padding: 12px;
}

/* Customizing the main action button with a gradient and hover effect */
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

/* The result card */
.result-card {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 30px;
    margin-top: 20px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.2);
    color: #e6edf3;
}
</style>
""", unsafe_allow_html=True)

# 3. Securely load the API Key and initialize the new Client
api_key = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=api_key)

# 4. The Core System Rules
system_prompt = """
You are a movie scoring algorithm based on the 'Story vs. Gore' scale. Evaluate the user's movie against these strict parameters:
- Rule 1 (Agency): Does the protagonist act with hyper-competence and treat survival like a tactical puzzle? (Reward points).
- Rule 2 (Squalor): Does the movie feature visceral body horror, miserable lifestyle squalor, or mean-spirited torture? (Deduct massive points. Stylized, theatrical action is exempt).
- Rule 3 (Payoff): Does the movie end with a triumphant, cathartic victory? (Reward points. Cynical, depressing 'Game Overs' are penalized).
- Exceptions: A flawless, mind-bending intellectual puzzle overrides a tragic ending (e.g., 12 Monkeys). Franchise lore can act as a shield (e.g., Twin Peaks).

Output a score from 1.0 to 10.0 and a punchy, entertaining explanation breaking down how it passes or fails the 3 Rules. Format with clear bullet points.
"""

# 5. Header Section
st.markdown("<h1 style='text-align: center; margin-top: 2rem;'>🎬 The Movie Enjoyment Predictor</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #8b949e; font-size: 1.2rem; margin-bottom: 40px;'>Based on the <b>Story vs. Gore</b> scale. Does your movie survive the algorithm?</p>", unsafe_allow_html=True)

# 6. Structural Layout
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
                    # Utilizing the new SDK generate_content method
                    response = client.models.generate_content(
                        model='gemini-3.5-flash',
                        contents=movie_title,
                        config={'system_instruction': system_prompt}
                    )
                    
                    # Wrap the AI output in our custom CSS card
                    st.markdown(f"""
                    <div class="result-card">
                        {response.text}
                    </div>
                    """, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"An error occurred: {e}")