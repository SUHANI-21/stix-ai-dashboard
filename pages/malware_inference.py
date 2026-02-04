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
.stApp { background: radial-gradient(circle at top left, #1a0b2e, #0d0d1a); color: #e0e0ff; }
.metric-card {
    background: linear-gradient(145deg, #1f1035, #140a24);
    padding: 20px; border-radius: 15px;
    box-shadow: 0 0 15px rgba(155, 89, 182, 0.4);
}
h1, h2, h3 { color: #c084fc; }
.success { color: #2ecc71; }
.warning { color: #f39c12; }
.inference-box {
    background: linear-gradient(145deg, #2d1b4e, #1a0f2e);
    padding: 15px; border-radius: 10px;
    border-left: 4px solid #c084fc;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

st.markdown("# 🔬 Malware Technique Inference Pipeline")
st.markdown("Convert STIX → Extract Malware → LLM Profile → Predict Techniques")
st.markdown("---")

# File uploader
uploaded_file = st.file_uploader("Upload STIX file (JSON or XML)", type=["json", "xml"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp:
        tmp.write(uploaded_file.read())
        file_path = tmp.name
    
    # Run pipeline
    with st.spinner("🔄 Running pipeline..."):
        try:
            result = run_pipeline(file_path)
            
            # Success message
            st.success("✅ Pipeline completed successfully!")
            
            # Tabs for different views
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Summary", "🎯 Inference", "📦 Bundle", "📄 Original"])
            
            with tab1:
                st.markdown("### Pipeline Summary")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("STIX Version", result["formatted"]["Version"])
                
                with col2:
                    st.metric("Total Objects", result["formatted"]["Object Count"])
                
                with col3:
                    st.metric("File Size", result["formatted"]["File Size (KB)"])
                
                with col4:
                    st.metric("Status", result["formatted"]["Status"])
            
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
