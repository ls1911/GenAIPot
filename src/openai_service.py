import openai
import logging

class OpenAIService:
    def __init__(self, api_key=None, debug_mode=False):
        """
        Initializes the OpenAI service with an API key and debug mode.
        """
        self.api_key = api_key
        openai.api_key = api_key
        self.debug_mode = debug_mode

        if self.debug_mode:
            logging.getLogger('openai_service').setLevel(logging.DEBUG)
        else:
            logging.getLogger('openai_service').setLevel(logging.CRITICAL)

    def validate_key(self):
        """
        Validates the OpenAI API key by making a simple request to the OpenAI API.
        """
        try:
            openai.Engine.list()  # This makes a simple request to verify the API key
            logging.info("OpenAI API key is valid.")
            return True
        except openai.error.AuthenticationError:
            logging.error("Invalid OpenAI API key.")
            return False
        except Exception as e:
            logging.error(f"Error validating OpenAI API key: {e}")
            return False

    def query_openai(self, prompt, response_type):
        """
        Queries OpenAI for a response based on the provided prompt.

        Args:
            prompt (str): The prompt to send to OpenAI.
            response_type (str): The type of response expected (e.g., "email").

        Returns:
            str: The response from OpenAI.
        """
        try:
            if self.debug_mode:
                logging.debug(f"Querying OpenAI for {response_type}...")

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500
            )
            response_text = response.choices[0]['message']['content'].strip()
            return response_text
        except Exception as e:
            logging.error(f"Failed to query OpenAI: {e}")
            return ""