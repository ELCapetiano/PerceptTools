import json
import os
import streamlit as st

def remove_long_columns(obj, exclude_keys=("SignalFrequencies", "SignalPsdValues")):
    """Recursively removes specified keys from a JSON object."""
    if isinstance(obj, dict):
        return {k: remove_long_columns(v, exclude_keys) for k, v in obj.items() if k not in exclude_keys}
    elif isinstance(obj, list):
        return [remove_long_columns(item, exclude_keys) for item in obj]
    else:
        return obj

def extract_sessions_from_json():
    """Allows user to upload a JSON file, extracts relevant session data, and provides a downloadable file."""
    st.title("Extract Sessions from JSON")
    uploaded_file = st.file_uploader("Upload a JSON file", type=["json"])
    
    if uploaded_file is not None:
        data = json.load(uploaded_file)
        
        # Extract sessions and clean them
        sessions_cleaned = []
        for session in data.get("GroupHistory", []):
            cleaned_session = remove_long_columns(session)
            sessions_cleaned.append(cleaned_session)
        
        # Convert to JSON string
        cleaned_json_str = json.dumps(sessions_cleaned, indent=4)
        
        # Provide download link
        st.download_button(
            label="Download Cleaned Sessions JSON",
            data=cleaned_json_str,
            file_name="extracted_sessions.json",
            mime="application/json"
        )
        
        st.success("✅ Successfully processed the JSON file!")

if __name__ == "__main__":
    extract_sessions_from_json()
