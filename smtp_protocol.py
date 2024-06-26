from twisted.protocols.basic import LineReceiver
from twisted.internet import protocol
from datetime import datetime
from ai_services import AIService
from database import log_interaction

class SMTPProtocol(LineReceiver):
    def __init__(self, use_azure=False, use_gcp=False):
        self.ip = None
        self.ai_service = AIService(use_azure=use_azure, use_gcp=use_gcp)
        self.state = 'INITIAL'

    def connectionMade(self):
        self.ip = self.transport.getPeer().host
        print(f"Connection from {self.ip}")
        self.sendLine(b"220 SMTP server ready")
        log_interaction(self.ip, 'WELCOME', '220 SMTP server ready')

    def lineReceived(self, line):
        command = line.decode('utf-8').strip()
        print(f"Received command: {command}")

        response = ""
        if command.upper().startswith("HELO") or command.upper().startswith("EHLO"):
            response = "250 Hello"
            self.state = 'HELO'
        elif command.upper().startswith("MAIL FROM"):
            response = "250 OK"
            self.state = 'MAIL_FROM'
        elif command.upper().startswith("RCPT TO"):
            response = "250 OK"
            self.state = 'RCPT_TO'
        elif command.upper().startswith("DATA"):
            response = "354 End data with <CR><LF>.<CR><LF>"
            self.state = 'DATA'
        elif command == ".":
            response = "250 OK"
            self.state = 'INITIAL'
        elif command.upper().startswith("QUIT"):
            response = "221 Bye"
            self.sendLine(response.encode('utf-8'))
            log_interaction(self.ip, command, response)
            self.transport.loseConnection()
            return
        else:
            response = self.ai_service.generate_response(command)

        self.sendLine(response.encode('utf-8'))
        log_interaction(self.ip, command, response)

class SMTPFactory(protocol.Factory):
    def __init__(self, use_azure=False, use_gcp=False):
        self.use_azure = use_azure
        self.use_gcp = use_gcp

    def buildProtocol(self, addr):
        return SMTPProtocol(use_azure=self.use_azure, use_gcp=self.use_gcp)