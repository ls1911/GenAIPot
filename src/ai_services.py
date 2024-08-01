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
This module provides AI service functionalities for interacting with OpenAI's API.
It includes methods for querying responses, saving and loading responses, 
and updating configuration settings.
"""

import configparser
import logging
import json
import os
import time

import openai

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR)  # Default to ERROR level

config_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'etc', 'config.ini'))
config = configparser.ConfigParser()
config.read(config_file_path)

class AIService:
    """
    AIService class handles interactions with the OpenAI API, including 
    querying responses and managing configuration settings.

    Attributes:
        technology (str): The technology field from the config.
        domain (str): The domain field from the config.
        segment (str): The segment field from the config.
        anonymous_access (bool): The anonymous access field from the config.
        debug_mode (bool): Flag for enabling debug mode.
    """

    def __init__(self, api_key, debug_mode=False):
        """
        Initialize AIService with API key and debug mode setting.

        Args:
            api_key (str): The API key for OpenAI.
            debug_mode (bool): If True, enables debug logging.
        """
        self.technology = config.get('server', 'technology', fallback='generic')
        self.domain = config.get('server', 'domain', fallback='localhost')
        self.segment = config.get('server', 'segment', fallback='general')
        self.anonymous_access = config.getboolean('server', 'anonymous_access', fallback=False)

        openai.api_key = api_key  # Set the API key directly

        self.debug_mode = debug_mode

        if self.debug_mode:
            logging.getLogger('ai_services').setLevel(logging.DEBUG)
            logging.getLogger('urllib3').setLevel(logging.DEBUG)
        else:
            logging.getLogger('ai_services').setLevel(logging.CRITICAL)
            logging.getLogger('urllib3').setLevel(logging.CRITICAL)

    def query_responses(self, prompt, response_type):
        """
        Query OpenAI for responses based on the provided prompt and response type.

        Args:
            prompt (str): The prompt to send to OpenAI.
            response_type (str): The type of response expected (e.g., "email").

        Returns:
            str: The response text from OpenAI.
        """
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
                    # sys.exit() - Commented out to avoid abrupt exit
                time.sleep(1)
        return ""

    def _save_raw_response(self, response_text, response_type):
        """
        Save the raw response text to a file.

        Args:
            response_text (str): The response text from OpenAI.
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
