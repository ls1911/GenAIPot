import openai
import configparser
import logging
import json
import os
import time

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR)  # Default to ERROR level

#config = configparser.ConfigParser()
#config.read('../etc/config.ini')
        # Read config file
config_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'etc', 'config.ini'))
config = configparser.ConfigParser()
config.read(config_file_path)

class AIService:
    def __init__(self, debug_mode=False):
        self.technology = config.get('server', 'technology', fallback='generic')
        self.domain = config.get('server', 'domain', fallback='localhost')
        self.segment = config.get('server', 'segment', fallback='general')
        self.anonymous_access = config.getboolean('server', 'anonymous_access', fallback=False)

        if not config.has_section('openai'):
            config.add_section('openai')
            print ("no")

        openai.api_key = config['openai']['api_key']
        self.debug_mode = debug_mode

        if self.debug_mode:
            logging.getLogger('ai_services').setLevel(logging.DEBUG)
            logging.getLogger('urllib3').setLevel(logging.DEBUG)
        else:
            logging.getLogger('ai_services').setLevel(logging.CRITICAL)  # Suppress errors in non-debug mode
            logging.getLogger('urllib3').setLevel(logging.CRITICAL)

    def query_responses(self, prompt, response_type):
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
                    exit(1)
                time.sleep(1)

    def _save_raw_response(self, response_text, response_type):
        filename = f'files/{response_type}_raw_response.txt'
        with open(filename, 'w') as f:
            f.write(response_text)
        if self.debug_mode:
            logger.debug(f"Raw response saved in {filename}")

    def _store_responses(self, responses, response_type):
        filename = f'files/{response_type}_responses.json'
        with open(filename, 'w') as f:
            json.dump(responses, f)
        if self.debug_mode:
            logger.debug(f"Responses stored in {filename}")

    def load_responses(self, response_type):
        filename = f'files/{response_type}_raw_response.txt'
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return f.read()
        return "No responses available"

    def cleanup_and_parse_json(self, text):
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
            with open(filename, 'w') as f:
                f.write(response_text)
            if self.debug_mode:
                logger.debug(f"Raw response saved in {filename}")

            return response_text
        except Exception as e:
            if self.debug_mode:
                logger.error(f"Error querying OpenAI for email {email_num}: {e}")
            return "No response"

    def save_email_responses(self, responses, email_num):
        """
        Save the cleaned email responses to a file.

        Args:
            responses (dict): The responses to save.
            email_num (int): The email number identifier.
        """
        filename = f'files/email_email{email_num}.json'
        with open(filename, 'w') as f:
            json.dump(responses, f)
        if self.debug_mode:
            logger.debug(f"Email {email_num} response stored in {filename}")

    def update_config_technology(self, technology):
        config.set('server', 'technology', technology)
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        if self.debug_mode:
            logger.debug(f"Config file updated with technology: {technology}")

    def update_config_segment(self, segment):
        config.set('server', 'segment', segment)
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        if self.debug_mode:
            logger.debug(f"Config file updated with segment: {segment}")

    def update_config_domain(self, domain):
        config.set('server', 'domain', domain)
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        if self.debug_mode:
            logger.debug(f"Config file updated with domain: {domain}")

    def update_config_anonymous_access(self, anonymous_access):
        config.set('server', 'anonymous_access', str(anonymous_access))
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        if self.debug_mode:
            logger.debug(f"Config file updated with anonymous access: {anonymous_access}")