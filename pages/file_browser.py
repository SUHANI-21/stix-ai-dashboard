"""
STIX File Browser
View and manage stored STIX files
"""
import streamlit as st
import json
from datetime import datetime
from pathlib import Path

# Import storage
from modules.storage import STIXStorage

st.set_page_config(page_title="STIX File Browser", layout="wide")

# Initialize storage
if "storage" not in st.session_state:
    st.session_state.storage = STIXStorage()

st.markdown("## 📁 STIX File Browser")
st.markdown("Browse and manage stored STIX files")

# Get all files
files = st.session_state.storage.list_files()

if not files:
    st.info("No STIX files stored yet. Convert some files first!")
else:
    st.markdown(f"**Found {len(files)} stored files:**")
    
    # Create columns for different file types
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📄 Original Files")
        for file_meta in files:
            file_id = file_meta.get('file_id')
            original_path = file_meta.get('original_path')
            if original_path and Path(original_path).exists():
                st.markdown(f"**{file_meta.get('original_filename', 'Unknown')}**")
                st.caption(f"ID: {file_id[:8]}...")
                st.caption(f"Size: {file_meta.get('file_size_kb', 0):.1f} KB")
                st.caption(f"Version: {file_meta.get('original_version', 'N/A')}")
                
                # Download original
                try:
                    with open(original_path, 'rb') as f:
                        st.download_button(
                            "📥 Download Original",
                            f.read(),
                            file_name=file_meta.get('original_filename', 'file'),
                            key=f"orig_{file_id[:8]}"
                        )
                except:
                    st.caption("❌ File not found")
                st.markdown("---")
    
    with col2:
        st.markdown("### 🔄 Converted Files")
        for file_meta in files:
            file_id = file_meta.get('file_id')
            stix_data = st.session_state.storage.get_stix_data(file_id)
            if stix_data:
                st.markdown(f"**STIX 2.1 - {file_meta.get('original_filename', 'Unknown')}**")
                st.caption(f"ID: {file_id[:8]}...")
                st.caption(f"Objects: {file_meta.get('object_count', 0)}")
                st.caption(f"Created: {file_meta.get('created_at', 'N/A')[:10]}")
                
                # Download converted
                st.download_button(
                    "📥 Download STIX 2.1",
                    json.dumps(stix_data, indent=2),
                    file_name=f"stix_2_1_{file_id[:8]}.json",
                    mime="application/json",
                    key=f"conv_{file_id[:8]}"
                )
                st.markdown("---")
    
    with col3:
        st.markdown("### 📊 Analysis Results")
        for file_meta in files:
            file_id = file_meta.get('file_id')
            results_list = st.session_state.storage.get_analysis_results_list(file_id)
            
            st.markdown(f"**Results - {file_meta.get('original_filename', 'Unknown')}**")
            st.caption(f"ID: {file_id[:8]}...")
            
            if results_list:
                st.caption(f"Modules: {len(results_list)}")
                for module in results_list:
                    result_data = st.session_state.storage.get_analysis_result(file_id, module)
                    if result_data:
                        st.download_button(
                            f"📥 {module}",
                            json.dumps(result_data, indent=2),
                            file_name=f"{module}_{file_id[:8]}.json",
                            mime="application/json",
                            key=f"res_{file_id[:8]}_{module}"
                        )
            else:
                st.caption("No analysis results yet")
            st.markdown("---")

# Add cleanup section
st.markdown("---")
st.markdown("### 🧹 File Management")

col1, col2 = st.columns(2)
with col1:
    st.info(f"**Storage Location:** `{st.session_state.storage.base_dir}`")

with col2:
    if st.button("🔄 Refresh List"):
        st.rerun()