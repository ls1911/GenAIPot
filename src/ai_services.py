# Copyright (C) 2024 Nucleon Cyber. All rights reserved.
#
# This file is part of GenAIPot.
#
# GenAIPot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# GenAIPot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GenAIPot. If not, see <http://www.gnu.org/licenses/>.
#
# For more information, visit: www.nucleon.sh or send email to contact[@]nucleon.sh
#

"""
This module provides AI service functionalities for interacting with OpenAI's API and Google's Gemini API Vertex.
It includes methods for querying responses, saving and loading responses,
and updating configuration settings.
"""

import configparser
import logging
import json
import os
import time

import openai
from google.cloud import aiplatform
from google.cloud.aiplatform.gapic.schema import predict
from google.protobuf import json_format

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR)  # Default to ERROR level

config_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'etc', 'config.ini'))
config = configparser.ConfigParser()
config.read(config_file_path)

class AIService:
    """
    AIService class handles interactions with the OpenAI API and Google Gemini API Vertex,
    including querying responses and managing configuration settings.

    Attributes:
        technology (str): The technology field from the config.
        domain (str): The domain field from the config.
        segment (str): The segment field from the config.
        anonymous_access (bool): The anonymous access field from the config.
        debug_mode (bool): Flag for enabling debug mode.
        gcp_project (str): GCP project ID for Gemini API Vertex.
        gcp_location (str): GCP location for Gemini API Vertex.
        gcp_model_id (str): Model ID for Gemini API Vertex.
    """

    def __init__(self, api_key=False, gcp_project=None, gcp_location=None, gcp_model_id=None, debug_mode=False):
        """
        Initialize AIService with API key for OpenAI, and GCP project details for Gemini API Vertex.

        Args:
            api_key (str): The API key for OpenAI.
            gcp_project (str): GCP project ID for Gemini API Vertex.
            gcp_location (str): GCP location for Gemini API Vertex.
            gcp_model_id (str): Model ID for Gemini API Vertex.
            debug_mode (bool): If True, enables debug logging.
        """
        self.technology = config.get('server', 'technology', fallback='generic')
        self.domain = config.get('server', 'domain', fallback='localhost')
        self.segment = config.get('server', 'segment', fallback='general')
        self.anonymous_access = config.getboolean('server', 'anonymous_access', fallback=False)

        openai.api_key = api_key  # Set the API key directly
        
        self.gcp_project = gcp_project
        self.gcp_location = gcp_location
        self.gcp_model_id = gcp_model_id
        self.debug_mode = debug_mode

        if self.debug_mode:
            logging.getLogger('ai_services').setLevel(logging.DEBUG)
            logging.getLogger('urllib3').setLevel(logging.DEBUG)
        else:
            logging.getLogger('ai_services').setLevel(logging.CRITICAL)
            logging.getLogger('urllib3').setLevel(logging.CRITICAL)

    def query_responses(self, prompt, response_type, use_openai=True):
        """
        Query AI services (OpenAI or Google Gemini Vertex) for responses based on the provided prompt and response type.

        Args:
            prompt (str): The prompt to send to the AI service.
            response_type (str): The type of response expected (e.g., "email").
            use_openai (bool): Whether to use OpenAI (True) or Gemini Vertex (False).

        Returns:
            str: The response text from the AI service.
        """
        if use_openai:
            return self._query_openai(prompt, response_type)
        else:
            return self._query_gcp_gemini(prompt, response_type)

    def _query_openai(self, prompt, response_type):
        for attempt in range(2):
            try:
                if self.debug_mode:
                    logger.debug(f"Querying OpenAI for {response_type} responses...")
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500
                )
                response_text = response.choices[0]['message']['content'].strip()
                self._save_raw_response(response_text, response_type)
                return response_text
            except Exception as e:
                if self.debug_mode:
                    logger.error(f"Error querying OpenAI (attempt {attempt+1}/2): {e}")
                if attempt == 1:
                    logger.critical("Failed to communicate with AI after 2 attempts. Exiting.")
                time.sleep(1)
        return ""

    def _query_gcp_gemini(self, prompt, response_type):
        try:
            if self.debug_mode:
                logger.debug(f"Querying Google Gemini Vertex for {response_type} responses...")
            
            client = aiplatform.gapic.PredictionServiceClient()
            endpoint = f"projects/{self.gcp_project}/locations/{self.gcp_location}/endpoints/{self.gcp_model_id}"

            instances = [{"content": prompt}]
            parameters = {}
            request = predict.instance.PredictRequest(
                endpoint=endpoint,
                instances=[json_format.ParseDict(instances, predict.instance.Value())],
                parameters=json_format.ParseDict(parameters, predict.instance.Value()),
            )
            response = client.predict(request=request)
            response_text = response.predictions[0].get("content", "").strip()
            self._save_raw_response(response_text, response_type)
            return response_text
        except Exception as e:
            if self.debug_mode:
                logger.error(f"Error querying Google Gemini Vertex: {e}")
            return ""

    def _save_raw_response(self, response_text, response_type):
        """
        Save the raw response text to a file.

        Args:
            response_text (str): The response text from the AI service.
            response_type (str): The type of response (e.g., "email").
        """
        filename = f'files/{response_type}_raw_response.txt'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(response_text)
        if self.debug_mode:
            logger.debug(f"Raw response saved in {filename}")

    def _store_responses(self, responses, response_type):
        """
        Store the parsed responses in a JSON file.

        Args:
            responses (dict): The parsed responses.
            response_type (str): The type of response (e.g., "email").
        """
        filename = f'files/{response_type}_responses.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(responses, f)
        if self.debug_mode:
            logger.debug(f"Responses stored in {filename}")

    def load_responses(self, response_type):
        """
        Load responses from a saved file.

        Args:
            response_type (str): The type of response (e.g., "email").

        Returns:
            str: The loaded response text.
        """
        filename = f'files/{response_type}_raw_response.txt'
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return f.read()
        return "No responses available"

    def cleanup_and_parse_json(self, text):
        """
        Clean up and parse a JSON string from text.

        Args:
            text (str): The text containing JSON.

        Returns:
            dict: The parsed JSON object, or an empty dict if parsing fails.
        """
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start == -1 or end == 0:
                if self.debug_mode:
                    logger.error("Invalid JSON structure detected.")
                    logger.debug(f"Raw text: {text}")
                return {}

            json_text = text[start:end]
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            if self.debug_mode:
                logger.error(f"Error parsing JSON response: {e}")
                logger.debug(f"Raw text for cleanup: {text}")
            return {}

    def generate_emails(self, segment, domain, email_num):
        """
        Generate a sample email related to the given segment and domain.

        This method uses the OpenAI API to generate a sample email, including
        the subject, body, and recipient address. The email content is saved
        to a file for later use.

        Args:
            segment (str): The segment or topic of the email.
            domain (str): The domain to use for the email address.
            email_num (int): The identifier number for the email.

        Returns:
            str: The generated email content.
        """
        try:
            prompt = (
                f"Generate an email related to the segment: {segment} for the domain {domain}. "
                f"The email should include a subject, body, and a recipient address at the domain."
            )
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500
            )
            response_text = response.choices[0]['message']['content'].strip()

            # Save the raw response to a file
            filename = f'files/email{email_num}_raw_response.txt'
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(response_text)
            if self.debug_mode:
                logger.debug(f"Raw response saved in {filename}")

            return response_text
        except Exception as e:
            if self.debug_mode:
                logger.error(f"Error querying OpenAI for email {email_num}: {e}")
            return "No response"
