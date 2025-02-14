import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from datetime import datetime, timedelta

def load_json_file():
    """Upload a JSON file via Streamlit UI."""
    uploaded_file = st.file_uploader("Upload JSON File", type=["json"])
    if uploaded_file is not None:
        data = json.load(uploaded_file)
        st.success("✅ Successfully loaded JSON file!")
        return data
    else:
        st.warning("⚠️ Please upload a JSON file.")
        return None

def get_time_filter():
    """Allow user to select the time range in weeks, days, and hours."""
    weeks = st.number_input("Weeks", min_value=0, max_value=10, value=0)
    days = st.number_input("Days", min_value=0, max_value=6, value=3)
    hours = st.number_input("Hours", min_value=0, max_value=23, value=12)
    total_hours = (weeks * 7 * 24) + (days * 24) + hours
    st.write(f"🔹 Showing last {weeks} weeks, {days} days, and {hours} hours ({total_hours} hours total).")
    return total_hours

def remove_outliers(df, column_name):
    """Remove outliers using the Interquartile Range Method."""
    Q1 = df[column_name].quantile(0.25)
    Q3 = df[column_name].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return df[(df[column_name] >= lower_bound) & (df[column_name] <= upper_bound)]

def extract_lfp_amplitude_data(data, hemisphere, time_filter_hours):
    """Extracts and filters LFP and Amplitude data for a given hemisphere within the selected time range."""
    logs = data["DiagnosticData"]["LFPTrendLogs"].get(f"HemisphereLocationDef.{hemisphere}", {})
    records = []
    for timestamp, values in logs.items():
        for entry in values:
            records.append(
                {"DateTime": entry["DateTime"], "LFP": entry["LFP"], "Amplitude": entry["AmplitudeInMilliAmps"]})

    df = pd.DataFrame(records).sort_values("DateTime").reset_index(drop=True)
    df["DateTime"] = pd.to_datetime(df["DateTime"])

    # Apply time filtering
    latest_time = df["DateTime"].max()
    cutoff_time = latest_time - timedelta(hours=time_filter_hours)
    df = df[df["DateTime"] >= cutoff_time]

    # Remove outliers from LFP data
    df = remove_outliers(df, 'LFP')

    return df

def extract_lfp_thresholds(data, hemisphere):
    """Extracts upper and lower LFP thresholds for the specified hemisphere."""
    try:
        for program in data.get("Groups", {}).get("Final", []):
            if program.get("ActiveGroup", False):  # Only consider the active program
                for setting in program.get("ProgramSettings", {}).get("SensingChannel", []):
                    if setting.get("HemisphereLocation") == f"HemisphereLocationDef.{hemisphere}":
                        return setting.get("UpperLfpThreshold", None), setting.get("LowerLfpThreshold", None)
    except KeyError:
        pass
    return None, None  # Return None if not found

def plot_lfp_amplitude(df_left, df_right, upper_threshold_left, lower_threshold_left, upper_threshold_right,
                       lower_threshold_right):
    """Plots LFP values and stimulation amplitude with separate scales for left and right hemispheres."""
    fig, ax = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    # Plotting for the Left Hemisphere
    if df_left is not None and not df_left.empty:
        ax1 = ax[0].twinx()
        ax[0].plot(df_left["DateTime"], df_left["LFP"], label="LFP Left", color="red")
        ax1.plot(df_left["DateTime"], df_left["Amplitude"], label="Amplitude Left", color="black", linestyle="dashed")
        if upper_threshold_left is not None:
            ax[0].axhline(y=upper_threshold_left, color="blue", linestyle="--", label="Upper LFP Threshold Left")
        if lower_threshold_left is not None:
            ax[0].axhline(y=lower_threshold_left, color="purple", linestyle="--", label="Lower LFP Threshold Left")
        ax[0].set_title("LFP and Stimulation Amplitude - Left Hemisphere")
        ax[0].set_ylabel("LFP Value")
        ax1.set_ylabel("Stimulation Amplitude (mA)")
        ax[0].legend(loc="upper left")
        ax1.legend(loc="upper right")

    # Plotting for the Right Hemisphere
    if df_right is not None and not df_right.empty:
        ax2 = ax[1].twinx()
        ax[1].plot(df_right["DateTime"], df_right["LFP"], label="LFP Right", color="green")
        ax2.plot(df_right["DateTime"], df_right["Amplitude"], label="Amplitude Right", color="black", linestyle="dashed")
        if upper_threshold_right is not None:
            ax[1].axhline(y=upper_threshold_right, color="blue", linestyle="--", label="Upper LFP Threshold Right")
        if lower_threshold_right is not None:
            ax[1].axhline(y=lower_threshold_right, color="purple", linestyle="--", label="Lower LFP Threshold Right")
        ax[1].set_title("LFP and Stimulation Amplitude - Right Hemisphere")
        ax[1].set_xlabel("Time")
        ax[1].set_ylabel("LFP Value")
        ax2.set_ylabel("Stimulation Amplitude (mA)")
        ax[1].legend(loc="upper left")
        ax2.legend(loc="upper right")

    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)

def main():
    st.title("LFP and Stimulation Amplitude Analyzer")
    data = load_json_file()
    if data is not None:
        time_filter_hours = get_time_filter()
        df_left = extract_lfp_amplitude_data(data, "Left", time_filter_hours)
        df_right = extract_lfp_amplitude_data(data, "Right", time_filter_hours)
        upper_threshold_left, lower_threshold_left = extract_lfp_thresholds(data, "Left")
        upper_threshold_right, lower_threshold_right = extract_lfp_thresholds(data, "Right")
        plot_lfp_amplitude(df_left, df_right, upper_threshold_left, lower_threshold_left, upper_threshold_right,
                           lower_threshold_right)

if __name__ == "__main__":
    main()
