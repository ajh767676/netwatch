import streamlit as st
import requests
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

API_URL = "http://127.0.0.1:8000"

st.title("📡 NetWatch Dashboard")

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Devices", "Event Log", "Settings"]
)

if page == "Dashboard":
    st.sidebar.header("Refresh Settings")
    refresh_rate = st.sidebar.slider("Auto-refresh every (seconds)", 5, 60, 10)
    st_autorefresh(interval=refresh_rate * 1000, key="data_refresh")

    devices = requests.get(f"{API_URL}/devices").json()

    if not devices:
        st.warning("No devices found. Add a device first.")
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

    total_devices = len(devices)
    online_devices = 0
    offline_devices = 0

    for device_id in device_names.keys():
        device_stats = requests.get(f"{API_URL}/stats?device_id={device_id}").json()

        if device_stats.get("last_status") == "Online":
            online_devices += 1
        else:
            offline_devices += 1

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Devices", total_devices)
    col2.metric("Online", online_devices)
    col3.metric("Offline", offline_devices)

    stats = requests.get(f"{API_URL}/stats?device_id={selected_id}").json()

    status = stats.get("last_status")

    if status == "Online":
        st.success("🟢 Device is Online")
    
    elif status == "Offline":
        st.error("🔴 Device is Offline")
    else:
        st.warning("⚪ Device has not been checked yet. Click Run Ping Now.")

    st.subheader("📊 Device Details")

    avg_latency = stats.get("average_latency_ms")
    last_latency = stats.get("last_latency_ms")
    last_checked = stats.get("last_timestamp")
    uptime = stats.get("uptime_percent", 0)
    total_checks = stats.get("total_checks", 0)

    col1, col2 = st.columns(2)

    col1.metric("📡 Status", status)
    col2.metric("📈 Uptime", f"{uptime}%")

    col1.metric(
        "⚡ Avg Latency",
        "N/A" if avg_latency is None else f"{avg_latency:.2f} ms"
    )

    col2.metric(
        "📶 Last Latency",
        "N/A" if last_latency is None else f"{last_latency:.2f} ms"
    )

    col1.metric("🔄 Total Checks", total_checks)

    if last_checked:
        col2.metric("🕒 Last Checked", last_checked)
    else:
        col2.metric("🕒 Last Checked", "Never")

    history = requests.get(f"{API_URL}/history?device_id={selected_id}").json()

    timestamps = [h["timestamp"] for h in history]
    latencies = [h["latency_ms"] for h in history]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=timestamps, y=latencies, mode="lines+markers"))
    fig.update_layout(
        title="Latency Over Time (ms)",
        xaxis_title="Time",
        yaxis_title="Latency (ms)"
    )
    st.plotly_chart(fig)

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
    


if page == "Devices":
    st.header("🖥️ Device Management")

    st.write("Add a new device to monitor.")

    with st.form("add_device_form"):
        name = st.text_input("Device Name")
        ip = st.text_input("IP Address")
        device_type = st.selectbox(
            "Device Type",
            ["Router", "Server", "Printer", "Switch", "PC", "Other"]
        )

        submitted = st.form_submit_button("Add Device")

        if submitted:
            if not name or not ip:
                st.error("Please enter both a device name and IP address.")
            else:
                new_device = {
                    "name": name,
                    "ip_address": ip,
                    "device_type": device_type
                }

                response = requests.post(f"{API_URL}/devices", json=new_device)

                if response.status_code == 200:
                    st.success(f"Device '{name}' added successfully!")
                else:
                    st.error("Could not add device.")
                    st.write(response.text)

    st.divider()

    st.subheader("📋 Monitored Devices")

    devices = requests.get(f"{API_URL}/devices").json()

    if devices:
        st.table(devices)
    else:
        st.info("No devices have been added yet.")

if page == "Event Log":
    st.header("📜 Event Log")
    st.info("Coming soon.")


if page == "Settings":
    st.header("⚙️ Settings")
    st.info("Coming soon.")