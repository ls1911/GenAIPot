# src/smtp/smtp_banner.py
from datetime import datetime

class SMTPBanner:
    def __init__(self, domain_name, technology):
        self.domain_name = domain_name
        self.technology = technology

    def get_banner(self):
        if self.technology.lower() == 'exchange':
            current_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
            return f"220 {self.domain_name} Microsoft ESMTP MAIL Service ready at {current_date}"
        return f"220 {self.domain_name} ESMTP"