import json
import logging

logger = logging.getLogger(__name__)

def extract_and_clean_json(text):
    try:
        # Attempt to extract JSON block even if it's surrounded by additional text
        start = text.find('{')
        end = text.rfind('}') + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON content found")
        
        json_text = text[start:end]
        
        # Check if extracted text is valid JSON
        try:
            data = json.loads(json_text)
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON: {e}")
            raise ValueError("Extracted text is not valid JSON")
    except Exception as e:
        logger.error(f"Error extracting JSON: {e}")
        logger.debug(f"Raw text for cleanup: {text}")
        raise ValueError("No JSON content found")