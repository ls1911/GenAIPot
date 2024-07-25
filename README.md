
# GenAIPot
🄶🄴🄽🄰🄸🄿🄾🅃
G̲e̲n̲A̲I̲P̲o̲t̲

GenAIPot is a sophisticated honeypot that emulates a POP3 server. It uses various AI services to generate realistic responses to POP3 commands, logs all interactions to an SQLite database, and provides capabilities for anomaly detection and predictions using machine learning. It supports multiple AI services, including OpenAI, Azure OpenAI, and Google Vertex AI.
Genaipot POP3 Server

Overview

Genaipot POP3 Server is a custom implementation of the Post Office Protocol version 3 (POP3) and Simple Mail Transfer Protocol (SMTP) using Twisted, an event-driven networking engine in Python. This server supports standard email operations such as user authentication, email retrieval, deletion, and session termination. It integrates AI-generated responses to provide dynamic and customizable email content and interactions. Additionally, the server includes analytics capabilities for monitoring and anomaly detection.

Protocol Descriptions

POP3 (Post Office Protocol Version 3)

POP3 is a standard mail protocol used to retrieve emails from a remote server to a local client. It operates over a TCP connection and follows a straightforward request-response model. Key features of POP3 include:

Authentication: Clients authenticate using a username and password.
Mail Retrieval: Emails are downloaded from the server to the client.
Session Management: Sessions can be established, maintained, and terminated. Messages can be marked for deletion during a session.
Typical commands in POP3 include:

USER: Specify the username for authentication.
PASS: Provide the password for the user account.
STAT: Get the number of messages and total size in the mailbox.
LIST: Get a list of messages with their sizes.
RETR: Retrieve a specific message.
DELE: Mark a specific message for deletion.
QUIT: End the session and optionally delete marked messages.
SMTP (Simple Mail Transfer Protocol)

SMTP is a protocol used to send emails from a client to a server or between servers. It is a text-based protocol, where one or more recipients of a message are specified, and the message text is transferred. SMTP commands include:

HELO: Greet the server, identify the client.
MAIL FROM: Specify the sender’s email address.
RCPT TO: Specify the recipient’s email address.
DATA: Start the transfer of the message content.
QUIT: End the session.
SMTP is designed for the reliable and efficient transmission of emails, primarily used for sending and routing messages across networks.

Project Description

Genaipot POP3 Server provides a robust implementation of the POP3 and SMTP protocols, allowing users to interact with an AI-driven email service. The server can serve AI-generated email content and provide responses to POP3 commands, simulating a real-world email server environment. It also includes analytics capabilities for monitoring server activity and detecting anomalies.

Analytics Capabilities

The server includes a comprehensive analytics module that can perform predictions, detect anomalies, and generate graphical reports. The analytics are performed using historical data collected from server logs.

Features

Perform Predictions: Uses the Prophet model to predict future command activity based on historical data.
Detect Anomalies: Identifies unusual patterns in command activity and IP addresses connecting to the server.
Generate Graphs: Visualizes key metrics such as the most connected IP addresses and connection patterns over the last 24 hours.
Analytics Functions

perform_prediction(df): This function takes a DataFrame df with server activity logs and predicts future activity using the Prophet model. The results are saved to future_forecast.csv.

detect_anomalies(df): This function detects anomalies in server activity by analyzing command lengths and IP address activity. It uses the Prophet model to forecast expected values and flags deviations as anomalies. The results are saved to command_anomalies.csv and ip_anomalies.csv.

generate_graphs(df): This function generates and saves graphs, including the top 10 most connected IP addresses and the number of connections in the last 24 hours. The graphs are saved as top_ips.png and connections_last_24_hours.png.

Installation

Prerequisites

Python 3.7 or higher
Twisted library
Prophet library for analytics
Installation Steps

Clone the repository:
git clone https://github.com/yourusername/genaipot-pop3.git
cd genaipot-pop3

Create and activate a virtual environment (optional but recommended):
python3 -m venv venv
source venv/bin/activate  # On Windows, use venv\Scripts\activate

Install the required packages:
pip install -r requirements.txt

Configuration

The server uses a configuration file named config.ini for setting up various parameters. This file can be customized to control server behavior and AI responses. The –config option allows specifying the path to a configuration file.

Config.ini Fields

domain: Specifies the domain name used in server responses (e.g., yourdomain.com).
technology: Defines the email technology being emulated, such as sendmail or postfix.
debug: A boolean flag (True or False) to enable or disable debug logging.
api_key: The API key for accessing OpenAI’s services to fetch AI-generated responses.
Example config.ini:
[server]
domain = yourdomain.com
technology = sendmail
debug = True

[openai]
api_key = your_openai_api_key

Using –config

The –config command-line option is used to specify the configuration file to be loaded. By default, the server looks for config.ini in the current directory. However, you can specify a different path using –config:

python3 main.py –config path/to/your_config.ini

This allows for flexible configuration management, making it easy to switch between different environments or settings.

Running the Server

To start the server, use:

python3 main.py –config

This command initializes the POP3 server with settings from the config.ini file, including AI configurations and server settings.

Logging

Logging is set up to capture detailed information about server activities, including debug information if enabled. This is useful for monitoring, troubleshooting, and analyzing server performance.

Customization

AI-Generated Responses: The server can use AI-generated responses for email commands, stored and managed in the ai_services.py file.
Email Content: Customize the raw email content in the files directory, which the server reads and serves to clients.
Troubleshooting

Connection Issues: Ensure the server is running and accessible. Verify network settings and firewall rules.
Command Not Recognized: Check the command syntax. Refer to server logs for detailed information.
Authentication Errors: Verify the username and password.
License

This project is licensed under the MIT License. See the LICENSE file for details.

Contributing

Contributions are welcome! Please submit pull requests or open issues for discussions on improvements and new features.

Contact

For any questions or support, please contact [your email address].