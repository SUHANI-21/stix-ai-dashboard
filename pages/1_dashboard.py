import streamlit as st
import tempfile
import plotly.graph_objects as go
import json
from pathlib import Path
from pyvis.network import Network
import streamlit.components.v1 as components
from stix.core import STIXPackage
from datetime import datetime

from modules.enhanced_detector import EnhancedVersionChecker
from modules.enhanced_validator import EnhancedValidator
from modules.cti_converter import convert_to_common_cti
from modules.threat_classifier import classify_threat
from threat_assessment import analyze_bundle
from modules.converter import STIXConverter


# ---------- THEME + CUSTOM UI STYLING ----------
st.markdown("""
<style>
.stApp {
    background-color: white;
    color: black;
}
.stSidebar {
    background-color: #f8f9fa;
}
.stSelectbox label, .stTextInput label, .stNumberInput label, .stMultiSelect label {
    color: black !important;
}
.stMarkdown {
    color: black;
}
.card {
    background: #f8f9fa;
    padding: 20px; border-radius: 15px;
    box-shadow: 0 0 15px rgba(0, 0, 0, 0.1);
    text-align: center;
    border: 1px solid #dee2e6;
}
h1, h2, h3 { color: black; }
label, .stMultiSelect label {
    color: black !important;
    font-weight: bold !important;
    font-size: 21px !important;
}
div.stDownloadButton > button {
    background-color: #007bff !important;
    color: white !important;
    font-size: 25px !important;
    font-weight: bold !important;
    border-radius: 10px !important;
}
.detected-text {
    color: #007bff;
    font-size: 21px;
    font-weight: bold;
}
.validation-text {
    color: #28a745;
    font-size: 21px;
    font-weight: bold;
}
.ai-explain-title {
    color: #6f42c1;
    font-size: 26px;
    font-weight: bold;
    margin-top: 20px;
}
.ai-explain-text {
    color: #495057;
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
        # Use enhanced detection and validation
        detection_result = EnhancedVersionChecker.detect_stix_full(file_path)
        validation_result = EnhancedValidator.validate_stix_detailed(file_path)
        
        version = detection_result["version"]
        valid = validation_result["is_valid"]
        
        # Display enhanced results
        if valid:
            msg = f"✅ Valid STIX {version} ({detection_result['format']}) - {detection_result['object_count']} objects"
        else:
            msg = f"⚠️ STIX {version} with {validation_result['error_count']} errors, {validation_result['warning_count']} warnings"
        
        st.markdown(f"<div class='validation-text'>{msg}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='detected-text'>Detected: {version} | Size: {detection_result['file_size_kb']:.1f}KB | Bundle: {'Yes' if detection_result['is_bundle'] else 'No'}</div>", unsafe_allow_html=True)

        if not valid:
            st.warning(f"Validation issues found - {validation_result['error_count']} errors, {validation_result['warning_count']} warnings")
            with st.expander("View Validation Details"):
                if validation_result["errors"]:
                    st.error("**Errors:**")
                    for error in validation_result["errors"][:3]:  # Show first 3 errors
                        st.write(f"• {error.get('message', 'Unknown error')}")
                if validation_result["warnings"]:
                    st.warning("**Warnings:**")
                    for warning in validation_result["warnings"][:3]:  # Show first 3 warnings
                        st.write(f"• {warning.get('message', 'Unknown warning')}")

        # Check if conversion to STIX 2.1 is needed
        needs_conversion = "2.1" not in str(version)
        if needs_conversion:
            st.info(f"File is {version}. Convert to STIX 2.1 for full graph visualization.")
            if st.button("🔄 Convert to STIX 2.1"):
                with st.spinner("Converting to STIX 2.1..."):
                    conversion_result = STIXConverter.convert_to_2_1(
                        file_path,
                        version,
                        detection_result['format']
                    )
                    
                    if conversion_result["success"]:
                        st.success("✅ Converted to STIX 2.1!")
                        data = conversion_result["converted_data"]
                        st.rerun()
                    else:
                        st.error(f"❌ Conversion failed: {conversion_result['message']}")
        
        # Load data for analysis
        if "2.1" in str(version):
            cti_data = convert_to_common_cti(file_path)
            with open(file_path, encoding='utf-8') as f:
                data = json.load(f)
        else:
            st.info("Convert to STIX 2.1 to proceed with analysis and visualization.")
            st.stop()

    # -------- STIX 1 XML --------
    elif file_ext == ".xml":
        # Use enhanced detection for XML files too
        detection_result = EnhancedVersionChecker.detect_stix_full(file_path)
        st.success(f"STIX 1.x XML detected - {detection_result['object_count']} objects, {detection_result['file_size_kb']:.1f}KB")
        
        # Automatically convert STIX 1.x to 2.1
        with st.spinner("Converting STIX 1.x to 2.1..."):
            conversion_result = STIXConverter.convert_to_2_1(
                file_path,
                detection_result.get("version"),
                detection_result.get("format")
            )
            
            if conversion_result["success"]:
                st.success("✅ Automatically converted to STIX 2.1!")
                data = conversion_result["converted_data"]
                cti_data = [{"description": "STIX 1.x converted to 2.1", "confidence": 50}]
            else:
                st.error(f"❌ Conversion failed: {conversion_result['message']}")
                st.stop()
    else:
        st.error("Unsupported file type")
        st.stop()

    # ---------- PRECISE THREAT TYPE ----------
    objects = data.get("objects", [])
    precise_type = derive_precise_threat_type(objects)

    desc = cti_data[0].get("description", "")

    if precise_type:
        threat_type = precise_type
    else:
        threat_type, _ = classify_threat(desc)

    # Use threat assessment for credibility
    assessment_result = analyze_bundle(data)
    score = assessment_result["score"]
    level = assessment_result["rating"]
    
    # Save analysis results to storage if we have shared file
    if "shared_stix_name" in st.session_state and st.session_state.shared_stix_name:
        if "storage" not in st.session_state:
            from modules.storage import STIXStorage
            st.session_state.storage = STIXStorage()
        
        # Find or create file_id for this file
        files = st.session_state.storage.list_files()
        file_id = None
        for file_meta in files:
            if file_meta.get('original_filename') == st.session_state.shared_stix_name:
                file_id = file_meta.get('file_id')
                break
        
        if file_id:
            # Save dashboard analysis results
            dashboard_results = {
                "threat_type": threat_type,
                "credibility_score": score,
                "credibility_rating": level,
                "assessment_details": assessment_result,
                "analyzed_at": str(datetime.now())
            }
            st.session_state.storage.save_analysis_result(file_id, "dashboard_analysis", dashboard_results)

    # ---------- OVERVIEW CARDS ----------
    st.markdown("## Threat Overview")
    c1, c2 = st.columns(2)
    c1.markdown(f"<div class='card'><h3>Threat Type</h3><h1>{threat_type}</h1></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='card'><h3>Credibility Score</h3><h1>{score} ({level})</h1></div>", unsafe_allow_html=True)

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
        net = Network(height="750px", width="100%", bgcolor="white", font_color="black")
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
    st.markdown(f"<div class='ai-explain-text'><b>Threat Assessment:</b> {threat_type} with credibility score {score} ({level})</div>", unsafe_allow_html=True)

else:
    st.info("Upload a STIX file to begin.")
