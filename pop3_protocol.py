from twisted.protocols.basic import LineReceiver
from twisted.internet import protocol
from datetime import datetime
from ai_services import AIService
from database import log_interaction

class POP3Protocol(LineReceiver):
    def __init__(self, use_azure=False, use_gcp=False):
        self.ip = None
        self.ai_service = AIService(use_azure=use_azure, use_gcp=use_gcp)

    def connectionMade(self):
        self.ip = self.transport.getPeer().host
        print(f"Connection from {self.ip}")
        self.sendLine(b"+OK POP3 server ready")
        log_interaction(self.ip, 'WELCOME', '+OK POP3 server ready')

    def lineReceived(self, line):
        command = line.decode('utf-8').strip()
        print(f"Received command: {command}")
        
        if command.upper() == "QUIT":
            response = "+OK POP3 server signing off"
            self.sendLine(response.encode('utf-8'))
            log_interaction(self.ip, command, response)
            self.transport.loseConnection()
        else:
            response = self.ai_service.generate_response(command)
            self.sendLine(response.encode('utf-8'))
            log_interaction(self.ip, command, response)

class POP3Factory(protocol.Factory):
    def __init__(self, use_azure=False, use_gcp=False):
        self.use_azure = use_azure
        self.use_gcp = use_gcp

    def buildProtocol(self, addr):
        return POP3Protocol(use_azure=self.use_azure, use_gcp=self.use_gcp)