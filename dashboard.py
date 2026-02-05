import streamlit as st
import tempfile
import plotly.graph_objects as go
import json
from pathlib import Path
from pyvis.network import Network
import streamlit.components.v1 as components
from stix.core import STIXPackage

from modules.version_detector import detect_stix_version
from modules.validator import validate_stix
from modules.cti_converter import convert_to_common_cti
from modules.threat_classifier import classify_threat
from modules.credibility_assessor import assess_credibility

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="AI CTI Dashboard", layout="wide")

# ---------- SIDEBAR NAVIGATION ----------
st.sidebar.title("🔍 Navigation")
page = st.sidebar.selectbox(
    "Choose a page:",
    ["STIX Analyzer", "RAG Chat", "File Browser", "Malware Inference", "Malware Mapping", "Malware Classifier"]
)

if page == "RAG Chat":
    exec(open("pages/rag_chat.py").read())
    st.stop()
elif page == "File Browser":
    exec(open("pages/file_browser.py").read())
    st.stop()
elif page == "Malware Inference":
    exec(open("pages/malware_inference.py").read())
    st.stop()
elif page == "Malware Mapping":
    exec(open("pages/malware_mapping.py").read())
    st.stop()
elif page == "Malware Classifier":
    exec(open("pages/malware_classifier.py").read())
    st.stop()
# If "STIX Analyzer" is selected, continue with main dashboard

