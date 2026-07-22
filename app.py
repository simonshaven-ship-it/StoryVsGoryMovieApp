import streamlit as st
import google.generativeai as genai

# 1. Setup the UI Page
st.set_page_config(page_title="Story vs. Gore Predictor", page_icon="🎬", layout="centered")
st.title("🎬 The Movie Enjoyment Predictor")
st.write("Based on the **Story vs. Gore** scale. Enter a movie to see if it survives the algorithm.")

# 2. Securely load the API Key
# This pulls the key invisibly from your secrets file (or cloud settings)
api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)

# 3. The Core System Rules
system_prompt = """
You are a movie scoring algorithm based on the 'Story vs. Gore' scale. Evaluate the user's movie against these strict parameters:
- Rule 1 (Agency): Does the protagonist act with hyper-competence and treat survival like a tactical puzzle? (Reward points).
- Rule 2 (Squalor): Does the movie feature visceral body horror, miserable lifestyle squalor, or mean-spirited torture? (Deduct massive points. Stylized, theatrical action is exempt).
- Rule 3 (Payoff): Does the movie end with a triumphant, cathartic victory? (Reward points. Cynical, depressing 'Game Overs' are penalized).
- Exceptions: A flawless, mind-bending intellectual puzzle overrides a tragic ending (e.g., 12 Monkeys). Franchise lore can act as a shield (e.g., Twin Peaks).

Output a score from 1.0 to 10.0 and a punchy, entertaining explanation breaking down how it passes or fails the 3 Rules. Format with clear bullet points.
"""

# 4. The User Input
movie_title = st.text_input("🍿 Enter a movie title (e.g., The Matrix, 12 Monkeys):")

# 5. The Engine
if st.button("Analyze Movie"):
    if not movie_title:
        st.warning("Please enter a movie title.")
    else:
        with st.spinner(f"Running {movie_title} through the board..."):
            try:
                model = genai.GenerativeModel('gemini-flash-latest', system_instruction=system_prompt)
                response = model.generate_content(movie_title)
                
                st.success("Analysis Complete!")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"An error occurred: {e}")