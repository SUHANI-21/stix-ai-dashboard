import streamlit as st

st.set_page_config(page_title="Dashboard", layout="wide")

pg = st.navigation({
    "Main": [
        st.Page("pages/dashboard_home.py", title="Dashboard"),
        st.Page("pages/Version_Detector_and_Validator.py", title="Version Detector and Validator"),
    ],
    "Threat Analysis": [
        st.Page("pages/SDO_Similarity_Search.py", title="SDO Similarity Search"),
        st.Page("pages/Attack_Mapping.py", title="Attack Mapping"),
        st.Page("pages/malware_classifier.py", title="Malware Classifier"),
    ],
    "Assessment & Chat": [
        st.Page("pages/Credibility_Assessment_Module.py", title="Credibility Assessment Module"),
    ],
    "Tools": [
        st.Page("pages/file_browser.py", title="File Browser"),
    ]
})
pg.run()
