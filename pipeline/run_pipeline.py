import json
import sys
import uuid
from pathlib import Path

# Add parent directory to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.version_detector import detect_stix_version
from modules.converter import STIXConverter
from pipeline.stix_utils import extract_malware_object
from pipeline.feature_extractor import build_prompt
from pipeline.feature_generator import generate_description_from_features
from pipeline.llm import call_ollama
from pipeline.predictor import TechniquePredictor
from pipeline.inference_object import build_inference_object
from modules.formatter import ResultFormatter


def run_pipeline(file_path):
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # 1) detect version/format
    detected = detect_stix_version(str(file_path))
    suffix = file_path.suffix if file_path.suffix else ".json"
    input_format = "xml" if suffix.lower() == ".xml" else "json"

    # 2) convert to STIX 2.1
    conv = STIXConverter.convert_to_2_1(str(file_path), detected, input_format)

    if not conv.get("success"):
        raise Exception(f"Conversion failed: {conv.get('message')}")

    bundle = conv.get("converted_data")
    
    # If the result is a single object (not a bundle), wrap it in a bundle
    if bundle.get("type") != "bundle":
        bundle = {
            "type": "bundle",
            "id": f"bundle--{uuid.uuid4()}",
            "objects": [bundle],
            "spec_version": bundle.get("spec_version", "2.1")
        }

    # 3) extract malware object
    malware = extract_malware_object(bundle)

    if not malware:
        # Return converted bundle plus note, no malware found
        return {
            "bundle": bundle,
            "inference": None,
            "message": "No malware object found in converted STIX bundle"
        }

    # 4) build prompt and call LLM
    prompt = build_prompt(malware, bundle)
    llm_text = call_ollama(prompt)
    llm_generated = bool(llm_text)  # Track if LLM actually generated text
    
    # If LLM failed/timed out, use feature-based generator as fallback
    if not llm_text:
        print("LLM unavailable, generating profile from features...", flush=True)
        llm_text = generate_description_from_features(malware, bundle)
        llm_generated = False

    # 5) predict techniques
    predictor = TechniquePredictor()
    techniques, probs = predictor.predict(llm_text)

    # 6) build inference object and append
    inference = build_inference_object(malware.get("id"), techniques, llm_text, llm_generated)
    bundle.setdefault("objects", []).append(inference)

    # 7) attach original STIX file as an object
    try:
        raw = file_path.read_text(encoding="utf-8")
    except Exception:
        raw = ""

    original_obj = {
        "type": "x-original-stix",
        "id": f"x-original-stix--{uuid.uuid4()}",
        "file_name": file_path.name,
        "raw": raw
    }

    bundle["objects"].append(original_obj)

    # 8) format model output for UI
    formatted = ResultFormatter.format_detection_card({
        "version": detected,
        "format": input_format,
        "is_bundle": bundle.get("type") == "bundle",
        "object_count": len(bundle.get("objects", [])),
        "file_size_kb": file_path.stat().st_size / 1024.0,
        "is_valid": True,
    })

    return {
        "bundle": bundle,
        "formatted": formatted
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m pipeline.run_pipeline <stix-file>")
        sys.exit(1)

    path = sys.argv[1]

    try:
        out = run_pipeline(path)
        print(json.dumps(out, indent=2))
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
        sys.exit(2)
