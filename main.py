import argparse
from twisted.internet import reactor
from protocol import POP3Factory
from analytics import perform_prediction, detect_anomalies, generate_graphs
from database import setup_database, collect_honeypot_data
import configparser

def main():
    parser = argparse.ArgumentParser(description="GenAIPot with Anomaly Detection and Prediction")
    parser.add_argument('--predict', action='store_true', help="Perform prediction on collected data")
    parser.add_argument('--anomaly', action='store_true', help="Perform anomaly detection on collected data")
    parser.add_argument('--graphs', action='store_true', help="Generate graphical graphs and textual descriptions")
    parser.add_argument('--azure', action='store_true', help="Use Azure OpenAI Service instead of OpenAI API")
    parser.add_argument('--gcp', action='store_true', help="Use Google Vertex AI instead of OpenAI API")
    parser.add_argument('--help', action='help', help="Show this help message and exit")

    args = parser.parse_args()

    setup_database()

    if args.predict:
        print("Predicting future commands...")
        honeypot_data = collect_honeypot_data()
        perform_prediction(honeypot_data)
    elif args.anomaly:
        print("Detecting anomalies in commands and IP addresses...")
        honeypot_data = collect_honeypot_data()
        detect_anomalies(honeypot_data)
    elif args.graphs:
        print("Generating graphs and descriptions...")
        honeypot_data = collect_honeypot_data()
        generate_graphs(honeypot_data)
    else:
        print("Starting GenAIPot on port 110...")
        reactor.listenTCP(110, POP3Factory(use_azure=args.azure, use_gcp=args.gcp))
        reactor.run()

if __name__ == "__main__":
    main()