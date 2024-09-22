# src/smtp/rate_limiter.py
import time
import logging
from twisted.internet import reactor

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, rate_limit):
        self.rate_limit = rate_limit
        self.connection_attempts = {}

    def allow_connection(self, ip):
        current_time = time.time()
        attempts = self.connection_attempts.get(ip, [])

        # Remove attempts older than 1 minute
        attempts = [t for t in attempts if current_time - t < 60]

        attempts.append(current_time)
        self.connection_attempts[ip] = attempts

        if len(attempts) > self.rate_limit:
            reactor.callLater(60, self._unblock_ip, ip)
            return False
        return True

    def _unblock_ip(self, ip):
        if ip in self.connection_attempts:
            del self.connection_attempts[ip]
            logger.debug(f"IP {ip} has been unblocked after rate limiting period.")