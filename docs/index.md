
# 🄶🄴🄽🄰🄸🄿🄾🅃

![Build Status](https://img.shields.io/github/actions/workflow/status/your-username/your-repo/main.yml?branch=main&style=flat-square)
![Coverage](https://img.shields.io/codecov/c/github/your-username/your-repo?style=flat-square)
![License](https://img.shields.io/github/license/your-username/your-repo?style=flat-square)
![Python Version](https://img.shields.io/badge/python-3.7%2B-blue?style=flat-square)
![Contributors](https://img.shields.io/github/contributors/your-username/your-repo?style=flat-square)
![Last Commit](https://img.shields.io/github/last-commit/your-username/your-repo?style=flat-square)

GenAIPot is the first a.i honeypot that emulates mail services.

It uses various AI services to generate realistic responses to both POP3 and SMTP commands, logs all interactions to an SQLite database, and provides capabilities for anomaly detection and predictions using machine learning.


## Overview

Genaipot contains a custom implementation of the Post Office Protocol version 3 (POP3) and Simple Mail Transfer Protocol (SMTP) using Twisted framework in Python.

It supports standard email operations such as user authentication, email retrieval, deletion, and session termination.

It integrates AI-generated responses to provide dynamic and customizable email content and interactions. Additionally, the server includes analytics capabilities for monitoring and anomaly detection.

This app is not meant to be used in production systems , if you do, do it at your own risk.

GenAIPot created by Nucleon Cyber (www.nucleon.sh) as part of its advanced Adversary Generated Threat Intelligence (AGTI) platform. 
If you wish to use this version or more advanced versions in production settings or if you want to hear more about the most advanced AGTI platform, you welcome to contact the project admins