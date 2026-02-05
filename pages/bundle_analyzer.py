import streamlit as st
import json
import tempfile
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.converter import STIXConverter
from modules.version_detector import detect_stix_version
from modules.rag_engine import RAGEngine

def initialize_rag():
    """Initialize RAG engine for malware analysis"""
    if 'malware_rag_engine' not in st.session_state:
        with st.spinner("Initializing Malware RAG system..."):
            try:
                st.session_state.malware_rag_engine = RAGEngine()
                st.session_state.malware_rag_initialized = True
            except Exception as e:
                st.error(f"Failed to initialize Malware RAG: {e}")
                st.session_state.malware_rag_initialized = False
    
    return st.session_state.get('malware_rag_initialized', False)

def analyze_bundle_with_rag(bundle_data, question="Analyze this STIX bundle for malware threats and provide insights"):
    """Analyze STIX bundle using RAG"""
    try:
        # Extract malware-related information from bundle
        malware_context = extract_malware_context(bundle_data)
        
        # Query RAG with context
        if malware_context:
            enhanced_question = f"{question}\n\nBundle Context:\n{malware_context}"
        else:
            enhanced_question = question
            
        response = st.session_state.malware_rag_engine.query(enhanced_question)
        return response
    except Exception as e:
        return {"answer": f"Error analyzing bundle: {str(e)}", "sources": []}

def extract_malware_context(bundle_data):
    """Extract malware-relevant information from STIX bundle"""
    context_parts = []
    
    objects = bundle_data.get("objects", [])
    
    for obj in objects:
        obj_type = obj.get("type", "")
        
        if obj_type == "malware":
            name = obj.get("name", "Unknown")
            description = obj.get("description", "")
            labels = obj.get("labels", [])
            context_parts.append(f"Malware: {name} - Labels: {', '.join(labels)} - {description}")
            
        elif obj_type == "attack-pattern":
            name = obj.get("name", "Unknown")
            description = obj.get("description", "")
            context_parts.append(f"Attack Pattern: {name} - {description}")
            
        elif obj_type == "indicator":
            pattern = obj.get("pattern", "")
            labels = obj.get("labels", [])
            context_parts.append(f"Indicator: {pattern} - Labels: {', '.join(labels)}")
            
        elif obj_type == "relationship":
            source = obj.get("source_ref", "")
            target = obj.get("target_ref", "")
            rel_type = obj.get("relationship_type", "")
            context_parts.append(f"Relationship: {source} {rel_type} {target}")
    
    return "\n".join(context_parts[:10])  # Limit context size

