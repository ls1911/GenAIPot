# src/smtp_protocol.py

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
import json
import base64
import time
from twisted.protocols.basic import LineReceiver
from twisted.internet import protocol, reactor
from ai_services import AIService
from database import log_interaction
from auth import check_credentials
import configparser
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# Load configuration with absolute path
config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'etc', 'config.ini')
if os.path.exists(config_path):
    config.read(config_path)
else:
    logger.error(f"Configuration file not found at {config_path}")
    # Handle missing configuration appropriately
domain_name = config.get('server', 'domain', fallback='localhost')
technology = config.get('server', 'technology', fallback='generic')
debug_mode = config.getboolean('server', 'debug', fallback=False)
rate_limit = config.getint('server', 'rate_limit', fallback=5)
blacklist = config.get('server', 'blacklist', fallback='').split(',')

# Clean up the blacklist to remove empty strings
blacklist = [ip.strip() for ip in blacklist if ip.strip()]

# Dictionary to track connection attempts per IP
connection_attempts = {}


class SMTPProtocol(LineReceiver):
    """
    A class representing the SMTP protocol for handling email transmission commands and responses.
    """

    def __init__(self, factory, debug=False):
        """
        Initialize the SMTPProtocol instance, setting up AI services and responses.

        Args:
            factory (SMTPFactory): The factory instance that created this protocol.
            debug (bool): Enables or disables debug mode.
        """
        self.factory = factory
        self.ip = None
        self.debug = debug or debug_mode
        self.ai_service = AIService(debug_mode=self.debug)
        try:
            responses = self.ai_service.load_responses("smtp")
            self.responses = self._format_responses(responses)
            if self.debug:
                logger.debug(f"Loaded and formatted responses: {self.responses}")
        except Exception as e:
            logger.error(f"Error loading SMTP responses: {e}")
            self.responses = self.default_responses()
        self.state = 'INITIAL'
        self.data_buffer = []
        self.auth_step = None
        self.auth_username = None
        self.auth_password = None

    def connectionMade(self):
        """
        Handle new connections, sending a welcome banner and logging the interaction.
        """
        self.ip = self.transport.getPeer().host

        # Check if IP is blacklisted
        if self.ip in self.factory.blacklist:
            logger.info(f"Connection attempt from blacklisted IP: {self.ip}")
            self.transport.loseConnection()
            return

        # Implement rate limiting
        if not self.factory.allow_connection(self.ip):
            logger.info(f"Rate limit exceeded for IP: {self.ip}")
            self.transport.loseConnection()
            return

        banner = self._get_banner()
        logger.info(f"Connection from {self.ip}")
        self.sendLine(banner.encode('utf-8'))
        log_interaction(self.ip, 'WELCOME', banner)

    def _get_banner(self):
        """
        Get the SMTP banner message to send upon connection.

        Returns:
            str: The banner message based on the server technology.
        """
        if technology.lower() == 'exchange':
            current_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
            return f"220 {domain_name} Microsoft ESMTP MAIL Service ready at {current_date}"
        return self.responses.get("220", f"220 {domain_name} ESMTP")

    def lineReceived(self, line):
        """
        Handle received lines of data, processing SMTP commands and managing state transitions.

        Args:
            line (bytes): The line of data received.
        """
        try:
            try:
                command = line.decode('utf-8').strip()
            except UnicodeDecodeError:
                command = line.decode('latin-1').strip()
            logger.info(f"Received command from {self.ip}: {command}")

            if self.state == 'DATA':
                if command == ".":
                    self.state = 'INITIAL'
                    data_message = "\n".join(self.data_buffer)
                    logger.info(f"Received DATA from {self.ip}:\n{data_message}")
                    self.data_buffer = []
                    response = self.responses.get("250-DATA", "250 OK: Queued")
                else:
                    self.data_buffer.append(command)
                    return
            elif self.auth_step:
                response = self._handle_auth(command)
                if response == '':
                    return  # Wait for next authentication input
            else:
                response = self._get_response(command)
                if response == '':
                    return  # Already handled in _get_response

            if command_upper := command.upper():
                if command_upper.startswith("QUIT"):
                    self.sendLine(response.encode('utf-8'))
                    log_interaction(self.ip, command, response)
                    self.transport.loseConnection()
                    return

            self.sendLine(response.encode('utf-8'))
            log_interaction(self.ip, command, response)
        except Exception as e:
            logger.error(f"Error processing command from {self.ip}: {e}")
            self.sendLine(b"500 Command unrecognized")

    def _get_response(self, command):
        """
        Generate the appropriate SMTP response for a given command.

        Args:
            command (str): The SMTP command received from the client.

        Returns:
            str: The SMTP response to be sent back to the client.
        """
        command_upper = command.upper()
        if command_upper.startswith("EHLO"):
            response = [self.responses.get("250-EHLO", f"250-{domain_name} Hello [{self.ip}]")]
            capabilities = [
                "SIZE 37748736",
                "PIPELINING",
                "DSN",
                "ENHANCEDSTATUSCODES",
                "STARTTLS",
                "AUTH LOGIN PLAIN",
                "8BITMIME",
                "SMTPUTF8",
            ]
            response.extend([f"250-{cap}" for cap in capabilities[:-1]])
            response.append(f"250 {capabilities[-1]}")
            return "\n".join(response)
        elif command_upper.startswith("HELO"):
            return self.responses.get("250-HELO", f"250 {domain_name}")
        elif command_upper.startswith("MAIL FROM"):
            return self.responses.get("250-MAIL FROM", "250 2.1.0 Sender OK")
        elif command_upper.startswith("RCPT TO"):
            return self.responses.get("250-RCPT TO", "250 2.1.5 Recipient OK")
        elif command_upper == "DATA":
            self.state = 'DATA'
            return self.responses.get("354", "354 End data with <CR><LF>.<CR><LF>")
        elif command_upper == "RSET":
            self.reset_state()
            return self.responses.get("250", "250 OK")
        elif command_upper.startswith("VRFY"):
            return self.responses.get("252", "252 Cannot VRFY user, but will accept message and attempt delivery")
        elif command_upper.startswith("EXPN"):
            return self.responses.get("502", "502 Command not implemented")
        elif command_upper == "NOOP":
            return self.responses.get("250", "250 OK")
        elif command_upper.startswith("HELP"):
            return self.responses.get("214", "214 Help message")
        elif command_upper.startswith("QUIT"):
            return self.responses.get("221", f"221 {domain_name} Service closing transmission channel")
        elif command_upper.startswith("AUTH LOGIN"):
            self.sendLine(b'334 VXNlcm5hbWU6')  # 'Username:' in Base64
            self.auth_step = 'USERNAME'
            return ''
        elif command_upper.startswith("AUTH PLAIN"):
            # Handle AUTH PLAIN with credentials in the same line
            try:
                parts = command.split(' ', 2)
                if len(parts) < 3:
                    self.sendLine(b'334 ')  # Prompt for credentials
                    self.auth_step = 'AUTH_PLAIN'
                    return ''
                credentials = parts[2]
                decoded_credentials = base64.b64decode(credentials).decode('utf-8')
                _, username, password = decoded_credentials.split('\x00')
                if check_credentials(username, password):
                    return self.responses.get("235", "235 Authentication successful")
                else:
                    return self.responses.get("535", "535 Authentication failed")
            except Exception as e:
                logger.error(f"Error during AUTH PLAIN from {self.ip}: {e}")
                return self.responses.get("535", "535 Authentication failed")
        else:
            return self.responses.get("500", "500 Command unrecognized")

    def _handle_auth(self, data):
        """
        Handle the authentication process for AUTH LOGIN.

        Args:
            data (str): The base64-encoded data received from the client.

        Returns:
            str: The SMTP response to be sent back to the client.
        """
        try:
            decoded_data = base64.b64decode(data.strip()).decode('utf-8')
            if self.auth_step == 'USERNAME':
                self.auth_username = decoded_data
                self.sendLine(b'334 UGFzc3dvcmQ6')  # 'Password:' in Base64
                self.auth_step = 'PASSWORD'
                return ''
            elif self.auth_step == 'PASSWORD':
                self.auth_password = decoded_data
                if check_credentials(self.auth_username, self.auth_password):
                    self.auth_step = None
                    self.auth_username = None
                    self.auth_password = None
                    return self.responses.get("235", "235 Authentication successful")
                else:
                    self.auth_step = None
                    self.auth_username = None
                    self.auth_password = None
                    return self.responses.get("535", "535 Authentication failed")
            elif self.auth_step == 'AUTH_PLAIN':
                # Handle continuation of AUTH PLAIN if credentials were not provided initially
                decoded_credentials = base64.b64decode(data.strip()).decode('utf-8')
                _, username, password = decoded_credentials.split('\x00')
                if check_credentials(username, password):
                    self.auth_step = None
                    return self.responses.get("235", "235 Authentication successful")
                else:
                    self.auth_step = None
                    return self.responses.get("535", "535 Authentication failed")
        except Exception as e:
            logger.error(f"Error during authentication from {self.ip}: {e}")
            self.auth_step = None
            return self.responses.get("535", "535 Authentication failed")

    def reset_state(self):
        """
        Reset the protocol state to INITIAL, clearing any buffers or authentication steps.
        """
        self.state = 'INITIAL'
        self.data_buffer = []
        self.auth_step = None
        self.auth_username = None
        self.auth_password = None

    def _format_responses(self, responses):
        """
        Format the loaded responses into a dictionary.

        Args:
            responses (dict or str): The dictionary or string of responses loaded from the AI service.

        Returns:
            dict: The formatted responses as a dictionary.
        """
        formatted_responses = {}

        # If responses are a string, attempt to parse it as JSON
        if isinstance(responses, str):
            try:
                responses = json.loads(responses)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON: {e}")
                return formatted_responses

        # If responses is a dictionary, process accordingly
        if isinstance(responses, dict):
            if "SMTP_Responses" in responses:
                # Handle list of dictionaries
                for item in responses["SMTP_Responses"]:
                    code = item.get('code')
                    message = item.get('message')
                    if code and message:
                        formatted_responses[code] = f"{code} {message}"
            elif "SMTP_Response_Codes" in responses:
                # Handle dictionary of codes
                for code, message in responses["SMTP_Response_Codes"].items():
                    formatted_responses[code] = f"{code} {message}"
            else:
                logger.error(f"Unexpected responses format: {responses}")
        else:
            logger.error(f"Unexpected type for responses: {type(responses)}")

        # Add default responses for additional commands if not provided
        default_additional_responses = {
            "252": "252 Cannot VRFY user, but will accept message and attempt delivery",
            "502": "502 Command not implemented",
            "214": "214 Help message",
        }
        for code, message in default_additional_responses.items():
            formatted_responses.setdefault(code, message)

        return formatted_responses

    def default_responses(self):
        """
        Provide default SMTP responses in case AI-generated responses are unavailable.

        Returns:
            dict: A dictionary of default SMTP responses.
        """
        return {
            "220": f"220 {domain_name} ESMTP",
            "221": f"221 {domain_name} Service closing transmission channel",
            "235": "235 Authentication successful",
            "250": f"250 {domain_name}",
            "250-EHLO": f"250-{domain_name} Hello [{self.ip}]",
            "250-HELO": f"250 {domain_name}",
            "250-MAIL FROM": "250 2.1.0 Sender OK",
            "250-RCPT TO": "250 2.1.5 Recipient OK",
            "250-DATA": "250 OK: Queued",
            "252": "252 Cannot VRFY user, but will accept message and attempt delivery",
            "502": "502 Command not implemented",
            "214": "214 Help message",
            "354": "354 End data with <CR><LF>.<CR><LF>",
            "500": "500 Command unrecognized",
            "535": "535 Authentication failed",
        }


