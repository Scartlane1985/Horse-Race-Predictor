
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Horse Race Predictor", layout="centered")

st.title("Horse Race Predictor – Paste a Race Link")

st.markdown("Paste a race URL from [At The Races](https://www.attheraces.com/racecards)")

race_url = st.text_input("Race URL", placeholder="https://www.attheraces.com/racecard/...")

if race_url:
    st.success(f"URL received: {race_url}")
    
    # Simulated runner data (placeholder until live scraper integration)
    data = {
        "Horse": ["Thunder Rhythm", "Mud Dancer", "Track Bullet"],
        "Form": ["3211", "2P14", "4352"],
        "Wins": [3, 1, 0],
        "Distance Match": [1, 0.5, 0.3],
        "Ground Match": [0.9, 0.3, 0.4]
    }

    df = pd.DataFrame(data)
    df["Score"] = (
        df["Wins"] * 10 +
        df["Distance Match"] * 20 +
        df["Ground Match"] * 20 +
        df["Form"].apply(lambda x: sum([5 if c == '1' else 3 if c == '2' else 1 if c == '3' else 0 for c in x]))
    )

    df = df.sort_values(by="Score", ascending=False)

    st.markdown("### Predictions")
    st.dataframe(df[["Horse", "Score"]].reset_index(drop=True))
    st.markdown("### Full Breakdown")
    st.dataframe(df.reset_index(drop=True))
else:
    st.info("Waiting for a valid race URL...")