def main():
    st.title("🔍 STIX Bundle Malware Analyzer")
    st.markdown("Upload any STIX bundle version and get AI-powered malware analysis")
    
    # Initialize RAG
    if not initialize_rag():
        st.error("❌ Malware RAG system failed to initialize. Please check the logs.")
        return
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload STIX Bundle (JSON or XML)",
        type=["json", "xml"],
        help="Supports STIX 1.x, 2.0, and 2.1 formats"
    )
    
    if uploaded_file:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp:
            tmp.write(uploaded_file.getvalue())
            file_path = tmp.name
        
        try:
            # Detect version and format
            file_ext = Path(file_path).suffix.lower()
            input_format = "json" if file_ext == ".json" else "xml"
            
            with st.spinner("Detecting STIX version..."):
                input_version = detect_stix_version(file_path)
            
            st.info(f"📋 **File:** {uploaded_file.name}")
            st.info(f"🔍 **Detected Version:** {input_version}")
            st.info(f"📄 **Format:** {input_format.upper()}")
            
            # Convert to STIX 2.1
            with st.spinner("Converting to STIX 2.1..."):
                conversion_result = STIXConverter.convert_to_2_1(file_path, input_version, input_format)
            
            if conversion_result["success"]:
                st.success(f"✅ {conversion_result['message']}")
                converted_data = conversion_result["converted_data"]
                
                # Display bundle overview
                st.markdown("## 📊 Bundle Overview")
                objects = converted_data.get("objects", [])
                
                # Count object types
                type_counts = {}
                for obj in objects:
                    obj_type = obj.get("type", "unknown")
                    type_counts[obj_type] = type_counts.get(obj_type, 0) + 1
                
                # Display counts in columns
                cols = st.columns(min(len(type_counts), 4))
                for i, (obj_type, count) in enumerate(type_counts.items()):
                    with cols[i % 4]:
                        st.metric(obj_type.replace("-", " ").title(), count)
                
                # Malware RAG Analysis
                st.markdown("## 🤖 AI Malware Analysis")
                
                # Analysis options
                analysis_type = st.selectbox(
                    "Select Analysis Type:",
                    [
                        "General Malware Analysis",
                        "Threat Actor Attribution", 
                        "Attack Pattern Analysis",
                        "Indicator Analysis",
                        "Custom Query"
                    ]
                )
                
                # Prepare question based on analysis type
                questions = {
                    "General Malware Analysis": "Analyze this STIX bundle for malware threats, attack patterns, and provide security insights",
                    "Threat Actor Attribution": "Analyze this bundle for threat actor attribution, TTPs, and campaign information",
                    "Attack Pattern Analysis": "Focus on attack patterns and techniques used in this bundle, map to MITRE ATT&CK",
                    "Indicator Analysis": "Analyze the indicators in this bundle and their threat implications",
                    "Custom Query": ""
                }
                
                if analysis_type == "Custom Query":
                    question = st.text_area("Enter your custom analysis question:", 
                                           placeholder="What specific aspect would you like to analyze?")
                else:
                    question = questions[analysis_type]
                    st.info(f"**Analysis Focus:** {question}")
                
                # Run analysis
                if st.button("🔍 Run Analysis", type="primary"):
                    if question.strip():
                        with st.spinner("Analyzing bundle with AI..."):
                            analysis_result = analyze_bundle_with_rag(converted_data, question)
                        
                        # Display results
                        st.markdown("### 📋 Analysis Results")
                        st.markdown(analysis_result["answer"])
                        
                        # Display sources
                        if analysis_result.get("sources"):
                            with st.expander("📚 Knowledge Sources Used", expanded=False):
                                for i, source in enumerate(analysis_result["sources"], 1):
                                    st.markdown(f"""
                                    **Source {i}:**
                                    - File: `{source['source']}`
                                    - Type: `{source['type']}`
                                    - Relevance: {source['relevance']}
                                    """)
                    else:
                        st.warning("Please enter a question for analysis.")
                
                # Raw data view
                with st.expander("🔍 View Converted STIX 2.1 Data", expanded=False):
                    st.json(converted_data)
                
                # Download converted bundle
                st.download_button(
                    "💾 Download STIX 2.1 Bundle",
                    json.dumps(converted_data, indent=2),
                    f"{Path(uploaded_file.name).stem}_converted_2.1.json",
                    "application/json"
                )
                
            else:
                st.error(f"❌ Conversion failed: {conversion_result['message']}")
                
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
        finally:
            # Clean up temp file
            try:
                os.unlink(file_path)
            except:
                pass
    
    else:
        st.info("👆 Upload a STIX bundle to begin analysis")
        
        # Show example
        with st.expander("📖 What this tool does", expanded=True):
            st.markdown("""
            This tool provides comprehensive STIX bundle analysis:
            
            1. **🔄 Universal Conversion**: Converts any STIX version (1.x, 2.0, 2.1) to STIX 2.1
            2. **🤖 AI Analysis**: Uses RAG (Retrieval-Augmented Generation) with malware knowledge base
            3. **🎯 Focused Insights**: Provides targeted analysis for malware, threat actors, and attack patterns
            4. **📊 Visual Overview**: Shows bundle composition and object relationships
            5. **💾 Export**: Download converted STIX 2.1 bundles
            
            **Supported Analysis Types:**
            - General malware threat analysis
            - Threat actor attribution and TTPs
            - MITRE ATT&CK technique mapping
            - Indicator threat assessment
            - Custom security queries
            """)

if __name__ == "__main__":
    main()