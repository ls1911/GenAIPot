import logging
#from google.cloud import aiplatform
#from google.cloud.aiplatform.gapic.schema import predict
#from google.protobuf import json_format
#from utils import save_raw_response

class GCPService:
    def __init__(self, gcp_project=None, gcp_location=None, gcp_model_id=None, debug_mode=False):
        self.gcp_project = gcp_project
        self.gcp_location = gcp_location
        self.gcp_model_id = gcp_model_id
        self.debug_mode = debug_mode

    def query_gcp_gemini(self, prompt, response_type):
        try:
            if self.debug_mode:
                logging.debug(f"Querying Google Gemini Vertex for {response_type} responses...")
            
            client = aiplatform.gapic.PredictionServiceClient()
            endpoint = f"projects/{self.gcp_project}/locations/{self.gcp_location}/endpoints/{self.gcp_model_id}"
            instances = [{"content": prompt}]
            request = predict.instance.PredictRequest(
                endpoint=endpoint,
                instances=[json_format.ParseDict(instances, predict.instance.Value())],
                parameters=json_format.ParseDict({}, predict.instance.Value())
            )
            response = client.predict(request=request)
            response_text = response.predictions[0].get("content", "").strip()
            save_raw_response(response_text, response_type)
            return response_text
        except Exception as e:
            if self.debug_mode:
                logging.error(f"Error querying Google Gemini Vertex: {e}")
            return ""