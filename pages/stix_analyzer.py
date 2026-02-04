"""
STIX Intelligence Analyzer - Version Detection & Validation
A dedicated page for analyzing STIX bundles with detailed version detection and validation
"""
import streamlit as st
import tempfile
from pathlib import Path

# Import our custom modules
from modules.enhanced_detector import EnhancedVersionChecker
from modules.enhanced_validator import EnhancedValidator
from modules.formatter import ResultFormatter
from modules.utils import FileManager, ErrorHandler
from modules.converter import STIXConverter


# ========== PAGE CONFIGURATION ==========
st.set_page_config(
    page_title="STIX Version Detection & Validation",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== STYLING ==========
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
    .error-card {
        background: linear-gradient(145deg, #2d0d0d, #1a0808);
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #e74c3c;
        margin: 10px 0;
    }
    .warning-card {
        background: linear-gradient(145deg, #2d1f0d, #1a1208);
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #f39c12;
        margin: 10px 0;
    }
    h1, h2, h3 { color: #c084fc; }
    .stButton>button { background-color: #7c3aed; color: white; }
</style>
""", unsafe_allow_html=True)

# ========== INITIALIZE SESSION STATE ==========
if "file_path" not in st.session_state:
    st.session_state.file_path = None
if "detection_result" not in st.session_state:
    st.session_state.detection_result = None
if "validation_result" not in st.session_state:
    st.session_state.validation_result = None
if "statistics" not in st.session_state:
    st.session_state.statistics = None
if "converted_data" not in st.session_state:
    st.session_state.converted_data = None


def reset_session_data():
    """Reset session data"""
    st.session_state.file_path = None
    st.session_state.detection_result = None
    st.session_state.validation_result = None
    st.session_state.statistics = None
    st.session_state.converted_data = None


# ========== HEADER ==========
st.markdown("## 🔍 STIX Version Detection & Validation")
st.markdown(
    "Upload a STIX bundle and get instant analysis of its version, format, and structural validity."
)
st.divider()

# ========== SIDEBAR - FILE UPLOAD ==========
# ========== SIDEBAR - FILE SOURCE ==========
with st.sidebar:
    st.markdown("### 📁 STIX File Source")

    # ✅ If Dashboard already uploaded a file, reuse it
    if "shared_stix_bytes" in st.session_state and st.session_state.shared_stix_bytes:

        st.success("✅ Using file uploaded in Dashboard")
        st.caption(f"Shared file: {st.session_state.shared_stix_name}")

        # Recreate temp file from shared bytes
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(st.session_state.shared_stix_name).suffix) as tmp:
            tmp.write(st.session_state.shared_stix_bytes)
            st.session_state.file_path = tmp.name

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔎 Analyze", key="analyze_btn", use_container_width=True):
                st.rerun()
        with col2:
            if st.button("🗑️ Clear", key="clear_btn", use_container_width=True):
                reset_session_data()
                st.session_state.shared_stix_bytes = None
                st.session_state.shared_stix_name = None
                st.rerun()

    else:
        st.info("No file from Dashboard yet. Upload here if needed.")

        uploaded_file = st.file_uploader(
            "Choose a STIX file (JSON or XML)",
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
                st.session_state.file_path = tmp.name

            st.success(f"✅ File uploaded: `{uploaded_file.name}`")
            st.info(f"File size: **{uploaded_file.size / 1024:.2f} KB**")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔎 Analyze", key="analyze_btn", use_container_width=True):
                    st.rerun()
            with col2:
                if st.button("🗑️ Clear", key="clear_btn", use_container_width=True):
                    reset_session_data()
                    st.session_state.shared_stix_bytes = None
                    st.session_state.shared_stix_name = None
                    st.rerun()



# ========== MAIN CONTENT ==========
if st.session_state.file_path and Path(st.session_state.file_path).exists():
    
    # ========== STEP 1: DETECTION ==========
    st.markdown("### 🎯 Step 1: Version Detection")
    
    with st.spinner("🔄 Detecting STIX version..."):
        detection_result = EnhancedVersionChecker.detect_stix_full(
            st.session_state.file_path
        )
        st.session_state.detection_result = detection_result
    
    # Display detection results in columns
    det_col1, det_col2, det_col3 = st.columns(3)
    
    with det_col1:
        st.metric("📌 Version", detection_result["version"])
    
    with det_col2:
        st.metric("📄 Format", detection_result["format"])
    
    with det_col3:
        st.metric("📦 Bundle", "Yes ✅" if detection_result["is_bundle"] else "No ❌")
    
    # Additional metadata
    meta_col1, meta_col2 = st.columns(2)
    
    with meta_col1:
        st.metric("🔢 Object Count", detection_result["object_count"])
    
    with meta_col2:
        st.metric("📊 File Size (KB)", f"{detection_result['file_size_kb']:.2f}")
    
    if not detection_result["is_valid"]:
        st.warning("⚠️ File detected but structure may be invalid. Validation details below.")
    
    st.divider()
    
    # ========== STEP 2: VALIDATION ==========
    st.markdown("### ✅ Step 2: Structural Validation")
    
    with st.spinner("🔄 Validating STIX structure..."):
        validation_result = EnhancedValidator.validate_stix_detailed(
            st.session_state.file_path
        )
        st.session_state.validation_result = validation_result
    
    # Validation summary
    val_col1, val_col2, val_col3 = st.columns(3)
    
    with val_col1:
        status_emoji = "✅" if validation_result["is_valid"] else "❌"
        st.metric("Status", f"{status_emoji} {('Valid' if validation_result['is_valid'] else 'Invalid')}")
    
    with val_col2:
        st.metric("❌ Errors", validation_result["error_count"])
    
    with val_col3:
        st.metric("⚠️ Warnings", validation_result["warning_count"])
    
    # Detailed error and warning lists
    if validation_result["errors"] or validation_result["warnings"]:
        st.markdown("#### Issues Found")
        
        if validation_result["errors"]:
            with st.expander(f"❌ Errors ({len(validation_result['errors'])})"):
                for i, error in enumerate(validation_result["errors"], 1):
                    st.write(f"**Error {i}:** {error.get('message', 'Unknown error')}")
                    if error.get("location"):
                        st.caption(f"Location: {error['location']}")
        
        if validation_result["warnings"]:
            with st.expander(f"⚠️ Warnings ({len(validation_result['warnings'])})"):
                for i, warning in enumerate(validation_result["warnings"], 1):
                    st.write(f"**Warning {i}:** {warning.get('message', 'Unknown warning')}")
                    if warning.get("location"):
                        st.caption(f"Location: {warning['location']}")
    else:
        st.success("🎉 No issues found! Your STIX file is structurally valid.")
    
    st.divider()
    
    # ========== STEP 2B: CONVERSION ==========
    st.markdown("### 🔄 Step 2B: Convert to STIX 2.1")
    
    if st.button("🚀 Convert to STIX 2.1", key="convert_btn", use_container_width=True):
        with st.spinner("Converting to STIX 2.1..."):
            conversion_result = STIXConverter.convert_to_2_1(
                st.session_state.file_path,
                st.session_state.detection_result.get("version"),
                st.session_state.detection_result.get("format")
            )
            
            if conversion_result["success"]:
                st.session_state.converted_data = conversion_result["converted_data"]
                st.success(f"✅ {conversion_result['message']}")
            else:
                st.error(f"❌ {conversion_result['message']}")
    
    st.divider()
    st.markdown("### 📊 Step 3: Summary Statistics")
    
    # Use converted data if available, otherwise extract from original file
    stats_source = "Original File"
    if st.session_state.converted_data:
        stats_source = "Converted STIX 2.1"
        # Extract stats from converted data directly
        statistics = EnhancedValidator.extract_statistics_from_data(st.session_state.converted_data)
        st.session_state.statistics = statistics
    else:
        with st.spinner("🔄 Extracting statistics..."):
            statistics = EnhancedValidator.extract_statistics(st.session_state.file_path)
            st.session_state.statistics = statistics
    
    st.caption(f"📌 Statistics from: {stats_source}")
    
    if "error" not in statistics:
        # Display statistics in columns
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        
        with stat_col1:
            st.metric("🔢 Total Objects", statistics["total_objects"])
        
        with stat_col2:
            st.metric("🚨 Threat Indicators", statistics["threat_indicators"])
        
        with stat_col3:
            st.metric("🦠 Malware Objects", statistics["malware_objects"])
        
        with stat_col4:
            st.metric("👤 Identity Objects", statistics["identity_objects"])
        
        # Extended statistics
        stat_col5, stat_col6, stat_col7, stat_col8 = st.columns(4)
        
        with stat_col5:
            st.metric("🎯 Campaigns", statistics["campaign_objects"])
        
        with stat_col6:
            st.metric("🔧 Tools", statistics["tool_objects"])
        
        with stat_col7:
            st.metric("⚔️ Attack Patterns", statistics["attack_pattern_objects"])
        
        with stat_col8:
            st.metric("🔓 Vulnerabilities", statistics["vulnerability_objects"])
        
        # Object type distribution
        if statistics["object_types"]:
            st.markdown("#### Object Type Distribution")
            st.bar_chart(statistics["object_types"])
    else:
        st.error(f"Could not extract statistics: {statistics.get('error')}")
    
    st.divider()
    
    # ========== STEP 4: FILE PREVIEW ==========
    st.markdown("### 📄 Step 4: File Preview (First 100 lines)")
    
    with st.expander("📖 View File Content"):
        preview_content, preview_type = ResultFormatter.get_file_preview(
            st.session_state.file_path,
            lines=100
        )
        
        if preview_type == "json":
            st.code(preview_content, language="json")
        elif preview_type == "xml":
            st.code(preview_content, language="xml")
        else:
            st.code(preview_content, language="text")
    
    st.divider()
        # ========== STEP 4B: DOWNLOAD PROCESSED FILE ==========
    st.markdown("### 📥 Step 4B: Download Processed File")
    
    download_col1, download_col2 = st.columns(2)
    
    with download_col1:
        # Show download button if converted OR if already 2.1
        if st.session_state.converted_data:
            import json
            converted_json = json.dumps(st.session_state.converted_data, indent=2)
            st.download_button(
                "📥 Download STIX 2.1 Converted",
                converted_json,
                file_name=f"converted_stix_2_1_{Path(st.session_state.file_path).stem}.json",
                mime="application/json"
            )
        elif st.session_state.detection_result.get("format") == "json" and "2.1" in str(st.session_state.detection_result.get("version")):
            # File is already STIX 2.1, allow download of original
            try:
                with open(st.session_state.file_path, "r") as f:
                    original_json = f.read()
                st.download_button(
                    "📥 Download Original STIX 2.1",
                    original_json,
                    file_name=f"{Path(st.session_state.file_path).stem}.json",
                    mime="application/json"
                )
            except:
                st.info("Convert file first to download")
        else:
            st.info("Convert file first to download")
    
    with download_col2:
        # Only show success message if conversion was attempted and successful
        if st.session_state.converted_data:
            st.success("✅ Conversion successful!")
    
    st.divider()
        # ========== STEP 5: SUMMARY REPORT ==========
    st.markdown("### 📋 Step 5: Summary Report")
    
    # Create downloadable report
    report = f"""
STIX ANALYSIS REPORT
{'='*60}

FILE INFORMATION
{'-'*60}
Uploaded File: {Path(st.session_state.file_path).name}
File Size: {detection_result['file_size_kb']:.2f} KB

VERSION DETECTION
{'-'*60}
STIX Version: {detection_result['version']}
Format: {detection_result['format']}
Is Bundle: {detection_result['is_bundle']}
Object Count: {detection_result['object_count']}

VALIDATION RESULTS
{'-'*60}
Status: {'✅ VALID' if validation_result['is_valid'] else '❌ INVALID'}
Errors: {validation_result['error_count']}
Warnings: {validation_result['warning_count']}

Error Details:
{chr(10).join([f"  - {e.get('message', 'Unknown error')}" for e in validation_result['errors']])}

Warning Details:
{chr(10).join([f"  - {w.get('message', 'Unknown warning')}" for w in validation_result['warnings']])}

STATISTICS
{'-'*60}
Total Objects: {statistics.get('total_objects', 0)}
Threat Indicators: {statistics.get('threat_indicators', 0)}
Malware Objects: {statistics.get('malware_objects', 0)}
Identity Objects: {statistics.get('identity_objects', 0)}
Campaign Objects: {statistics.get('campaign_objects', 0)}
Attack Pattern Objects: {statistics.get('attack_pattern_objects', 0)}
Tool Objects: {statistics.get('tool_objects', 0)}
Vulnerability Objects: {statistics.get('vulnerability_objects', 0)}

CONCLUSION
{'-'*60}
The STIX file has been analyzed successfully.
{validation_result['summary']}
"""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.download_button(
            "📥 Download Report (TXT)",
            report,
            file_name="stix_analysis_report.txt",
            mime="text/plain"
        )
    
    with col2:
        if Path(st.session_state.file_path).suffix.lower() == ".json":
            st.info("📄 Original file is already JSON format (STIX 2.0/2.1)")
    
    with col3:
        st.info("💾 All data is stored per-session and will be cleared on refresh.")

else:
    # No file uploaded
    st.info(
        """
        👈 **Getting Started:**
        
        1. Click the file uploader in the left sidebar
        2. Select your STIX file (JSON or XML)
        3. Click "Analyze" button
        4. Review version detection, validation, and statistics
        
        **Supported Formats:**
        - STIX 1.x (XML files)
        - STIX 2.0 (JSON files)
        - STIX 2.1 (JSON files)
        """
    )

# ========== FOOTER ==========
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: #888; font-size: 12px;'>
    🔐 Session-based Analysis | Data cleared on page refresh | Built with Streamlit & STIX Libraries
    </div>
    """,
    unsafe_allow_html=True
)
