# src/smtp/config_manager.py
import configparser
import os
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'etc', 'config.ini')
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_path):
            self.config.read(self.config_path)
        else:
            logger.error(f"Configuration file not found at {self.config_path}")

    def get(self, section, option, fallback=None):
        return self.config.get(section, option, fallback=fallback)

    def getboolean(self, section, option, fallback=False):
        return self.config.getboolean(section, option, fallback=fallback)

    def getint(self, section, option, fallback=0):
        return self.config.getint(section, option, fallback=fallback)