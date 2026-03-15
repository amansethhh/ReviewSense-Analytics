import streamlit as st

st.title("Bulk Review Analysis")

file = st.file_uploader("Upload CSV file")

if file:
    st.success("Bulk processing module will appear here.")