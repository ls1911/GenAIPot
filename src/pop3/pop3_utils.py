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
    """
    Load email data from predefined JSON files and prepare it for further processing.

    This function checks specific JSON files for email data, extracts the contents, and formats them
    into a structure suitable for use within the application. It includes email headers, body, and size.

    Returns:
        list: A list of dictionaries, each containing the email headers, body, full content, and size in bytes.
    """
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
    """
    Generate synthetic email headers for a given email body.

    This function creates fake email headers including fields such as 'Received', 'Message-ID', 'Date',
    'From', and 'To', using random values for IP addresses and IDs. It simulates the email metadata.

    Args:
        email_body (dict): The body of the email for which headers are to be generated.

    Returns:
        str: A string containing the generated email headers.
    """
    random_ip = f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
    message_id = f"<{random.randint(1000000000, 9999999999)}.{''.join(random.choices(string.ascii_letters + string.digits, k=5))}@{domain_name}>"
    current_time = datetime.datetime.now()
    received_time = current_time - datetime.timedelta(hours=random.randint(10, 18))
    message_date_time = current_time - datetime.timedelta(hours=random.randint(5, 8))

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
    """
    Log interactions between the client and the server.

    This function logs the IP address of the client, the command sent, and the server's response.

    Args:
        ip (str): The IP address of the client.
        command (str): The command issued by the client.
        response (str): The response from the server.
    """
    logger.info(f"IP: {ip}, Command: {command}, Response: {response}")

def format_responses(responses):
    """
    Format the raw responses into a structured format for use in the application.

    This function takes a dictionary of raw responses, typically from a POP3 server or similar service,
    and restructures them into a more accessible format.

    Args:
        responses (dict): The raw responses dictionary.

    Returns:
        dict: A formatted dictionary where each key-value pair represents a code and its corresponding description.
    """
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
    
    # Ensure to add a final newline at the end of the file
