"""
GreenScore Analytics Engine
Owned by Person 3 (Application, Analytics, and Deployment)
Generates interactive Plotly visualizations for campus waste-management oversight.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from constants import (
    STATUS_SUBMITTED,
    STATUS_UNDER_REVIEW,
    STATUS_VERIFIED,
    STATUS_RESOLVED,
    STATUS_REJECTED,
)

# Status color palette aligned with GreenScore branding
STATUS_COLOR_MAP = {
    STATUS_SUBMITTED: "#6c757d",      # Gray / Neutral
    STATUS_UNDER_REVIEW: "#f59e0b",   # Amber / Caution
    STATUS_VERIFIED: "#10b981",       # Emerald / In-Progress Positive
    STATUS_RESOLVED: "#1b4332",       # Deep Green / Complete
    STATUS_REJECTED: "#ef4444",       # Red / Rejected
}

BRAND_GREEN = "#1b4332"
BRAND_ACCENT = "#2d6a4f"
BRAND_LIGHT = "#d8f3dc"


def _empty_figure(message: str) -> go.Figure:
    """Return an empty figure displaying a clean message when data is insufficient."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=14, color="#6b7280"),
    )
    fig.update_layout(
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        margin=dict(l=20, r=20, t=30, b=20),
        height=260,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def plot_status_breakdown(reports: List[Dict[str, Any]]) -> go.Figure:
    """
    Generate a donut chart showing the distribution of reports by status.
    """
    if not reports:
        return _empty_figure("No report data available yet.")

    df = pd.DataFrame(reports)
    if "status" not in df.columns or df["status"].empty:
        return _empty_figure("No report statuses recorded.")

    status_counts = df["status"].value_counts().reset_index()
    status_counts.columns = ["status", "count"]

    fig = px.pie(
        status_counts,
        values="count",
        names="status",
        hole=0.55,
        color="status",
        color_discrete_map=STATUS_COLOR_MAP,
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        marker=dict(line=dict(color="#ffffff", width=2)),
        hovertemplate="<b>%{label}</b><br>Reports: %{value}<br>Share: %{percent}<extra></extra>",
    )

    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        margin=dict(l=20, r=20, t=30, b=40),
        height=320,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def plot_issues_by_category(reports: List[Dict[str, Any]]) -> go.Figure:
    """
    Generate a horizontal bar chart showing frequency of each issue category.
    """
    if not reports:
        return _empty_figure("No report data available yet.")

    df = pd.DataFrame(reports)
    if "issue_type" not in df.columns or df["issue_type"].empty:
        return _empty_figure("No issue categories recorded.")

    issue_counts = df["issue_type"].value_counts().reset_index()
    issue_counts.columns = ["issue_type", "count"]
    issue_counts = issue_counts.sort_values(by="count", ascending=True)

    fig = px.bar(
        issue_counts,
        x="count",
        y="issue_type",
        orientation="h",
        color_discrete_sequence=[BRAND_ACCENT],
        text="count",
    )

    fig.update_traces(
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Incidents Reported: %{x}<extra></extra>",
        marker=dict(cornerradius=5),
    )

    fig.update_layout(
        xaxis_title="Number of Reports",
        yaxis_title="",
        xaxis=dict(dtick=1),
        margin=dict(l=20, r=40, t=20, b=40),
        height=300,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def plot_reports_by_bin(reports: List[Dict[str, Any]], top_n: int = 8) -> go.Figure:
    """
    Generate a bar chart showing campus locations/bins with the highest report activity.
    """
    if not reports:
        return _empty_figure("No report data available yet.")

    df = pd.DataFrame(reports)
    if "bin_id" not in df.columns or df["bin_id"].empty:
        return _empty_figure("No bin location data recorded.")

    # Combine bin_id and location if location column is present
    if "bin_location" in df.columns and df["bin_location"].notna().any():
        df["display_bin"] = df["bin_id"] + " (" + df["bin_location"] + ")"
    else:
        df["display_bin"] = df["bin_id"]

    bin_counts = df["display_bin"].value_counts().head(top_n).reset_index()
    bin_counts.columns = ["bin", "count"]
    bin_counts = bin_counts.sort_values(by="count", ascending=True)

    fig = px.bar(
        bin_counts,
        x="count",
        y="bin",
        orientation="h",
        color_discrete_sequence=["#40916c"],
        text="count",
    )

    fig.update_traces(
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Reports: %{x}<extra></extra>",
        marker=dict(cornerradius=5),
    )

    fig.update_layout(
        xaxis_title="Number of Reports",
        yaxis_title="",
        xaxis=dict(dtick=1),
        margin=dict(l=20, r=40, t=20, b=40),
        height=320,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def plot_activity_timeline(reports: List[Dict[str, Any]]) -> go.Figure:
    """
    Generate an activity timeline chart showing daily report submissions.
    """
    if not reports:
        return _empty_figure("No report timeline data available.")

    df = pd.DataFrame(reports)
    if "created_at" not in df.columns or df["created_at"].empty:
        return _empty_figure("No timestamps found in reports.")

    # Parse created_at timestamps safely
    try:
        df["date"] = pd.to_datetime(df["created_at"]).dt.date
    except Exception:
        return _empty_figure("Could not parse report dates.")

    timeline = df.groupby(["date", "status"]).size().reset_index(name="count")
    timeline["date"] = timeline["date"].astype(str)

    fig = px.bar(
        timeline,
        x="date",
        y="count",
        color="status",
        color_discrete_map=STATUS_COLOR_MAP,
        barmode="stack",
    )

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Reports",
        yaxis=dict(dtick=1),
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
        margin=dict(l=20, r=20, t=20, b=50),
        height=320,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def plot_points_distribution(ledger_entries: List[Dict[str, Any]]) -> go.Figure:
    """
    Generate a chart showing GreenPoints awarded by action type (verified vs resolved).
    """
    if not ledger_entries:
        return _empty_figure("No GreenPoints awarded yet.")

    df = pd.DataFrame(ledger_entries)
    if "action" not in df.columns or df["action"].empty:
        return _empty_figure("No points ledger records.")

    action_summary = df.groupby("action")["points"].sum().reset_index()
    action_summary["display_action"] = action_summary["action"].map({
        "verified": "Report Verification (+5 pts)",
        "resolved": "Issue Resolution (+5 pts)",
    }).fillna(action_summary["action"])

    fig = px.pie(
        action_summary,
        values="points",
        names="display_action",
        color="action",
        color_discrete_map={
            "verified": "#52b788",
            "resolved": "#1b4332",
        },
        hole=0.45,
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent+value",
        hovertemplate="<b>%{label}</b><br>Points Awarded: %{value} 🌱<extra></extra>",
    )

    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        margin=dict(l=20, r=20, t=20, b=40),
        height=280,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig
