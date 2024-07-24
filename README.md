
# GenAIPot
🄶🄴🄽🄰🄸🄿🄾🅃
G̲e̲n̲A̲I̲P̲o̲t̲

GenAIPot is a sophisticated honeypot that emulates a POP3 server. It uses various AI services to generate realistic responses to POP3 commands, logs all interactions to an SQLite database, and provides capabilities for anomaly detection and predictions using machine learning. It supports multiple AI services, including OpenAI, Azure OpenAI, and Google Vertex AI.

## [](#features)Features

-   Emulates a POP3 server using the Twisted networking framework.
-   Generates realistic POP3 responses using OpenAI, Azure OpenAI, or Google Vertex AI.
-   Logs all connections and commands to an SQLite database.
-   Provides anomaly detection and predictions using the Prophet library.
-   Generates graphical representations of the data.

## [](#installation)Installation

### [](#prerequisites)Prerequisites

Ensure you have the following installed:

-   Python 3.7 or higher
-   pip

### [](#install-required-libraries)Install Required Libraries

```
pip install openai azure-ai openai[azure] google-cloud-aiplatform python-dotenv pandas scikit-learn fbprophet email asyncio sqlite3 matplotlib twisted```

###Configuration
Create a config.ini file in the project root with the following content:
```

[openai] api_key = YOUR_OPENAI_API_KEY

[azure] api_key = YOUR_AZURE_OPENAI_API_KEY endpoint = YOUR_AZURE_OPENAI_ENDPOINT deployment_name = YOUR_AZURE_OPENAI_DEPLOYMENT_NAME

[gcp] project_id = YOUR_GCP_PROJECT_ID model_name = YOUR_GCP_MODEL_NAME


Replace the placeholder values with your actual API keys and endpoints.

# Usage

### Running GenAIPot
Start server: python main.py

### Command-Line Arguments


	•	--predict: Perform prediction on collected data.
	•	--anomaly: Perform anomaly detection on collected data.
	•	--graphs: Generate graphical graphs and textual descriptions.
	•	--azure: Use Azure OpenAI Service instead of OpenAI API.
	•	--gcp: Use Google Vertex AI instead of OpenAI API.
	•	--help: Show help message and exit.

Acknowledgements

	•	OpenAI
	•	Azure OpenAI Service
	•	Google Vertex AI
	•	Twisted
	•	Prophet
```