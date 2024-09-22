# src/smtp/response_manager.py
import json
import logging

logger = logging.getLogger(__name__)

class ResponseManager:
    def __init__(self, ai_service, debug=False):
        self.ai_service = ai_service
        self.debug = debug
        self.responses = self._load_responses()

    def _load_responses(self):
        try:
            responses = self.ai_service.load_responses("smtp")
            return self._format_responses(responses)
        except Exception as e:
            logger.error(f"Error loading SMTP responses: {e}")
            return self.default_responses()

    def _format_responses(self, responses):
        formatted_responses = {}
        if isinstance(responses, str):
            try:
                responses = json.loads(responses)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON: {e}")
                return formatted_responses

        if isinstance(responses, dict):
            if "SMTP_Responses" in responses:
                for item in responses["SMTP_Responses"]:
                    code = item.get('code')
                    message = item.get('message')
                    if code and message:
                        formatted_responses[code] = f"{code} {message}"
            elif "SMTP_Response_Codes" in responses:
                for code, message in responses["SMTP_Response_Codes"].items():
                    formatted_responses[code] = f"{code} {message}"
            else:
                logger.error(f"Unexpected responses format: {responses}")
        else:
            logger.error(f"Unexpected type for responses: {type(responses)}")

        return formatted_responses

    def default_responses(self):
        return {
            "220": f"220 localhost ESMTP",
            "221": f"221 localhost Service closing transmission channel",
            "235": "235 Authentication successful",
            "250": "250 localhost",
            "252": "252 Cannot VRFY user, but will accept message and attempt delivery",
            "502": "502 Command not implemented",
            "214": "214 Help message",
            "354": "354 End data with <CR><LF>.<CR><LF>",
            "500": "500 Command unrecognized",
            "535": "535 Authentication failed",
        }

    def get_response(self, code, default=None):
        return self.responses.get(code, default)