"""
Threat Assessment Page
Converts STIX bundles to 2.1 and applies threat credibility assessment
"""
import streamlit as st
import tempfile
import json
from pathlib import Path
from uuid import uuid4

# Import modules
from modules.converter import STIXConverter
from modules.enhanced_detector import EnhancedVersionChecker
from modules.storage import STIXStorage

# Import threat assessment functions
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from threat_assessment import analyze_bundle

# Page config
st.set_page_config(
    page_title="Threat Assessment",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styling
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(145deg, #1f1035, #140a24);
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 0 15px rgba(155, 89, 182, 0.3);
        margin: 10px 0;
    }
    .success-card {
        background: linear-gradient(145deg, #0d2818, #0a1810);
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #2ecc71;
        margin: 10px 0;
    }
    .warning-card {
        background: linear-gradient(145deg, #2d1f0d, #1a1208);
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #f39c12;
        margin: 10px 0;
    }
    .error-card {
        background: linear-gradient(145deg, #2d0d0d, #1a0808);
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #e74c3c;
        margin: 10px 0;
    }
    h1, h2, h3 { color: #c084fc; }
    .stButton>button { background-color: #7c3aed; color: white; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "threat_file_path" not in st.session_state:
    st.session_state.threat_file_path = None
if "threat_converted_data" not in st.session_state:
    st.session_state.threat_converted_data = None
if "threat_assessment_result" not in st.session_state:
    st.session_state.threat_assessment_result = None
if "threat_storage" not in st.session_state:
    st.session_state.threat_storage = STIXStorage()

def reset_threat_session():
    """Reset threat assessment session data"""
    st.session_state.threat_file_path = None
    st.session_state.threat_converted_data = None
    st.session_state.threat_assessment_result = None

# Header
st.markdown("## 🛡️ Threat Assessment & Credibility Analysis")
st.markdown("Upload any STIX bundle version - it will be converted to STIX 2.1 and analyzed for threat credibility.")
st.divider()

# Sidebar - File Upload
with st.sidebar:
    st.markdown("### 📁 STIX Bundle Source")
    
    # Check if file shared from dashboard
    if "shared_stix_bytes" in st.session_state and st.session_state.shared_stix_bytes:
        st.success("✅ Using file from Dashboard")
        st.caption(f"File: {st.session_state.shared_stix_name}")
        
        # Create temp file from shared bytes
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(st.session_state.shared_stix_name).suffix) as tmp:
            tmp.write(st.session_state.shared_stix_bytes)
            st.session_state.threat_file_path = tmp.name
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Analyze", key="analyze_threat", use_container_width=True):
                st.rerun()
        with col2:
            if st.button("🗑️ Clear", key="clear_threat", use_container_width=True):
                reset_threat_session()
                st.session_state.shared_stix_bytes = None
                st.session_state.shared_stix_name = None
                st.rerun()
    else:
        st.info("Upload a STIX bundle for threat assessment")
        
        uploaded_file = st.file_uploader(
            "Choose STIX file (JSON/XML)",
            type=["json", "xml"],
            accept_multiple_files=False,
            help="Supports STIX 1.x (XML) and STIX 2.0/2.1 (JSON)"
        )
        
        if uploaded_file:
            file_bytes = uploaded_file.getvalue()
            st.session_state.shared_stix_bytes = file_bytes
            st.session_state.shared_stix_name = uploaded_file.name
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp:
                tmp.write(file_bytes)
                st.session_state.threat_file_path = tmp.name
            
            st.success(f"✅ Uploaded: {uploaded_file.name}")
            st.info(f"Size: {uploaded_file.size / 1024:.2f} KB")
            
            if st.button("🔍 Analyze", key="analyze_threat", use_container_width=True):
                st.rerun()

# Main content
if st.session_state.threat_file_path and Path(st.session_state.threat_file_path).exists():
    
    # Step 1: Version Detection
    st.markdown("### 🎯 Step 1: Version Detection & Conversion")
    
    with st.spinner("🔄 Detecting STIX version..."):
        detection_result = EnhancedVersionChecker.detect_stix_full(st.session_state.threat_file_path)
    
    # Display detection results
    det_col1, det_col2, det_col3 = st.columns(3)
    with det_col1:
        st.metric("📌 Version", detection_result["version"])
    with det_col2:
        st.metric("📄 Format", detection_result["format"])
    with det_col3:
        st.metric("📦 Objects", detection_result["object_count"])
    
    # Step 2: Convert to STIX 2.1
    st.markdown("### 🔄 Step 2: Convert to STIX 2.1")
    
    if st.button("🚀 Convert to STIX 2.1", key="convert_threat", use_container_width=True):
        with st.spinner("Converting to STIX 2.1..."):
            conversion_result = STIXConverter.convert_to_2_1(
                st.session_state.threat_file_path,
                detection_result.get("version"),
                detection_result.get("format")
            )
            
            if conversion_result["success"]:
                st.session_state.threat_converted_data = conversion_result["converted_data"]
                st.success(f"✅ {conversion_result['message']}")
                
                # Save converted data
                file_id = str(uuid4())
                filename = st.session_state.shared_stix_name or "unknown_file"
                
                st.session_state.threat_storage.save_converted_stix(
                    stix_data=conversion_result["converted_data"],
                    original_filename=filename,
                    metadata={
                        "original_version": detection_result.get("version"),
                        "original_format": detection_result.get("format"),
                        "file_size_kb": detection_result.get("file_size_kb")
                    }
                )
                st.info(f"💾 Saved with ID: {file_id}")
            else:
                st.error(f"❌ {conversion_result['message']}")
    
    st.divider()
    
    # Step 3: Threat Assessment
    if st.session_state.threat_converted_data:
        st.markdown("### 🛡️ Step 3: Threat Credibility Assessment")
        
        if st.button("🔍 Run Threat Assessment", key="run_assessment", use_container_width=True):
            with st.spinner("🔄 Analyzing threat credibility..."):
                try:
                    assessment_result = analyze_bundle(st.session_state.threat_converted_data)
                    st.session_state.threat_assessment_result = assessment_result
                    st.success("✅ Threat assessment completed!")
                except Exception as e:
                    st.error(f"❌ Assessment failed: {str(e)}")
        
        # Display assessment results
        if st.session_state.threat_assessment_result:
            result = st.session_state.threat_assessment_result
            
            # Overview metrics
            st.markdown("#### 📊 Assessment Overview")
            
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            with metric_col1:
                score_color = "🟢" if result["score"] >= 75 else "🟡" if result["score"] >= 45 else "🔴"
                st.metric("Credibility Score", f"{score_color} {result['score']}/100")
            
            with metric_col2:
                rating_color = {"HIGH": "🟢", "MEDIUM": "🟡", "LOW": "🔴"}
                st.metric("Rating", f"{rating_color.get(result['rating'], '⚪')} {result['rating']}")
            
            with metric_col3:
                total_factors = len(result["reasons"])
                st.metric("Assessment Factors", total_factors)
            
            st.divider()
            
            # Detailed analysis
            st.markdown("#### 🔍 Detailed Analysis")
            
            # Categorize reasons
            positives = [r for r in result["reasons"] if r.startswith("✔")]
            warnings = [r for r in result["reasons"] if r.startswith("⚠")]
            negatives = [r for r in result["reasons"] if r.startswith("❌")]
            
            analysis_col1, analysis_col2 = st.columns(2)
            
            with analysis_col1:
                if positives:
                    st.markdown("##### ✅ Positive Factors")
                    for positive in positives:
                        st.markdown(f"- {positive}")
                
                if warnings:
                    st.markdown("##### ⚠️ Warnings")
                    for warning in warnings:
                        st.markdown(f"- {warning}")
            
            with analysis_col2:
                if negatives:
                    st.markdown("##### ❌ Critical Issues")
                    for negative in negatives:
                        st.markdown(f"- {negative}")
                
                # Summary
                st.markdown("##### 📝 Summary")
                st.info(result["summary"])
            
            st.divider()
            
            # JSON Output
            st.markdown("#### 📄 JSON Output")
            
            output_col1, output_col2 = st.columns(2)
            
            with output_col1:
                st.markdown("##### 🔍 Explainable Form")
                explainable_output = {
                    "assessment_summary": {
                        "credibility_score": result["score"],
                        "credibility_rating": result["rating"],
                        "summary": result["summary"]
                    },
                    "detailed_analysis": {
                        "positive_factors": positives,
                        "warning_factors": warnings,
                        "critical_issues": negatives
                    },
                    "metadata": {
                        "total_assessment_factors": len(result["reasons"]),
                        "original_version": detection_result.get("version"),
                        "converted_to": "STIX 2.1"
                    }
                }
                st.json(explainable_output)
            
            with output_col2:
                st.markdown("##### 📊 Raw JSON")
                st.json(result)
            
            # Download options
            st.markdown("#### 📥 Download Results")
            
            download_col1, download_col2, download_col3 = st.columns(3)
            
            with download_col1:
                # Download explainable JSON
                explainable_json = json.dumps(explainable_output, indent=2)
                st.download_button(
                    "📥 Download Explainable JSON",
                    explainable_json,
                    file_name="threat_assessment_explainable.json",
                    mime="application/json"
                )
            
            with download_col2:
                # Download raw JSON
                raw_json = json.dumps(result, indent=2)
                st.download_button(
                    "📥 Download Raw JSON",
                    raw_json,
                    file_name="threat_assessment_raw.json",
                    mime="application/json"
                )
            
            with download_col3:
                # Download converted STIX 2.1
                converted_json = json.dumps(st.session_state.threat_converted_data, indent=2)
                st.download_button(
                    "📥 Download STIX 2.1",
                    converted_json,
                    file_name="converted_stix_2_1.json",
                    mime="application/json"
                )

else:
    # No file uploaded
    st.info("""
        👈 **Getting Started:**
        
        1. Upload a STIX bundle (any version) using the sidebar
        2. The system will detect the version and format
        3. Convert to STIX 2.1 for standardized analysis
        4. Run threat credibility assessment
        5. View results in both explainable and JSON formats
        
        **Supported Formats:**
        - STIX 1.x (XML files)
        - STIX 2.0 (JSON files) 
        - STIX 2.1 (JSON files)
        
        **Assessment Features:**
        - Source credibility analysis
        - IOC validation via VirusTotal
        - Metadata quality assessment
        - Relationship analysis
        - Timeline validation
    """)

# Footer
st.divider()
st.markdown("""
    <div style='text-align: center; color: #888; font-size: 12px;'>
    🛡️ Threat Assessment Engine | Converts any STIX version to 2.1 | Built with Streamlit
    </div>
""", unsafe_allow_html=True)