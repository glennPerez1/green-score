
import streamlit as st


def render_dashboard():
    st.title("🌿 GreenScore Dashboard")
    st.caption("Campus waste management overview")

    st.info("Dashboard integration in progress.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Reports", 0)
    c2.metric("Pending Reports", 0)
    c3.metric("Resolved Reports", 0)
    c4.metric("GreenPoints Awarded", 0)

    st.write("Analytics and report management coming next.")
