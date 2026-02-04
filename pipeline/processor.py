from modules.converter import STIXConverter

from pipeline.stix_utils import extract_malware_object
from pipeline.feature_extractor import build_prompt
from pipeline.llm import call_ollama
from pipeline.predictor import TechniquePredictor
from pipeline.inference_object import build_inference_object


class STIXPipeline:

    def __init__(self):

        self.predictor = TechniquePredictor()


    def run(self, bundle):

        # 1 Convert
        bundle_21 = STIXConverter(bundle)

        # 2 Extract malware
        malware = extract_malware_object(bundle_21)

        if not malware:
            raise Exception("No malware object found")

        # 3 LLM
        prompt = build_prompt(malware, bundle_21)

        llm_text = call_ollama(prompt)

        # 4 Predict
        techniques, probs = self.predictor.predict(llm_text)

        # 5 Build inference
        inference = build_inference_object(
            malware["id"],
            techniques,
            llm_text
        )

        # 6 Append
        bundle_21["objects"].append(inference)

        return bundle_21
