import logging
import os
import json
import random
import string
import datetime
import configparser

logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read('config.ini')
domain_name = config.get('server', 'domain', fallback='localhost')

def load_emails():
    email_files = [
        "files/email_email1.json",
        "files/email_email2.json",
        "files/email_email3.json"
    ]
    emails = []
    debug = config.getboolean('server', 'debug', fallback=False)
    if debug:
        logger.debug(f"Checking for email files in directory. Total files to check: {len(email_files)}")
    for email_file in email_files:
        if os.path.exists(email_file):
            if debug:
                logger.debug(f"Found email file: {email_file}")
            try:
                with open(email_file, 'r') as f:
                    email = json.load(f)
                    email_size = len(email.get("body", "").encode('utf-8'))
                    email_headers = generate_email_headers(email)
                    email_content = f"{email_headers}\n\n{email.get('body', '')}"
                    emails.append({
                        'headers': email_headers,
                        'body': email.get("body", ""),
                        'content': email_content,
                        'size': len(email_content.encode('utf-8'))
                    })
                    if debug:
                        logger.debug(f"Email file {email_file} size: {email_size} bytes")
            except Exception as e:
                logger.error(f"Error reading email file {email_file}: {e}")
        else:
            if debug:
                logger.debug(f"Email file not found: {email_file}")
    if debug:
        logger.debug(f"Total emails loaded: {len(emails)}")
    return emails

def generate_email_headers(email_body):
    random_ip = f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
    message_id = f"<{random.randint(1000000000, 9999999999)}.{''.join(random.choices(string.ascii_letters + string.digits, k=5))}@{domain_name}>"
    current_time = datetime.datetime.now()
    received_time = current_time - datetime.timedelta(hours=random.randint(10, 18))
    message_date_time = current_time - datetime.timedelta(hours=random.randint(5, 8))

    # Basic headers; modify according to actual email content
    headers = (
        f"Received: from {random_ip} by {domain_name} (SMTPD) id {''.join(random.choices(string.ascii_letters + string.digits, k=10))}\n"
        f"Message-ID: {message_id}\n"
        f"Date: {message_date_time.strftime('%a, %d %b %Y %H:%M:%S %z')}\n"
        f"From: {'unknown@domain.com'}\n"
        f"To: {'recipient@domain.com'}\n"
        f"Subject: {'No Subject'}\n"
    )
    return headers


def log_interaction(ip, command, response):
    # Implement the logging functionality
    logger.info(f"IP: {ip}, Command: {command}, Response: {response}")

def format_responses(responses):
    if isinstance(responses, dict):
        formatted_responses = {}
        for item in responses.get("POP3_Responses", []):
            code = item.get("code")
            descriptions = item.get("descriptions", {})
            for key, description in descriptions.items():
                formatted_responses[f"{code} {key}"] = f"{code} {description}"
        return formatted_responses
    else:
        logger.error(f"Unexpected responses format: {responses}")
        return {}