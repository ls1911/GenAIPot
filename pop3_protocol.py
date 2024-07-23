import logging
from twisted.protocols.basic import LineReceiver
from twisted.internet import protocol
from ai_services import AIService
from database import log_interaction
import configparser

logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read('config.ini')
domain_name = config.get('server', 'domain', fallback='localhost')
technology = config.get('server', 'technology', fallback='generic')

class POP3Protocol(LineReceiver):
    def __init__(self):
        self.ip = None
        self.ai_service = AIService()
        responses = self.ai_service.load_responses()
        logger.debug(f"Loaded responses: {responses}")
        self.responses = self._format_responses(responses)
        self.state = 'INITIAL'
        logger.debug("POP3Protocol initialized")

    def connectionMade(self):
        self.ip = self.transport.getPeer().host
        banner = self._get_banner()
        logger.info(f"Connection from {self.ip}")
        self.sendLine(banner.encode('utf-8'))
        log_interaction(self.ip, 'WELCOME', banner)

    def _get_banner(self):
        return self.responses.get("220", f"+OK {domain_name} {technology} POP3 server ready")

    def lineReceived(self, line):
        try:
            command = line.decode('utf-8').strip()
            logger.info(f"Received command: {command}")
            response = self._get_response(command)
            self.sendLine(response.encode('utf-8'))
            log_interaction(self.ip, command, response)

            if command.upper().startswith("QUIT"):
                self.transport.loseConnection()
        except UnicodeDecodeError as e:
            logger.error(f"Unicode decode error: {e}")
            self.sendLine(b"-ERR Command unrecognized")

    def _get_response(self, command):
        command_upper = command.upper()
        if command_upper.startswith("USER"):
            return self.responses.get("USER", "+OK User accepted")
        elif command_upper.startswith("PASS"):
            return self.responses.get("PASS", "+OK Pass accepted")
        elif command_upper.startswith("STAT"):
            return self.responses.get("STAT", "+OK 0 0")
        elif command_upper.startswith("LIST"):
            return self.responses.get("LIST", "+OK No messages")
        elif command_upper.startswith("RETR"):
            return self.responses.get("RETR", "+OK No messages")
        elif command_upper.startswith("DELE"):
            return self.responses.get("DELE", "+OK No messages")
        elif command_upper.startswith("QUIT"):
            return self.responses.get("QUIT", "+OK Goodbye")
        else:
            return self.responses.get("ERR", "-ERR Command unrecognized")

    def _format_responses(self, responses):
        if isinstance(responses, list):
            formatted_responses = {}
            for item in responses:
                if isinstance(item, dict):
                    code = item.get('response_code')
                    description = item.get('description')
                    if code and description:
                        formatted_responses[f"{code}"] = f"{description}"
                else:
                    logger.error(f"Unexpected item format: {item}")
            return formatted_responses
        else:
            logger.error(f"Unexpected responses format: {responses}")
            return {}

class POP3Factory(protocol.Factory):
    def __init__(self):
        logger.debug("POP3Factory initialized")

    def buildProtocol(self, addr):
        logger.debug(f"Building POP3 protocol for {addr}")
        return POP3Protocol()