
# G̲e̲n̲A̲I̲P̲o̲t̲

![License](https://img.shields.io/badge/license-%20%20GNU%20GPLv3%20-green?style=plastic)
![Python Version](https://img.shields.io/badge/python-3.12%2B-blue?style=flat-square)
[![Deploy static content to Pages](https://github.com/ls1911/GenAIPot/actions/workflows/static.yml/badge.svg)](https://github.com/ls1911/GenAIPot/actions/workflows/static.yml)
![Lint with Pylint](https://github.com/ls1911/GenAIPot/actions/workflows/lint.yml/badge.svg)
[![Publish Docker image](https://github.com/ls1911/GenAIPot/actions/workflows/docker.yml/badge.svg)](https://github.com/ls1911/GenAIPot/actions/workflows/docker.yml)
![Coverage](https://img.shields.io/badge/build-pass-blue)
[![CodeQL](https://github.com/ls1911/GenAIPot/actions/workflows/codeql.yml/badge.svg


### GenAIPot the first open source A.I honeypot

## Overview

GenAIPot contains a custom implementation of the Post Office Protocol version 3 (POP3) and Simple Mail Transfer Protocol (SMTP) using Twisted framework in Python.
It supports standard email operations such as user authentication, email retrieval, deletion, and session termination.
It integrates AI-generated responses to provide dynamic and customizable email content and interactions. Additionally, the server includes analytics capabilities for monitoring and anomaly detection.

**Dont forget to check documentation for more details**


![t](/docs/images/abc.png)

## Usage Example
Generate content for emails in the server , customize responses using A.I service and test the service.
![Demo GIF](docs/fulldemo.gif)

## Docker (basic/default) Usage Example

Here's a demo of the tool in action:
![Demo GIF](docs/demo.gif)


## Installation

### Using PreMade Docker Image

Read for use docker image is availble at docker hub
```
docker pull annls/genaipot:latest
docker run -dp25:25 -p110:110 annls/genaipot
```

### Prerequisites

Python 3.7 or higher
Twisted library
Installation Steps
OpenAI key

Installation:

```
git clone https://github.com/yourusername/genaipot-pop3.git
cd genaipot
#Create and activate a virtual environment (optional but recommended):
python3 -m venv venv
source venv/bin/activate  # On Windows, use venv\Scripts\activate
#Install the required packages:
pip install -r requirements.txt
```

## Configuration

The server uses a configuration file named config.ini for setting up various parameters. This file can be customized to control server behavior and AI responses. The –-config option allows specifying the path to a configuration file.

## Running the Server

To start the server with configuration wizard, use:
```
python3 bin/genaipot.py –-config
```

This allows for flexible configuration management, making it easy to switch between different environments or settings, 
it will create config.ini based on reposnses

### Starting the app
use --pop3 , --smtp or --all to start the server


### Logging

Logging is set up to capture detailed information about server activities, including debug information if enabled. This is useful for monitoring, troubleshooting, and analyzing server performance.

## Customization

AI-Generated Responses: The server can use AI-generated responses for email commands, stored and managed in the ai_services.py file.
Email Content: Customize the raw email content in the files directory, which the server reads and serves to clients.

## Troubleshooting

### Connection Issues: 
Ensure the server is running and accessible. Verify network settings and firewall rules.

### Command Not Recognized: 
Check the command syntax. Refer to server logs for detailed information.


## License

This project is licensed under the GPLv3 License. See the LICENSE file for details.

## Contributing

Contributions are welcome! Please submit pull requests or open issues for discussions on improvements and new features.

## Contact

For any questions or support, either open an issue or contact by mail.
This app is not meant to be used in production systems , if you do, do it at your own risk.

GenAIPot created by Nucleon Cyber (www.nucleon.sh) as part of its advanced Adversary Generated Threat Intelligence (AGTI) platform. 
If you wish to use this version or more advanced versions in production settings or if you want to hear more about the most advanced AGTI platform, you welcome to contact the project admins or by mail contact@nucleon.sh

## Protocol Descriptions

### POP3 (Post Office Protocol Version 3)

POP3 is a standard mail protocol used to retrieve emails from a remote server to a local client. It operates over a TCP connection and follows a straightforward request-response model. Key features of POP3 include:

Authentication: Clients authenticate using a username and password.
Mail Retrieval: Emails are downloaded from the server to the client.
Session Management: Sessions can be established, maintained, and terminated. Messages can be marked for deletion during a session.
Typical commands in POP3 include:

- USER: Specify the username for authentication.
- PASS: Provide the password for the user account.
- STAT: Get the number of messages and total size in the mailbox.
- LIST: Get a list of messages with their sizes.
- RETR: Retrieve a specific message.
- DELE: Mark a specific message for deletion.
- QUIT: End the session.

### SMTP (Simple Mail Transfer Protocol)

SMTP is a protocol used to send emails from a client to a server or between servers. It is a text-based protocol, where one or more recipients of a message are specified, and the message text is transferred. SMTP commands include:

- HELO: Greet the server, identify the client.
- MAIL FROM: Specify the sender’s email address.
- RCPT TO: Specify the recipient’s email address.
- DATA: Start the transfer of the message content.
- QUIT: End the session.
