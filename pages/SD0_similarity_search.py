import streamlit as st
from pyvis.network import Network
import tempfile
import json
import os
from collections import defaultdict

# ── Your modules ─────────────────────────────────────────────────────────────
from modules.SDO_graphs import build_stix_graph, get_ego_graph

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

if "bundle_graph" not in st.session_state:
    st.session_state.bundle_graph = None
    
if "bundle_path" not in st.session_state:
    st.session_state.bundle_path = None

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
                
                # Build graph from the uploaded bundle
                with st.spinner("Building graph from bundle…"):
                    st.session_state.bundle_graph = build_stix_graph(os.path.dirname(bundle_path))
                    st.session_state.bundle_path = bundle_path

                st.success("Similarity data ready for visualization")
            else:
                st.error("Pipeline failed")

    else:
        default_path = r"E:\college\NITK Internship\stix_normalizer\stix_normalizer\stix_intelligence_analyzer\modules\stix_bundle-18similar_ids.json"
        similarity_json_path = st.text_input(
            "Path to similarity JSON",
            value=default_path
        )
        
        bundle_json_path = st.text_input(
            "Path to source STIX bundle (optional, for graph building)",
            value=""
        )

        if similarity_json_path and os.path.isfile(similarity_json_path):
            with open(similarity_json_path, encoding="utf-8") as f:
                st.session_state.similarity_map = json.load(f)

            st.session_state.selectable_ids = sorted(
                st.session_state.similarity_map.keys()
            )
            st.session_state.pipeline_done = True
            
            # Build graph from bundle if provided
            if bundle_json_path and os.path.isfile(bundle_json_path):
                with st.spinner("Building graph from bundle…"):
                    st.session_state.bundle_graph = build_stix_graph(os.path.dirname(bundle_json_path))
                    st.session_state.bundle_path = bundle_json_path

# ─────────────────────────────────────────────────────────────────────────────
# HARD GATE
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.pipeline_done or st.session_state.bundle_graph is None:
    st.info("📤 Upload a STIX bundle to start the similarity pipeline.")
    st.stop()

similarity_map = st.session_state.similarity_map
selectable_ids = st.session_state.selectable_ids

# Use bundle graph if available
graph = st.session_state.bundle_graph

# ─────────────────────────────────────────────────────────────────────────────
# GROUP IDS BY TYPE
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def group_by_type(ids):
    by_type = defaultdict(list)
    for obj_id in ids:
        if obj_id in graph:
            obj_type = graph.nodes[obj_id].get("type", "unknown")
            by_type[obj_type].append(obj_id)
        else:
            # Fallback: try to extract type from ID if not in graph
            try:
                obj_type = obj_id.split("--")[0]  # Extract type from STIX ID
                by_type[obj_type].append(obj_id)
            except:
                by_type["unknown"].append(obj_id)
    return dict(by_type) if by_type else {"No types found": []}

nodes_by_type = group_by_type(tuple(selectable_ids))
st.write(f"DEBUG: nodes_by_type = {nodes_by_type}")

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

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8")
    tmp.write(net.generate_html())
    tmp.close()
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
st.components.v1.html(open(html, encoding="utf-8").read(), height=600, scrolling=True)

with st.expander("Selected object JSON"):
    if selected_id in graph:
        st.json(graph.nodes[selected_id])
    else:
        # If not in graph, try to get from similarity_map
        st.warning(f"Object {selected_id} not in main graph. Showing from similarity data...")
        if selected_id in similarity_map:
            st.json(similarity_map[selected_id])

st.divider()

st.subheader("Most similar objects")

for i, sim_id in enumerate(similarity_map.get(selected_id, []), 1):
    if sim_id not in graph or sim_id == selected_id:
        continue

    st.markdown(f"### {i}. {sim_id}")
    sim_html = render_cached(sim_id)
    st.components.v1.html(open(sim_html, encoding="utf-8").read(), height=500, scrolling=True)

    with st.expander(f"JSON – {sim_id}"):
        st.json(graph.nodes[sim_id])

st.caption("STIX bundle → similarity → ego graph exploration")
