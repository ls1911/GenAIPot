
# G̲e̲n̲A̲I̲P̲o̲t̲

![License](https://img.shields.io/badge/license-%20%20GNU%20GPLv3%20-green?style=plastic&logo=GNU)
![Python Version](https://img.shields.io/badge/python-3.12%2B-blue?style=flat-square&logo=Python)
[![Deploy Documentation](https://github.com/ls1911/GenAIPot/actions/workflows/static.yml/badge.svg)](https://github.com/ls1911/GenAIPot/actions/workflows/static.yml)
![Lint with Pylint](https://github.com/ls1911/GenAIPot/actions/workflows/lint.yml/badge.svg)
[![Publish Docker image](https://github.com/ls1911/GenAIPot/actions/workflows/docker.yml/badge.svg)](https://github.com/ls1911/GenAIPot/actions/workflows/docker.yml)
![Security Checks](https://github.com/ls1911/GenAIPot/actions/workflows/codeql.yml/badge.svg)
<a href="https://genaipot.zulipchat.com/#narrow/stream/451830-genaipot/topic/Welcome">![Live Support](https://img.shields.io/badge/Support-ZulipChat-green?logo=cachet)</a>


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

Read for use docker image is available at docker hub
```
docker pull annls/genaipot:latest
docker run -dp25:25 -p110:110 annls/genaipot
```

### Prerequisites

Python 3.7 or higher
Twisted library
Installation Steps
OpenAI key

Normal Installation (*nix,mac):

```
git clone https://github.com/yourusername/genaipot-pop3.git
cd genaipot
#Create and activate a virtual environment (optional but recommended):
python3 -m venv venv
source venv/bin/activate
#Install the required packages:
pip install -r requirements.txt
```

## Windows Installation

###Important! Dont forget to install Microsoft Visual C++ Build Tools from Microsoft site (https://visualstudio.microsoft.com/visual-cpp-build-tools/)
open cmd.exe
```
> python3 -m venv venv
>  .\venv\Scripts\activate
> python3 install_requirements.py
(install needed deps on windows, this script will continue even if there are errors, script still under development, windows really dont like pip)
```
Looking for better way to perform windows installation , suggestions welcome.

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

You are welcome to join the project space on ZulipChat
https://genaipot.zulipchat.com/#narrow/stream/451830-genaipot/topic/Welcome

For any questions or support, either open an issue , contact by mail or use ZulipChat.
This app is not meant to be used (But we know it is being used) in production systems , if you do, do it at your own risk.

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

# What is the intro.py file used for ???

In the warez scene of the 1990s, it was common for cracked software (software that had its copy protection removed) to come bundled with a “demo” or “intro” file. 
These intro files were essentially digital calling cards created by the cracking groups. 
They were used to showcase the group’s skills and creativity, often featuring flashy animations, pixel art, scrolling text, and sometimes music.

These intros served multiple purposes:

	1.	Bragging Rights: Cracking groups wanted to show off their skills not just in bypassing software protection but also in creating impressive visual and audio effects. It was a way to gain reputation in the warez community.
	2.	Identity: The intros were a form of branding. Each cracking group had its own style and identity, and the intros were a way to stamp their name on the cracked software.
	3.	Entertainment: These intros were often fun and creative, adding a layer of entertainment to the software cracking scene. They were like mini digital art pieces, making the process of obtaining and using cracked software more than just about the software itself.

The intro.py file you have see is a modern take on those old-school warez intros. 

	•	Text Art: The large “Nucleon” text created using the art library mimics the kind of bold, attention-grabbing logos seen in many warez intros.
	•	ASCII Art: The images of the bird and computer are created using text characters. This kind of art was common in the 90s intros because it could be rendered on any screen, regardless of graphical capabilities.
	•	Animation: The script animates the ASCII art, making it appear as if the bird is flying or moving across the screen, reminiscent of the animated sequences often seen in warez intros.
	•	Music Playback: By playing a music file, the script completes the multimedia experience that was typical of warez intros.

In short, intro.py script is a homage to the warez intros from the 90s, bringing back the creativity and flair of that era in a modern format using Python. happy ?
