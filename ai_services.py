import openai
import configparser
import logging
import json
import os

logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read('config.ini')

class AIService:
    def __init__(self):
        self.technology = config.get('server', 'technology', fallback='generic')
        self.domain = config.get('server', 'domain', fallback='localhost')
        self.segment = config.get('server', 'segment', fallback='general')
        self.anonymous_access = config.getboolean('server', 'anonymous_access', fallback=False)
        openai.api_key = config['openai']['api_key']

    def query_responses(self, prompt, response_type):
        try:
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
            self._save_raw_response(response_text, response_type)

            return response_text
        except Exception as e:
            logger.error(f"Error querying OpenAI: {e}")
            return ""

    def _extract_and_clean_json(self, text):
        try:
            # Extract the JSON part from within the text
            start = text.find('{')
            end = text.rfind('}') + 1
            json_text = text[start:end]
            responses = json.loads(json_text)

            return responses
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing extracted JSON: {e}")
            raise

    def _save_raw_response(self, response_text, response_type):
        filename = f'files/{self.technology}_{response_type}_raw_response.txt'
        with open(filename, 'w') as f:
            f.write(response_text)
        logger.info(f"Raw response saved in {filename}")

    def _store_responses(self, responses, response_type):
        filename = f'files/{self.technology}_{response_type}_responses.json'
        with open(filename, 'w') as f:
            json.dump(responses, f)
        logger.info(f"Responses stored in {filename}")

    def load_responses(self, response_type):
        filename = f'files/{self.technology}_{response_type}_responses.json'
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        return self.default_responses(response_type)

    def default_responses(self, response_type):
        if response_type == "smtp":
            return {
                "220": f"{self.domain} {self.technology} SMTP server ready",
                "221": f"{self.domain} Service closing transmission channel",
                "250": "Requested mail action okay, completed",
                "251": "User not local; will forward",
                "354": "Start mail input; end with <CRLF>.<CRLF>",
                "421": "Service not available, closing transmission channel",
                "450": "Requested mail action not taken: mailbox unavailable",
                "451": "Requested action aborted: local error in processing",
                "452": "Requested action not taken: insufficient system storage",
                "500": "Syntax error, command unrecognized",
                "501": "Syntax error in parameters or arguments",
                "502": "Command not implemented",
                "503": "Bad sequence of commands",
                "504": "Command parameter not implemented",
                "550": "Requested action not taken: mailbox unavailable",
                "551": "User not local; please try",
                "552": "Requested mail action aborted: exceeded storage allocation",
                "553": "Requested action not taken: mailbox name not allowed",
                "554": "Transaction failed"
            }
        elif response_type == "pop3":
            return {
                "+OK": f"+OK {self.domain} {self.technology} POP3 server ready",
                "-ERR": "-ERR command not recognized"
            }

    def save_email_responses(self, email_response, email_num):
        filename = f'files/email_{email_num}.json'
        with open(filename, 'w') as f:
            json.dump(email_response, f)
        logger.info(f"Email {email_num} response stored in {filename}")

    def update_config_technology(self, technology):
        config.set('server', 'technology', technology)
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        logger.info(f"Config file updated with technology: {technology}")

    def update_config_segment(self, segment):
        config.set('server', 'segment', segment)
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        logger.info(f"Config file updated with segment: {segment}")

    def update_config_domain(self, domain):
        config.set('server', 'domain', domain)
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        logger.info(f"Config file updated with domain: {domain}")

    def update_config_anonymous_access(self, anonymous_access):
        config.set('server', 'anonymous_access', str(anonymous_access))
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        logger.info(f"Config file updated with anonymous_access: {anonymous_access}")

    def cleanup_and_parse_json(self, text):
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            json_text = text[start:end]
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            logger.debug(f"Raw text for cleanup: {text}")
            if start == -1 or end == 0:
                logger.error("Invalid JSON structure detected.")
                return {}

            cleaned_text = text[start:end]
            cleaned_text = cleaned_text.replace('\n', '').replace('\r', '')
            try:
                return json.loads(cleaned_text)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing cleaned JSON: {e}")
                return {}

    def generate_emails(self, segment, domain, email_type):
        try:
            prompt = (
                f"Generate an email for a {email_type} related to the segment: {segment} in JSON format. "
                f"The email should include a subject, body, mail from, and rcpt to field. The rcpt_to field "
                f"should include a random name and the domain {domain}."
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
            filename = f'files/{email_type}_raw_response.txt'
            with open(filename, 'w') as f:
                f.write(response_text)
            logger.info(f"Raw response saved in {filename}")

            email_json = self.cleanup_and_parse_json(response_text)
            return email_json
        except Exception as e:
            logger.error(f"Error querying OpenAI for {email_type} email: {e}")
            return {}