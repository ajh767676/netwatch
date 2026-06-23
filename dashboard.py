import streamlit as st
import requests
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

API_URL = "http://127.0.0.1:8000"

st.title("📡 NetWatch Dashboard")

# Auto-refresh controls
st.sidebar.header("Refresh Settings")
refresh_rate = st.sidebar.slider("Auto-refresh every (seconds)", 5, 60, 10)
st_autorefresh(interval=refresh_rate * 1000, key="data_refresh")

# Fetch devices
devices = requests.get(f"{API_URL}/devices").json()

if not devices:
    st.warning("No devices found. Add a device in the API first.")
    st.stop()

device_names = {d["id"]: d["name"] for d in devices}

selected_id = st.selectbox(
    "Select a device",
    options=list(device_names.keys()),
    format_func=lambda x: device_names[x]
)

if st.button("Run Ping Now"):
    requests.post(f"{API_URL}/status/run")
    st.success("Ping executed!")


# Fetch stats
stats = requests.get(f"{API_URL}/stats?device_id={selected_id}").json()

status = stats["last_status"]

if status == "Online":
    st.success("🟢 Device is Online")
else:
    st.error("🔴 Device is Offline")

st.subheader("📊 Device Stats")
st.json(stats)

# Fetch history
history = requests.get(f"{API_URL}/history?device_id={selected_id}").json()

timestamps = [h["timestamp"] for h in history]
latencies = [h["latency_ms"] for h in history]

# Latency chart
fig = go.Figure()
fig.add_trace(go.Scatter(x=timestamps, y=latencies, mode="lines+markers"))
fig.update_layout(title="Latency Over Time (ms)", xaxis_title="Time", yaxis_title="Latency (ms)")
st.plotly_chart(fig)

# Status timeline chart
status_values = [1 if h["status"] == "Online" else 0 for h in history]

status_fig = go.Figure()
status_fig.add_trace(go.Bar(
    x=timestamps,
    y=status_values,
    marker_color=["green" if v == 1 else "red" for v in status_values]
))

status_fig.update_layout(
    title="Status Timeline (Online = Green, Offline = Red)",
    xaxis_title="Time",
    yaxis=dict(
        tickmode="array",
        tickvals=[0, 1],
        ticktext=["Offline", "Online"]
    ),
    showlegend=False
)

st.plotly_chart(status_fig)


# Uptime gauge
uptime = stats["uptime_percent"]

gauge = go.Figure(go.Indicator(
    mode="gauge+number",
    value=uptime,
    title={"text": "Uptime %"},
    gauge={"axis": {"range": [0, 100]}}
))

st.plotly_chart(gauge)