class SMTPFactory(protocol.Factory):
    """
    A factory class for creating instances of SMTPProtocol.
    """

    def __init__(self, debug=False):
        """
        Initialize the SMTPFactory.

        Args:
            debug (bool): Indicates whether debug mode is enabled.
        """
        self.debug = debug or debug_mode
        if self.debug:
            logger.setLevel(logging.DEBUG)
        logger.debug("SMTPFactory initialized")
        self.blacklist = blacklist
        self.rate_limit = rate_limit
        self.connection_attempts = {}  # Dictionary to track connection times per IP

    def buildProtocol(self, addr):
        """
        Build and return an instance of SMTPProtocol.

        Args:
            addr (Address): The address of the incoming connection.

        Returns:
            SMTPProtocol: A new instance of SMTPProtocol.
        """
        logger.debug(f"Building SMTP protocol for {addr.host}")
        return SMTPProtocol(self, debug=self.debug)

    def allow_connection(self, ip):
        """
        Determine if a connection from the given IP should be allowed based on rate limiting.

        Args:
            ip (str): The IP address of the client.

        Returns:
            bool: True if the connection is allowed, False otherwise.
        """
        current_time = time.time()
        attempts = self.connection_attempts.get(ip, [])

        # Remove attempts older than 1 minute
        attempts = [t for t in attempts if current_time - t < 60]

        # Update the attempts list
        attempts.append(current_time)
        self.connection_attempts[ip] = attempts

        if self.debug:
            logger.debug(f"Connection attempts from {ip}: {len(attempts)}")

        # Check if attempts exceed rate limit
        if len(attempts) > self.rate_limit:
            # Schedule unblocking after 1 minute
            reactor.callLater(60, self._unblock_ip, ip)
            return False
        return True

    def _unblock_ip(self, ip):
        """
        Unblock the IP by resetting its connection attempts.

        Args:
            ip (str): The IP address to unblock.
        """
        if ip in self.connection_attempts:
            del self.connection_attempts[ip]
            if self.debug:
                logger.debug(f"IP {ip} has been unblocked after rate limiting period.")