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
# src/smtp_protocol.py

import logging
from twisted.internet import protocol
from smtp.config_manager import ConfigManager
from smtp.smtp_banner import SMTPBanner
from smtp.response_manager import ResponseManager
from smtp.rate_limiter import RateLimiter
from twisted.protocols.basic import LineReceiver
from ai_services import AIService
from database import log_interaction

logger = logging.getLogger(__name__)

# SMTP Protocol
class SMTPProtocol(LineReceiver):
    def __init__(self, factory, debug=False):
        self.factory = factory
        self.ip = None
        self.debug = debug
        self.ai_service = AIService(debug_mode=self.debug)
        self.responses = ResponseManager(self.ai_service, debug)
        self.state = 'INITIAL'
        self.data_buffer = []
        self.auth_step = None
        self.auth_username = None
        self.auth_password = None

    def connectionMade(self):
        self.ip = self.transport.getPeer().host
        if not self.factory.rate_limiter.allow_connection(self.ip):
            logger.info(f"Rate limit exceeded for IP: {self.ip}")
            self.transport.loseConnection()
            return

        banner = self.factory.banner.get_banner()
        self.sendLine(banner.encode('utf-8'))
        log_interaction(self.ip, 'WELCOME', banner)

    def lineReceived(self, line):
        try:
            command = line.decode('utf-8').strip()
            if self.state == 'DATA':
                if command == ".":
                    self.state = 'INITIAL'
                    data_message = "\n".join(self.data_buffer)
                    self.data_buffer = []
                    response = self.responses.get_response("250-DATA", "250 OK: Queued")
                else:
                    self.data_buffer.append(command)
                    return
            else:
                response = self._get_response(command)

            self.sendLine(response.encode('utf-8'))
            log_interaction(self.ip, command, response)

        except Exception as e:
            logger.error(f"Error processing command from {self.ip}: {e}")
            self.sendLine(b"500 Command unrecognized")

    def _get_response(self, command):
        command_upper = command.upper()
        if command_upper.startswith("EHLO"):
            return self._ehlo_response()
        elif command_upper.startswith("HELO"):
            return self.responses.get_response("250-HELO", "250 localhost")
        # Other SMTP commands here

    def _ehlo_response(self):
        response = [self.responses.get_response("250-EHLO", f"250-{self.factory.banner.domain_name} Hello [{self.ip}]")]
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


# SMTP Factory
class SMTPFactory(protocol.Factory):
    def __init__(self, debug=False):
        self.config = ConfigManager()
        self.debug = debug or self.config.getboolean('server', 'debug')
        self.banner = SMTPBanner(self.config.get('server', 'domain', fallback='localhost'),
                                 self.config.get('server', 'technology', fallback='generic'))
        self.rate_limiter = RateLimiter(self.config.getint('server', 'rate_limit', fallback=5))

    def buildProtocol(self, addr):
        return SMTPProtocol(self, debug=self.debug)

if __name__ == "__main__":
    # Start the reactor or other initialization code
    pass