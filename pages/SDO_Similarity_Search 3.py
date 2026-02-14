import streamlit as st
from pyvis.network import Network
import tempfile
import json
import os
from collections import defaultdict

# ── Your modules ─────────────────────────────────────────────────────────────
from modules.SDO_graphs import graph, get_ego_graph

# ── Pipeline odules ─────────────────────────────────────────────────────────
from modules.bundles_2_csv import stix_json_to_csv
from modules.summary_generator import summarize_csv
from modules.clean_csv import clean_csv
from modules.similarity_search import generate_similarity_json
# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="STIX Bundle → Similarity → Graph Explorer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INIT (CRITICAL)
# ─────────────────────────────────────────────────────────────────────────────
if "similarity_map" not in st.session_state:
    st.session_state.similarity_map = None

if "selectable_ids" not in st.session_state:
    st.session_state.selectable_ids = []

if "pipeline_done" not in st.session_state:
    st.session_state.pipeline_done = False

# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE WRAPPER
# ─────────────────────────────────────────────────────────────────────────────
class BundleToSummaryPipeline:
    def __init__(self, bundle_path: str):
        self.bundle_path = bundle_path

    def run(self, top_k=5):
        csv_path = stix_json_to_csv(self.bundle_path)
        summary_csv = summarize_csv(csv_path)
        cleaned_csv = clean_csv(summary_csv)
        if cleaned_csv is None:
            return None
        return generate_similarity_json(cleaned_csv, top_k=top_k)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR – INPUT
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("STIX Similarity Explorer")

    mode = st.radio(
        "Bundle source",
        ["Use existing similarity JSON", "Process new STIX bundle"],
        index=0
    )

    similarity_json_path = None

    if mode == "Process new STIX bundle":
        bundle_file = st.file_uploader(
            "Upload STIX 2.x JSON bundle",
            type=["json"]
        )

        top_k = st.number_input("Top K similar objects", 1, 20, 5)
        process_btn = st.button("Process Bundle", type="primary")

        if process_btn and bundle_file:
            os.makedirs("temp_bundles", exist_ok=True)
            bundle_path = os.path.join("temp_bundles", bundle_file.name)

            with open(bundle_path, "wb") as f:
                f.write(bundle_file.getvalue())

            with st.spinner("Running similarity pipeline…"):
                pipeline = BundleToSummaryPipeline(bundle_path)
                sim_path = pipeline.run(top_k=top_k)

            if sim_path and os.path.exists(sim_path):
                with open(sim_path, encoding="utf-8") as f:
                    st.session_state.similarity_map = json.load(f)

                st.session_state.selectable_ids = sorted(
                    st.session_state.similarity_map.keys()
                )
                st.session_state.pipeline_done = True

                st.success("Similarity data ready for visualization")
            else:
                st.error("Pipeline failed")

    else:
        default_path = "C:/Users/nitk/Downloads/stix-dashboard/stix-ai-dashboard/modules/stix_bundle-18similar_ids.json"
        similarity_json_path = st.text_input(
            "Path to similarity JSON",
            value=default_path
        )

        if similarity_json_path and os.path.isfile(similarity_json_path):
            with open(similarity_json_path, encoding="utf-8") as f:
                st.session_state.similarity_map = json.load(f)

            st.session_state.selectable_ids = sorted(
                st.session_state.similarity_map.keys()
            )
            print(st.session_state.selectable_ids)  #debug statement 
            st.session_state.pipeline_done = True

# ─────────────────────────────────────────────────────────────────────────────
# HARD GATE
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.pipeline_done:
    st.info("Upload a bundle or load a similarity JSON to start.")
    st.stop()

similarity_map = st.session_state.similarity_map
selectable_ids = st.session_state.selectable_ids

# ─────────────────────────────────────────────────────────────────────────────
# GROUP IDS BY TYPE
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def group_by_type(ids):
    by_type = defaultdict(list)
    for obj_id in ids:
        if obj_id in graph:
            by_type[graph.nodes[obj_id].get("type", "unknown")].append(obj_id)
    return dict(by_type)

nodes_by_type = group_by_type(tuple(selectable_ids))
print(nodes_by_type)

# ─────────────────────────────────────────────────────────────────────────────
# PYVIS RENDER (CACHED)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def render_cached(node_id):
    ego = get_ego_graph(graph, node_id)
    net = Network(
        height="520px",
        bgcolor="#0f172a",
        font_color="white",
        directed=True,
        cdn_resources="in_line"
    )

    for n, d in ego.nodes(data=True):
        net.add_node(
            n,
            label=d.get("name", n[:14]),
            title=json.dumps(d, indent=2),
            color="#facc15" if n == node_id else "#60a5fa"
        )

    for s, t, d in ego.edges(data=True):
        net.add_edge(s, t, title=d.get("relationship", ""))

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
    net.write_html(tmp.name)
    return tmp.name

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR – GRAPH CONTROLS
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.subheader("Graph Controls")

    stix_type = st.selectbox(
        "STIX Type",
        options=[""] + sorted(nodes_by_type.keys())
    )

    selected_id = None
    if stix_type:
        selected_id = st.selectbox(
            "Object",
            options=nodes_by_type[stix_type]
        )

# ─────────────────────────────────────────────────────────────────────────────
# MAIN VIEW
# ─────────────────────────────────────────────────────────────────────────────
st.title("STIX Similar Objects – Ego Graph Explorer")

if not selected_id:
    st.warning("Select a STIX object to visualize")
    st.stop()

st.subheader(f"Selected: {selected_id}")

html = render_cached(selected_id)
st.components.v1.html(open(html).read(), height=600, scrolling=True)

with st.expander("Selected object JSON"):
    st.json(graph.nodes[selected_id])

st.divider()

st.subheader("Most similar objects")

for i, sim_id in enumerate(similarity_map.get(selected_id, []), 1):
    if sim_id not in graph or sim_id == selected_id:
        continue

    st.markdown(f"### {i}. {sim_id}")
    sim_html = render_cached(sim_id)
    st.components.v1.html(open(sim_html).read(), height=500, scrolling=True)

    with st.expander(f"JSON – {sim_id}"):
        st.json(graph.nodes[sim_id])

st.caption("STIX bundle → similarity → ego graph exploration")
