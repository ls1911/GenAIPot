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
from twisted.protocols.basic import LineReceiver
from twisted.internet import protocol
from ai_services import AIService
from database import log_interaction
from auth import check_credentials
import configparser
from datetime import datetime

logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read('config.ini')
domain_name = config.get('server', 'domain', fallback='localhost')
technology = config.get('server', 'technology', fallback='generic')

class SMTPProtocol(LineReceiver):
    """
    A class representing the SMTP protocol for handling email transmission commands and responses.
    
    Attributes:
        ip (str): The IP address of the connected client.
        ai_service (AIService): An instance of the AIService for loading and managing responses.
        responses (dict): A dictionary of SMTP responses loaded from the AI service.
        state (str): The current state of the protocol, used to manage the 
        flow of commands (e.g., INITIAL, DATA).
        data_buffer (list): A buffer for storing lines of data received during the DATA state.
    """

    def __init__(self):
        """
        Initialize the SMTPProtocol instance, setting up AI services and responses.
        """
        self.ip = None
        self.ai_service = AIService()
        responses = self.ai_service.load_responses("smtp")
        logger.debug(f"Loaded responses: {responses}")
        self.responses = self._format_responses(responses)
        self.state = 'INITIAL'
        self.data_buffer = []
        logger.debug("SMTPProtocol initialized")

    def connectionMade(self):
        """
        Handle new connections, sending a welcome banner and logging the interaction.
        """
        self.ip = self.transport.getPeer().host
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
            command = line.decode('utf-8').strip()
            logger.info(f"Received command: {command}")

            if self.state == 'DATA':
                if command == ".":
                    self.state = 'INITIAL'
                    data_message = "\n".join(self.data_buffer)
                    logger.info(f"Received DATA: {data_message}")
                    self.data_buffer = []
                    response = self.responses.get("250-DATA", "250 ok")
                else:
                    self.data_buffer.append(command)
                    return
            else:
                response = self._get_response(command)
                if command.upper().startswith("QUIT"):
                    self.sendLine(response.encode('utf-8'))
                    log_interaction(self.ip, command, response)
                    self.transport.loseConnection()
                    return

            self.sendLine(response.encode('utf-8'))
            log_interaction(self.ip, command, response)
        except UnicodeDecodeError as e:
            logger.error(f"Unicode decode error: {e}")
            self.sendLine(b"500 Command unrecognized")

    def _get_response(self, command):
        """
        Get the appropriate response for a given SMTP command.

        Args:
            command (str): The SMTP command received.

        Returns:
            str: The response to the SMTP command.
        """
        command_upper = command.upper()
        if command_upper.startswith("EHLO"):
            return self.responses.get("250-EHLO", f"250-{domain_name} Hello [{self.ip}]") + \
                   "\n250-SIZE 37748736\n250-PIPELINING\n250-DSN\n250-ENHANCEDSTATUSCODES\n250-STARTTLS\n250-X-ANONYMOUSTLS\n250-AUTH NTLM\n250-X-EXPS GSSAPI NTLM\n250-8BITMIME\n250-BINARYMIME\n250-CHUNKING\n250 XRDST"
        elif command_upper.startswith("HELO"):
            return self.responses.get("250-HELO", f"250 {domain_name}")
        elif command_upper.startswith("MAIL FROM"):
            return self.responses.get("250-MAIL FROM", "250 2.1.0 Sender OK")
        elif command_upper.startswith("RCPT TO"):
            return self.responses.get("250-RCPT TO", "250 2.1.5 Recipient OK")
        elif command_upper.startswith("DATA"):
            self.state = 'DATA'
            return self.responses.get("354", "354 Start mail input; end with <CRLF>.<CRLF>")
        elif command_upper.startswith("QUIT"):
            return self.responses.get("221", f"221 {domain_name} Service closing transmission channel")
        elif command_upper.startswith("AUTH LOGIN"):
            username = self._read_base64_response()
            password = self._read_base64_response()
            if check_credentials(username, password):
                return self.responses.get("235", "235 Authentication successful")
            else:
                return self.responses.get("535", "535 Authentication failed")
        else:
            return self.responses.get("500", "500 Command unrecognized")

    def _read_base64_response(self):
        """
        Read a base64 encoded response from the client.

        Returns:
            str: The decoded response (e.g., username or password).

        Note:
            This method should be implemented to actually decode base64 responses. 
            Currently, it returns a placeholder.
        """
        return "username"  # Replace this with actual base64 decoding logic

    def _format_responses(self, responses):
        """
        Format the loaded responses into a dictionary.

        Args:
            responses (dict or str): The dictionary or string of responses loaded from the AI service.

        Returns:
            dict: The formatted responses as a dictionary.
        """
        formatted_responses = {}

        # If the responses are already a dictionary, just return them
        if isinstance(responses, dict):
            return responses

        # If responses are a string, attempt to parse them as JSON
        try:
            responses = json.loads(responses)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            return formatted_responses

        # Now handle the expected structure
        if "SMTP_Responses" in responses:
            for item in responses["SMTP_Responses"]:
                code = item.get('code')
                message = item.get('message')
                if code and message:
                    formatted_responses[f"{code}"] = f"{code} {message}"
        else:
            logger.error(f"Unexpected responses format: {responses}")
        
        return formatted_responses

class SMTPFactory(protocol.Factory):
    """
    A factory class for creating instances of SMTPProtocol.
    """

    def __init__(self):
        """
        Initialize the SMTPFactory.
        """
        logger.debug("SMTPFactory initialized")

    def buildProtocol(self, addr):
        """
        Build and return an instance of SMTPProtocol.

        Args:
            addr (Address): The address of the incoming connection.

        Returns:
            SMTPProtocol: A new instance of SMTPProtocol.
        """
        logger.debug(f"Building SMTP protocol for {addr}")
        return SMTPProtocol()