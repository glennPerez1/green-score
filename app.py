
import streamlit as st

st.set_page_config(
    page_title="GreenScore",
    page_icon="🌱",
    layout="wide",
)

st.sidebar.title("🌱 GreenScore")
st.sidebar.caption("Smarter campus waste management")

role = st.sidebar.radio(
    "Demo role",
    ["Admin", "Student"],
)

if role == "Admin":
    from dashboard import render_dashboard
    render_dashboard()
else:
    from student_ui import render_student_ui
    render_student_ui()

st.sidebar.divider()
st.sidebar.caption("GreenScore • Hackathon MVP")
