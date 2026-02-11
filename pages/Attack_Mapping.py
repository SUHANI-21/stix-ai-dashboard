"""
Malware Technique Inference Page
Displays results from the end-to-end STIX pipeline
"""

import streamlit as st
import json
import tempfile
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.run_pipeline import run_pipeline

st.set_page_config(page_title="Malware Inference Pipeline", layout="wide")

# Style
st.markdown("""
<style>
.stApp {
    background-color: white;
    color: black;
}
.stSidebar {
    background-color: #f8f9fa;
}
.stSelectbox label, .stTextInput label, .stNumberInput label {
    color: black !important;
}
.stMarkdown {
    color: black;
}
.metric-card {
    background: #f8f9fa;
    padding: 20px; border-radius: 15px;
    box-shadow: 0 0 15px rgba(0, 0, 0, 0.1);
    border: 1px solid #dee2e6;
}
h1, h2, h3 { color: black; }
.success { color: #28a745; }
.warning { color: #ffc107; }
.inference-box {
    background: #f8f9fa;
    padding: 15px; border-radius: 10px;
    border-left: 4px solid #007bff;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

st.markdown("# 🔬 Malware Technique Inference Pipeline")
st.markdown("Convert STIX → Extract Malware → LLM Profile → Predict Techniques")
st.markdown("---")

# Check if file shared from dashboard
if "shared_stix_bytes" in st.session_state and st.session_state.shared_stix_bytes:
    st.success("✅ Using file from Dashboard")
    st.caption(f"File: {st.session_state.shared_stix_name}")
    
    # Add button to upload different file
    if st.button("📁 Upload Different File"):
        st.session_state.shared_stix_bytes = None
        st.session_state.shared_stix_name = None
        st.rerun()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(st.session_state.shared_stix_name).suffix) as tmp:
        tmp.write(st.session_state.shared_stix_bytes)
        file_path = tmp.name
    
    uploaded_file = type('obj', (object,), {'name': st.session_state.shared_stix_name})()
else:
    # File uploader
    uploaded_file = st.file_uploader("Upload STIX file (JSON or XML)", type=["json", "xml"])
    
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp:
            tmp.write(uploaded_file.read())
            file_path = tmp.name
    else:
        uploaded_file = None

if uploaded_file:
    
    # Run pipeline
    with st.spinner("🔄 Running pipeline..."):
        try:
            result = run_pipeline(file_path)
            
            # Success message
            st.success("✅ Pipeline completed successfully!")
            
            # Save analysis results to storage
            if "storage" not in st.session_state:
                from modules.storage import STIXStorage
                st.session_state.storage = STIXStorage()
            
            files = st.session_state.storage.list_files()
            file_id = None
            for file_meta in files:
                if file_meta.get('original_filename') == uploaded_file.name:
                    file_id = file_meta.get('file_id')
                    break
            
            if file_id:
                st.session_state.storage.save_analysis_result(file_id, "attack_mapping", result)
            
            # Tabs for different views
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Summary", "🎯 Inference", "📦 Bundle", "📄 Original"])
            
            with tab1:
                st.markdown("### Pipeline Summary")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    version = result.get("formatted", {}).get("Version", "Unknown")
                    st.metric("STIX Version", version)
                
                with col2:
                    obj_count = result.get("formatted", {}).get("Object Count", 0)
                    st.metric("Total Objects", obj_count)
                
                with col3:
                    file_size = result.get("formatted", {}).get("File Size (KB)", "Unknown")
                    st.metric("File Size", file_size)
                
                with col4:
                    status = result.get("formatted", {}).get("Status", "Unknown")
                    st.metric("Status", status)
            
            with tab2:
                st.markdown("### 🎯 Inference Results")
                
                # Find inference object in bundle
                inference_obj = None
                for obj in result["bundle"].get("objects", []):
                    if obj.get("type") == "x-malware-technique-inference":
                        inference_obj = obj
                        break
                
                if inference_obj:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        llm_gen = inference_obj.get("llm_generated", False)
                        status = "🟢 LLM Generated" if llm_gen else "🟡 Feature-Based"
                        st.info(status)
                        
                        st.markdown("#### Model Info")
                        st.write(f"**Model**: {inference_obj.get('model', 'N/A')}")
                        st.write(f"**ID**: {inference_obj.get('id', 'N/A')}")
                        st.write(f"**Created**: {inference_obj.get('created', 'N/A')}")
                    
                    with col2:
                        techniques = inference_obj.get("output", [])
                        st.markdown("#### MITRE ATT&CK Techniques")
                        st.metric("Predicted Techniques", len(techniques))
                    
                    # Techniques list
                    st.markdown("#### Techniques Details")
                    cols = st.columns(3)
                    for idx, tech in enumerate(techniques):
                        with cols[idx % 3]:
                            st.button(f"🎯 {tech}", key=f"tech_{idx}", disabled=True)
                    
                    # LLM Profile
                    st.markdown("#### LLM/Feature Profile")
                    profile = inference_obj.get("llm_profile", "")
                    st.text_area("Profile Text", profile, height=150, disabled=True)
                else:
                    st.warning("No inference object found in bundle")
            
            with tab3:
                st.markdown("### 📦 Complete STIX Bundle")
                st.json(result["bundle"], expanded=False)
            
            with tab4:
                st.markdown("### 📄 Original STIX File")
                
                # Find original STIX object
                original_obj = None
                for obj in result["bundle"].get("objects", []):
                    if obj.get("type") == "x-original-stix":
                        original_obj = obj
                        break
                
                if original_obj:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**File**: {original_obj.get('file_name', 'N/A')}")
                    with col2:
                        st.download_button(
                            "⬇️ Download Original",
                            original_obj.get("raw", ""),
                            file_name=original_obj.get("file_name", "original.json"),
                            mime="application/json"
                        )
                    
                    st.text_area(
                        "Original Content",
                        original_obj.get("raw", ""),
                        height=200,
                        disabled=True
                    )
                else:
                    st.warning("No original STIX object found")
            
            # Export results
            st.markdown("---")
            st.markdown("### 💾 Export Results")
            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    "📥 Download Full Output (JSON)",
                    json.dumps(result, indent=2),
                    file_name="pipeline_output.json",
                    mime="application/json"
                )
            
            with col2:
                st.download_button(
                    "📥 Download Bundle Only (JSON)",
                    json.dumps(result["bundle"], indent=2),
                    file_name="stix_bundle_with_inference.json",
                    mime="application/json"
                )
        
        except FileNotFoundError as e:
            st.error(f"❌ File not found: {e}")
        except Exception as e:
            st.error(f"❌ Error: {e}")
            st.exception(e)
else:
    st.info("👆 Upload a STIX file to begin")
    
    # Show example structure
    with st.expander("📖 Expected Output Structure"):
        example = {
            "bundle": {
                "type": "bundle",
                "objects": [
                    {"type": "malware", "id": "malware--xxx", "name": "ExampleMalware"},
                    {"type": "x-malware-technique-inference", "output": ["T1016", "T1082"], "llm_generated": True},
                    {"type": "x-original-stix", "file_name": "original.json"}
                ]
            },
            "formatted": {"Version": "STIX 2.1", "Object Count": 3, "Status": "✅ Valid"}
        }
        st.json(example)
