import uuid
from datetime import datetime


def build_inference_object(malware_id, techniques, llm_text, llm_generated=True):
    """Build a STIX custom object with malware technique inference."""
    now = datetime.utcnow().isoformat() + "Z"

    return {
        "type": "x-malware-technique-inference",
        "id": f"x-malware-technique-inference--{uuid.uuid4()}",
        "created": now,
        "modified": now,
        "malware_ref": malware_id,
        "model": "lr-v1",
        "output": techniques,
        "llm_profile": llm_text,
        "llm_generated": llm_generated
    }