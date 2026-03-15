import streamlit as st

st.title("Live Sentiment Prediction")

review = st.text_area("Enter a review")

if st.button("Analyze"):
    st.success("Prediction module will appear here.")