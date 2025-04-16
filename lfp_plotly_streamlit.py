import json
import pandas as pd
import streamlit as st
import plotly.graph_objects as go


def remove_outliers(df, column_name):
    Q1 = df[column_name].quantile(0.25)
    Q3 = df[column_name].quantile(0.75)
    IQR = Q3 - Q1.0
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    return df[(df[column_name] >= lower) & (df[column_name] <= upper)]


def extract_lfp_amplitude_data(data, hemisphere):
    logs = data.get("DiagnosticData", {}).get("LFPTrendLogs", {}).get(f"HemisphereLocationDef.{hemisphere}", {})
    records = []
    for timestamp, entries in logs.items():
        for entry in entries:
            records.append({
                "DateTime": entry["DateTime"],
                "LFP": entry["LFP"],
                "Amplitude": entry["AmplitudeInMilliAmps"]
            })
    df = pd.DataFrame(records)
    if not df.empty:
        df["DateTime"] = pd.to_datetime(df["DateTime"])
        df = df.sort_values("DateTime").reset_index(drop=True)
        df = remove_outliers(df, "LFP")
    return df


def extract_lfp_thresholds(data, hemisphere):
    try:
        for group in data.get("Groups", {}).get("Final", []):
            if group.get("ActiveGroup", False):
                for setting in group.get("ProgramSettings", {}).get("SensingChannel", []):
                    if setting.get("HemisphereLocation") == f"HemisphereLocationDef.{hemisphere}":
                        return setting.get("UpperLfpThreshold"), setting.get("LowerLfpThreshold")
    except Exception as e:
        st.warning(f"[WARNING] Could not extract thresholds for {hemisphere}: {e}")
    return None, None


def plot_interactive(df_left, df_right, thresholds_left, thresholds_right):
    fig = make_combined_figure(df_left, df_right, thresholds_left, thresholds_right)
    st.plotly_chart(fig, use_container_width=True)


def make_combined_figure(df_left, df_right, thresholds_left, thresholds_right):
    fig = go.Figure()

    # LEFT LFP
    fig.add_trace(go.Scatter(x=df_left["DateTime"], y=df_left["LFP"],
                             mode="lines", name="LFP Left", line=dict(color='red')))
    if thresholds_left[0]:
        fig.add_hline(y=thresholds_left[0], line=dict(color='green', dash='dash'), annotation_text="Left Upper")
    if thresholds_left[1]:
        fig.add_hline(y=thresholds_left[1], line=dict(color='purple', dash='dash'), annotation_text="Left Lower")

    # LEFT Amplitude
    fig.add_trace(go.Scatter(x=df_left["DateTime"], y=df_left["Amplitude"],
                             mode="lines", name="Amplitude Left", line=dict(color='blue', dash='dot')))

    # RIGHT LFP
    fig.add_trace(go.Scatter(x=df_right["DateTime"], y=df_right["LFP"],
                             mode="lines", name="LFP Right", line=dict(color='green')))
    if thresholds_right[0]:
        fig.add_hline(y=thresholds_right[0], line=dict(color='green', dash='dash'), annotation_text="Right Upper")
    if thresholds_right[1]:
        fig.add_hline(y=thresholds_right[1], line=dict(color='purple', dash='dash'), annotation_text="Right Lower")

    # RIGHT Amplitude
    fig.add_trace(go.Scatter(x=df_right["DateTime"], y=df_right["Amplitude"],
                             mode="lines", name="Amplitude Right", line=dict(color='black', dash='dot')))

    fig.update_layout(
        title="LFP and Amplitude Trends (Left & Right Hemispheres)",
        xaxis_title="Time",
        yaxis_title="Signal",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


# Streamlit App UI
st.set_page_config(layout="wide", page_title="LFP Viewer (Plotly)")
st.title("📈 Interactive LFP & Amplitude Viewer (Plotly Edition)")

uploaded_file = st.file_uploader("Upload a Percept JSON file", type="json")

if uploaded_file:
    try:
        data = json.load(uploaded_file)
        st.success("✅ JSON loaded")

        df_left = extract_lfp_amplitude_data(data, "Left")
        df_right = extract_lfp_amplitude_data(data, "Right")

        if df_left.empty or df_right.empty:
            st.error("⚠️ One or both hemispheres have no LFP data after outlier filtering.")
        else:
            ul, ll = extract_lfp_thresholds(data, "Left")
            ur, lr = extract_lfp_thresholds(data, "Right")

            st.subheader("🎯 Thresholds")
            st.write(f"🔹 Left:  Upper = {ul}, Lower = {ll}")
            st.write(f"🔹 Right: Upper = {ur}, Lower = {lr}")

            plot_interactive(df_left, df_right, (ul, ll), (ur, lr))

    except Exception as e:
        st.exception(f"❌ Failed to process file: {e}")
else:
    st.info("👈 Please upload a Percept JSON file to begin.")
