"""RepoMind AI — Streamlit entry point."""

import streamlit as st

from repomind.ui import render_app


def main() -> None:
    st.set_page_config(
        page_title="RepoMind AI",
        page_icon="🧠",
        layout="wide",
    )
    render_app()


if __name__ == "__main__":
    main()