# ---------- THEME + CUSTOM UI STYLING ----------
st.markdown("""
<style>
.stApp { background: radial-gradient(circle at top left, #1a0b2e, #0d0d1a); color: #e0e0ff; }
.card {
    background: linear-gradient(145deg, #1f1035, #140a24);
    padding: 20px; border-radius: 15px;
    box-shadow: 0 0 15px rgba(155, 89, 182, 0.4);
    text-align: center;
}
h1, h2, h3 { color: #c084fc; }
label, .stMultiSelect label {
    color: #ff66ff !important;
    font-weight: bold !important;
    font-size: 21px !important;
}
div.stDownloadButton > button {
    background-color: #c084fc !important;
    color: black !important;
    font-size: 25px !important;
    font-weight: bold !important;
    border-radius: 10px !important;
}
.detected-text {
    color: #00e5ff;
    font-size: 21px;
    font-weight: bold;
}
.validation-text {
    color: #00ff99;
    font-size: 21px;
    font-weight: bold;
}
.ai-explain-title {
    color: #ff9ff3;
    font-size: 26px;
    font-weight: bold;
    margin-top: 20px;
}
.ai-explain-text {
    color: #f1c40f;
    font-size: 22px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("## AI-Powered Cyber Threat Intelligence Dashboard")
st.markdown("---")

# 🔄 SHARED FILE UPLOADER (used by all pages)
# 🔄 SHARED FILE UPLOADER (used by all pages)
if "shared_stix_bytes" not in st.session_state:
    st.session_state.shared_stix_bytes = None
if "shared_stix_name" not in st.session_state:
    st.session_state.shared_stix_name = None

uploaded_file = st.file_uploader(
    "Upload STIX (JSON or XML)",
    type=["json", "xml"],
    key="shared_uploader"
)

if uploaded_file:
    st.session_state.shared_stix_bytes = uploaded_file.getvalue()
    st.session_state.shared_stix_name = uploaded_file.name

if st.session_state.shared_stix_bytes:
    uploaded_file = st.session_state.shared_stix_bytes
    uploaded_filename = st.session_state.shared_stix_name
else:
    uploaded_file = None


# ---------- SMART THREAT TYPE LOGIC ----------
def derive_precise_threat_type(objects):
    types_present = {obj.get("type") for obj in objects}
    if "malware" in types_present: return "Malware Activity"
    if "intrusion-set" in types_present: return "Advanced Persistent Threat (APT)"
    if "campaign" in types_present: return "Coordinated Attack Campaign"
    if "attack-pattern" in types_present: return "Attack Technique Activity"
    if "indicator" in types_present: return "Suspicious Indicators Detected"

    full_text = json.dumps(objects).lower()
    if "ransomware" in full_text: return "Ransomware Attack"
    if "phishing" in full_text: return "Phishing Attack"
    return None


if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_filename).suffix) as tmp:
     tmp.write(uploaded_file)
     file_path = tmp.name


    file_ext = Path(file_path).suffix.lower()

    # -------- STIX 2 JSON --------
    if file_ext == ".json":
        version = detect_stix_version(file_path)
        valid, msg = validate_stix(file_path)

        st.markdown(f"<div class='validation-text'>{msg}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='detected-text'>Detected STIX Version: {version}</div>", unsafe_allow_html=True)

        if not valid:
            st.warning("Validation failed — showing visualization anyway.")

        cti_data = convert_to_common_cti(file_path)
        with open(file_path) as f:
            data = json.load(f)

    # -------- STIX 1 XML --------
    elif file_ext == ".xml":
        st.success("STIX 1.x XML detected")
        stix_package = STIXPackage.from_xml(file_path)
        data = {"objects": []}

        for ind in getattr(stix_package, "indicators", []):
            data["objects"].append({"id": ind.id_, "type": "indicator", "name": ind.title})
        for camp in getattr(stix_package, "campaigns", []):
            data["objects"].append({"id": camp.id_, "type": "campaign", "name": camp.title})
        for actor in getattr(stix_package, "threat_actors", []):
            data["objects"].append({"id": actor.id_, "type": "intrusion-set", "name": actor.title})

        cti_data = [{"description": "STIX 1.x data", "confidence": 50}]
    else:
        st.error("Unsupported file type")
        st.stop()

    # ---------- PRECISE THREAT TYPE ----------
    objects = data.get("objects", [])
    precise_type = derive_precise_threat_type(objects)

    desc = cti_data[0].get("description", "")
    conf = cti_data[0].get("confidence", 50)

    if precise_type:
        threat_type = precise_type
        prob = 90
    else:
        threat_type, prob = classify_threat(desc)

    score, level = assess_credibility(conf, prob)

    # ---------- OVERVIEW CARDS ----------
    st.markdown("## Threat Overview")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='card'><h3>Threat Type</h3><h1>{threat_type}</h1></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='card'><h3>AI Probability</h3><h1>{prob}%</h1></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='card'><h3>Credibility Score</h3><h1>{score} ({level})</h1></div>", unsafe_allow_html=True)

    st.markdown("---")

    # ---------- GAUGE ----------
    st.markdown("### Threat Probability")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=prob,
        title={'text': "Threat Probability"},
        gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#c084fc"}}
    ))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("---")

    # ---------- GRAPH HEADER + FILTER ----------
    type_counts = {}
    for o in objects:
        t = o.get("type")
        type_counts[t] = type_counts.get(t, 0) + 1

    header_col1, header_col2 = st.columns([2, 6])
    with header_col1:
        st.markdown("### Threat Relationship Graph")
    with header_col2:
        selected_types = st.multiselect(
            "Filter Node Types",
            list(type_counts.keys()),
            default=list(type_counts.keys()),
            key="top_filter"
        )

    graph_col, side_col = st.columns([5, 1])

    with graph_col:
        net = Network(height="750px", width="100%", bgcolor="#0d0d1a", font_color="white")
        net.set_options("""var options = {"physics":{"barnesHut":{"gravitationalConstant":-4000,"springLength":180}},"interaction":{"hover":true},"edges":{"arrows":{"to":{"enabled":true}},"smooth":{"type":"dynamic"}}}""")

        color_map = {
            "malware": "#ff9f43",
            "attack-pattern": "#ff4b5c",
            "tool": "#1dd1a1",
            "intrusion-set": "#54a0ff",
            "campaign": "#5f27cd",
            "indicator": "#feca57",
            "report": "#aaaaaa"
        }

        for obj in objects:
            if obj.get("type") in selected_types:
                net.add_node(obj.get("id"), label=obj.get("name", obj.get("type"))[:20], title=json.dumps(obj, indent=2), color=color_map.get(obj.get("type"), "#cccccc"))

        visible_node_ids = {obj.get("id") for obj in objects if obj.get("type") in selected_types}

        for obj in objects:
            if obj.get("type") == "relationship":
                src = obj.get("source_ref")
                tgt = obj.get("target_ref")
                if src in visible_node_ids and tgt in visible_node_ids:
                    net.add_edge(src, tgt, label=obj.get("relationship_type", ""), arrows="to")

        graph_path = "stix_graph.html"
        net.save_graph(graph_path)
        components.html(open(graph_path).read(), height=750)

        with open(graph_path, "r") as f:
            st.download_button("💾 Download Graph HTML", f.read(), "threat_graph.html")

    with side_col:
        st.markdown("### Node Counts")
        for t, count in type_counts.items():
            st.markdown(f"**{t}**: {count}")

    st.markdown("<div class='ai-explain-title'>🧠 AI Explanation</div>", unsafe_allow_html=True)
    st.markdown("<div class='ai-explain-text'>This graph shows how different cyber threat entities are connected through relationships like usage, targeting, or indication.</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='ai-explain-text'><b>Description:</b> {desc}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='ai-explain-text'><b>AI Assessment:</b> {threat_type} with {prob}% probability</div>", unsafe_allow_html=True)

else:
    st.info("Upload a STIX file to begin.")
