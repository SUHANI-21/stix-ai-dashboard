"""
Canonical Output Generator
Runs complete pipeline and outputs canonical JSON format
"""

import streamlit as st
import json
import tempfile
from pathlib import Path
from datetime import datetime
import sys
import signal
from functools import wraps

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.enhanced_detector import EnhancedVersionChecker
from modules.converter import STIXConverter
from threat_assessment import analyze_bundle
from pipeline.run_pipeline import run_pipeline

# Timeout decorator
def timeout(seconds):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import threading
            result = [None]
            exception = [None]
            
            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(seconds)
            
            if thread.is_alive():
                return {"status": "timeout", "message": f"Operation timed out after {seconds} seconds"}
            
            if exception[0]:
                raise exception[0]
            
            return result[0]
        return wrapper
    return decorator

st.set_page_config(page_title="Canonical Output Generator", layout="wide")

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
h1, h2, h3 { color: black; }
.success-box {
    background: #d4edda;
    padding: 15px;
    border-radius: 10px;
    border-left: 4px solid #28a745;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

st.markdown("# 📋 Canonical Output Generator")
st.markdown("Upload a STIX file → Run complete analysis → Get canonical JSON output")
st.markdown("---")

# File uploader
uploaded_file = st.file_uploader("Upload STIX file (JSON or XML)", type=["json", "xml"])

if uploaded_file:
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp:
        tmp.write(uploaded_file.read())
        file_path = tmp.name
    
    st.success(f"✅ File uploaded: {uploaded_file.name}")
    
    # Run button
    if st.button("🚀 Run Complete Analysis", type="primary"):
        
        with st.spinner("🔄 Running complete pipeline..."):
            try:
                # Step 1: Version Detection
                with st.status("Step 1: Detecting STIX version...", expanded=True) as status:
                    detection_result = EnhancedVersionChecker.detect_stix_full(file_path)
                    st.write(f"✅ Detected: {detection_result['version']} ({detection_result['format']})")
                    status.update(label="✅ Version detected", state="complete")
                
                # Step 2: Convert to STIX 2.1
                with st.status("Step 2: Converting to STIX 2.1...", expanded=True) as status:
                    conversion_result = STIXConverter.convert_to_2_1(
                        file_path,
                        detection_result['version'],
                        detection_result['format']
                    )
                    if conversion_result['success']:
                        st.write("✅ Conversion successful")
                        converted_data = conversion_result['converted_data']
                        status.update(label="✅ Converted to STIX 2.1", state="complete")
                    else:
                        st.error(f"❌ Conversion failed: {conversion_result['message']}")
                        st.stop()
                
                # Step 3: Credibility Assessment
                with st.status("Step 3: Running credibility assessment...", expanded=True) as status:
                    credibility_result = analyze_bundle(converted_data, skip_external_checks=True)
                    st.write(f"✅ Credibility Score: {credibility_result['score']}/100 ({credibility_result['rating']})")
                    status.update(label="✅ Credibility assessed", state="complete")
                
                # Step 4: Attack Mapping (with placeholder support)
                with st.status("Step 4: Running attack mapping...", expanded=True) as status:
                    try:
                        attack_result = run_pipeline(file_path)
                        st.write("✅ Attack mapping completed")
                        status.update(label="✅ Attack mapping complete", state="complete")
                        
                        # Extract only inference object, not the full bundle
                        attack_mapping_data = None
                        if attack_result and attack_result.get('bundle'):
                            for obj in attack_result['bundle'].get('objects', []):
                                if obj.get('type') == 'x-malware-technique-inference':
                                    attack_mapping_data = obj
                                    break
                        
                        if not attack_mapping_data:
                            attack_mapping_data = {"status": "no_inference", "message": "No malware found for technique inference"}
                    except Exception as e:
                        st.warning(f"⚠️ Attack mapping failed: {str(e)}")
                        attack_result = None
                        attack_mapping_data = {"status": "failed", "message": str(e)}
                        status.update(label="⚠️ Attack mapping skipped", state="complete")
                
                # Step 5: Malware Classifier (with 20s timeout)
                with st.status("Step 5: Running malware classifier...", expanded=True) as status:
                    try:
                        @timeout(20)
                        def run_malware_classifier():
                            from pages.malware_classifier import classify_malware
                            return classify_malware(converted_data)
                        
                        malware_classifier_result = run_malware_classifier()
                        
                        if malware_classifier_result.get("status") == "timeout":
                            st.warning("⏱️ Malware classifier timed out after 20 seconds")
                            status.update(label="⏱️ Malware Classifier (Timeout)", state="complete")
                        elif "error" in malware_classifier_result:
                            st.warning(f"⚠️ Malware classifier failed: {malware_classifier_result['error'][:100]}")
                            status.update(label="⚠️ Malware Classifier (Failed)", state="complete")
                        else:
                            st.write("✅ Malware classification completed")
                            status.update(label="✅ Malware Classifier complete", state="complete")
                    except Exception as e:
                        st.warning(f"⚠️ Malware classifier error: {str(e)[:100]}")
                        malware_classifier_result = {"status": "error", "message": str(e)}
                        status.update(label="⚠️ Malware Classifier (Error)", state="complete")
                
                # Step 6: SDO Similarity Search (with 20s timeout)
                with st.status("Step 6: Running SDO similarity search...", expanded=True) as status:
                    try:
                        @timeout(20)
                        def run_sdo_similarity():
                            from modules.bundles_2_csv import stix_json_to_csv
                            from modules.summary_generator import summarize_csv
                            from modules.clean_csv import clean_csv
                            from modules.similarity_search import generate_similarity_json
                            
                            # Save converted data to temp file
                            import tempfile
                            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                                json.dump(converted_data, f)
                                temp_path = f.name
                            
                            csv_path = stix_json_to_csv(temp_path)
                            summary_csv = summarize_csv(csv_path)
                            cleaned_csv = clean_csv(summary_csv)
                            
                            if cleaned_csv:
                                sim_path = generate_similarity_json(cleaned_csv, top_k=5)
                                with open(sim_path, 'r') as f:
                                    return json.load(f)
                            return {"error": "Failed to generate similarity data"}
                        
                        sdo_similarity_result = run_sdo_similarity()
                        
                        if sdo_similarity_result.get("status") == "timeout":
                            st.warning("⏱️ SDO similarity search timed out after 20 seconds")
                            status.update(label="⏱️ SDO Similarity (Timeout)", state="complete")
                        elif "error" in sdo_similarity_result:
                            st.warning(f"⚠️ SDO similarity failed: {sdo_similarity_result['error'][:100]}")
                            status.update(label="⚠️ SDO Similarity (Failed)", state="complete")
                        else:
                            st.write("✅ SDO similarity search completed")
                            status.update(label="✅ SDO Similarity complete", state="complete")
                    except Exception as e:
                        st.warning(f"⚠️ SDO similarity error: {str(e)[:100]}")
                        sdo_similarity_result = {"status": "error", "message": str(e)}
                        status.update(label="⚠️ SDO Similarity (Error)", state="complete")
                
                # Build Canonical Output
                st.success("✅ All steps completed!")
                
                canonical_output = {
                    "metadata": {
                        "original_filename": uploaded_file.name,
                        "processed_at": datetime.now().isoformat(),
                        "pipeline_version": "1.0"
                    },
                    "version_detection": {
                        "original_version": detection_result['version'],
                        "original_format": detection_result['format'],
                        "file_size_kb": detection_result['file_size_kb'],
                        "object_count": detection_result['object_count'],
                        "is_bundle": detection_result['is_bundle']
                    },
                    "converted_stix_2_1": converted_data,
                    "credibility_assessment": {
                        "score": credibility_result['score'],
                        "rating": credibility_result['rating'],
                        "reasons": credibility_result['reasons'],
                        "summary": credibility_result['summary']
                    },
                    "attack_mapping": attack_mapping_data,
                    "malware_classifier": malware_classifier_result,
                    "sdo_similarity_search": sdo_similarity_result
                }
                
                # Store raw data separately
                raw_data = uploaded_file.getvalue().decode('utf-8', errors='ignore')
                
                # Display results
                st.markdown("---")
                st.markdown("## 📊 Results")
                
                tab1, tab2, tab3 = st.tabs(["📋 Summary", "📄 Canonical JSON", "📋 Raw Uploaded File"])
                
                with tab1:
                    st.markdown("### Analysis Summary")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Original Version", detection_result['version'])
                        st.metric("File Size", f"{detection_result['file_size_kb']:.1f} KB")
                    with col2:
                        st.metric("Credibility Score", f"{credibility_result['score']}/100")
                        st.metric("Rating", credibility_result['rating'])
                    with col3:
                        st.metric("Objects", detection_result['object_count'])
                        st.metric("Format", detection_result['format'])
                    
                    st.markdown("### Credibility Reasons")
                    for reason in credibility_result['reasons']:
                        st.write(f"• {reason}")
                    
                    if attack_result and attack_result.get('bundle'):
                        st.markdown("### Attack Mapping")
                        inference_obj = None
                        for obj in attack_result['bundle'].get('objects', []):
                            if obj.get('type') == 'x-malware-technique-inference':
                                inference_obj = obj
                                break
                        
                        if inference_obj:
                            techniques = inference_obj.get('output', [])
                            st.write(f"**Predicted Techniques:** {len(techniques)}")
                            cols = st.columns(4)
                            for idx, tech in enumerate(techniques):
                                with cols[idx % 4]:
                                    st.button(tech, key=f"tech_{idx}", disabled=True)
                
                with tab2:
                    st.markdown("### Canonical JSON Output")
                    st.json(canonical_output, expanded=False)
                    
                    # Download button
                    st.download_button(
                        "📥 Download Canonical JSON",
                        json.dumps(canonical_output, indent=2),
                        file_name=f"canonical_output_{uploaded_file.name}.json",
                        mime="application/json"
                    )
                
                with tab3:
                    st.markdown("### Original Uploaded File")
                    try:
                        raw_json = json.loads(raw_data)
                        st.json(raw_json, expanded=False)
                    except:
                        st.code(raw_data, language='xml' if detection_result['format'] == 'xml' else 'json')
                    
                    st.download_button(
                        "📥 Download Original File",
                        raw_data,
                        file_name=uploaded_file.name,
                        mime="application/json" if detection_result['format'] == 'json' else "application/xml"
                    )
                
            except Exception as e:
                st.error(f"❌ Error during processing: {str(e)}")
                st.exception(e)

else:
    st.info("👆 Upload a STIX file to begin")
    
    # Show example output structure
    with st.expander("📖 Expected Canonical Output Structure"):
        example = {
            "metadata": {
                "original_filename": "example.json",
                "processed_at": "2024-01-01T00:00:00",
                "pipeline_version": "1.0"
            },
            "version_detection": {
                "original_version": "STIX 2.0",
                "original_format": "json",
                "file_size_kb": 12.5,
                "object_count": 10,
                "is_bundle": True
            },
            "converted_stix_2_1": {"type": "bundle", "objects": []},
            "credibility_assessment": {
                "score": 85,
                "rating": "HIGH",
                "reasons": ["✔ Valid STIX bundle format"],
                "summary": "Overall credibility is HIGH (85/100)."
            },
            "attack_mapping": {"bundle": {}, "formatted": {}},
            "malware_classifier": {"status": "placeholder"},
            "sdo_similarity_search": {"status": "placeholder"},
            "raw_original_file": "..."
        }
        st.json(example)
