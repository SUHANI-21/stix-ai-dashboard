import streamlit as st

# ---------- PAGE CONFIG ----------
# This must be the first Streamlit command.
st.set_page_config(
    page_title="AI-Powered CTI Dashboard",
    page_icon="📊",
    layout="wide"
)

# ---------- CUSTOM NAVIGATION ----------
# This defines the structure of your app's sidebar navigation.
# It points to the pages located in your 'pages/' directory.
pg = st.navigation({
    "Main": [
        # This now points to the new dashboard file inside the pages folder.
        st.Page("pages/1_Dashboard.py", title="Dashboard", default=True),
        st.Page("pages/Version_Detector_and_Validator.py", title="Version Detector & Validator"),
    ],
    "Threat Analysis": [
        st.Page("pages/SDO_similarity_search.py", title="SDO Similarity Search"),
        st.Page("pages/Attack_Mapping.py", title="Attack Mapping"),
        st.Page("pages/malware_classifier.py", title="Malware Classifier"),
    ],
    "Assessment ": [
        st.Page("pages/Credibility_Assessment_Module.py", title="Credibility Assessment"),
        st.Page("pages/STIX_Chat.py", title="STIX Chat"),
    ],
    "Tools": [
        st.Page("pages/file_browser.py", title="File Browser"),
        st.Page("pages/Canonical_Output.py", title="Canonical Output Generator"),
    ]
})

# Run the navigation
pg.run()