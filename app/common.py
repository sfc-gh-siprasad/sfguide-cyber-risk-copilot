"""Shared data context for all pages."""

import os

import streamlit as st

import analytics
import mock_backend
import snowflake_backend

SAMPLE, LIVE = "Sample data", "Snowflake"


@st.cache_data(ttl="1h", show_spinner="Loading sample data")
def _sample_frames():
    return mock_backend.load_frames()


@st.cache_data(ttl="15m", show_spinner="Querying Snowflake")
def _live_frames():
    return snowflake_backend.load_frames()


@st.cache_data(ttl="1h")
def _prepared(source: str):
    frames = _live_frames() if source == LIVE else _sample_frames()
    return analytics.prepare(frames)


def default_mode() -> str:
    return LIVE if os.environ.get("CYBER_COPILOT_MODE", "mock").lower() == "live" else SAMPLE


def context() -> dict:
    """Return backend, frames, joined findings and whether live data is in use."""
    wanted = st.session_state.get("mode") or SAMPLE
    if wanted == LIVE:
        try:
            frames = _live_frames()
            return {"live": True, "backend": snowflake_backend, "frames": frames, "df": _prepared(LIVE)}
        except Exception as exc:
            st.session_state["live_error"] = str(exc)
    return {"live": False, "backend": mock_backend, "frames": _sample_frames(), "df": _prepared(SAMPLE)}
