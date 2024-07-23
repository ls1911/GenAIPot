import logging
from twisted.protocols.basic import LineReceiver
from twisted.internet import protocol
from ai_services import AIService
from database import log_interaction
import configparser
from datetime import datetime

logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read('config.ini')
domain_name = config.get('server', 'domain', fallback='localhost')
technology = config.get('server', 'technology', fallback='generic')

class SMTPProtocol(LineReceiver):
    def __init__(self):
        self.ip = None
        self.ai_service = AIService()
        responses = self.ai_service.load_responses("smtp")
        logger.debug(f"Loaded responses: {responses}")
        self.responses = self._format_responses(responses)
        self.state = 'INITIAL'
        self.data_buffer = []
        logger.debug("SMTPProtocol initialized")

    def connectionMade(self):
        self.ip = self.transport.getPeer().host
        banner = self._get_banner()
        logger.info(f"Connection from {self.ip}")
        self.sendLine(banner.encode('utf-8'))
        log_interaction(self.ip, 'WELCOME', banner)

    def _get_banner(self):
        if technology.lower() == 'exchange':
            current_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
            return f"220 {domain_name} Microsoft ESMTP MAIL Service ready at {current_date}"
        return self.responses.get("220", f"220 {domain_name} ESMTP")

    def lineReceived(self, line):
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
        else:
            return self.responses.get("500", "500 Command unrecognized")

    def _format_responses(self, responses):
        if isinstance(responses, list):
            formatted_responses = {}
            for item in responses:
                if isinstance(item, dict):
                    code = item.get('response_code')
                    description = item.get('description')
                    if code and description:
                        formatted_responses[f"{code}"] = f"{code} {description}"
                else:
                    logger.error(f"Unexpected item format: {item}")
            return formatted_responses
        else:
            logger.error(f"Unexpected responses format: {responses}")
            return {}

class SMTPFactory(protocol.Factory):
    def __init__(self):
        logger.debug("SMTPFactory initialized")

    def buildProtocol(self, addr):
        logger.debug(f"Building SMTP protocol for {addr}")
        return SMTPProtocol()