import streamlit as st
import tempfile
import plotly.graph_objects as go
import json
from pyvis.network import Network
import streamlit.components.v1 as components

from modules.version_detector import detect_stix_version
from modules.validator import validate_stix
from modules.cti_converter import convert_to_common_cti
from modules.threat_classifier import classify_threat
from modules.credibility_assessor import assess_credibility
from modules.attack_type_mapper import map_attack_type

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="AI CTI Dashboard", layout="wide")

# ---------- PURPLE SOC THEME ----------
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
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("## 🛡️ AI-Powered Cyber Threat Intelligence Dashboard")
st.markdown("Upload STIX threat intelligence data and let AI analyze risk, relationships, and credibility.")
st.markdown("---")

# ---------- SIDEBAR ----------
st.sidebar.markdown("## ⚙️ Control Panel")
uploaded_file = st.sidebar.file_uploader("Choose a STIX file", type=["json", "xml"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(uploaded_file.read())
        file_path = tmp.name

    st.header("🔍 STIX Processing Pipeline")

    version = detect_stix_version(file_path)
    valid, message = validate_stix(file_path)

    st.success(message)
    st.write("**Detected Version:**", version)

    if valid:
        cti_data = convert_to_common_cti(file_path)

        if len(cti_data) > 0:
            desc = cti_data[0].get("description") or "unknown threat activity"
            confidence = cti_data[0].get("confidence", 50)

            threat_type, prob = classify_threat(desc)
            score, level = assess_credibility(confidence, prob)

            # ---------- PRECISE ATT&CK TYPE ----------
            with open(file_path) as f:
                data = json.load(f)

            technique_ids = []
            for obj in data.get("objects", []):
                if obj.get("type") == "attack-pattern":
                    for ref in obj.get("external_references", []):
                        if ref.get("source_name") == "mitre-attack":
                            technique_ids.append(ref.get("external_id"))

            attack_types = map_attack_type(technique_ids)

            # ---------- OVERVIEW CARDS ----------
            st.markdown("## 🛡️ Threat Overview")
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"<div class='card'><h3>Threat Type</h3><h1>{threat_type}</h1></div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='card'><h3>AI Probability</h3><h1>{prob}%</h1></div>", unsafe_allow_html=True)
            c3.markdown(f"<div class='card'><h3>Credibility Score</h3><h1>{score} ({level})</h1></div>", unsafe_allow_html=True)

            st.markdown("### 🎯 Precise ATT&CK Attack Types")
            st.write(", ".join(attack_types))

            st.markdown("---")

            # ---------- GAUGE ----------
            st.markdown("### 📊 Threat Probability")
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=prob,
                title={'text': "Threat Probability"},
                gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#c084fc"}}
            ))
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")

            # ---------- THREAT RELATIONSHIP GRAPH ----------
            st.markdown("### 🌐 Threat Relationship Graph")

            net = Network(height="750px", width="100%", bgcolor="#0d0d1a", font_color="white")

            net.set_options("""
            var options = {
              "physics": {
                "barnesHut": {
                  "gravitationalConstant": -5000,
                  "springLength": 220,
                  "springConstant": 0.02
                }
              },
              "interaction": { "hover": true },
              "nodes": { "shape": "dot", "size": 14, "font": { "size": 12, "color": "#ffffff" } },
              "edges": { "color": { "color": "#aaaaaa" }, "smooth": { "type": "dynamic" } }
            }
            """)

            color_map = {
                "attack-pattern": "#ff4b5c",
                "malware": "#ff9f43",
                "tool": "#1dd1a1",
                "intrusion-set": "#54a0ff",
                "campaign": "#5f27cd"
            }

            objects = data.get("objects", [])
            related_ids = set()

            for obj in objects:
                if obj.get("type") == "relationship":
                    related_ids.add(obj.get("source_ref"))
                    related_ids.add(obj.get("target_ref"))

            MAX_NODES = 120
            added_nodes = set()

            for obj in objects:
                obj_id = obj.get("id")
                obj_type = obj.get("type")

                if obj_id in related_ids and obj_id not in added_nodes and len(added_nodes) < MAX_NODES:
                    name = obj.get("name", obj_type)
                    color = color_map.get(obj_type, "#aaaaaa")
                    net.add_node(obj_id, label=name[:25], title=f"{name} ({obj_type})", color=color)
                    added_nodes.add(obj_id)

            for obj in objects:
                if obj.get("type") == "relationship":
                    src = obj.get("source_ref")
                    tgt = obj.get("target_ref")
                    if src in added_nodes and tgt in added_nodes:
                        net.add_edge(src, tgt)

            graph_path = "stix_graph.html"
            net.save_graph(graph_path)

            with open(graph_path, "r", encoding="utf-8") as f:
                html = f.read()

            components.html(html, height=750)

            st.markdown("---")

            # ---------- DETAILS ----------
            st.markdown("### 🧠 Threat Intelligence Details")
            st.write("**Description:**", desc)
            st.write("**Source Confidence:**", confidence)
            st.write("**AI Assessment:**", f"{threat_type} with {prob}% probability")

        else:
            st.warning("No CTI objects found in STIX file.")
else:
    st.info("Please upload a STIX file to begin analysis.")
