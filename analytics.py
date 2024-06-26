import pandas as pd
import matplotlib.pyplot as plt
from fbprophet import Prophet
from datetime import datetime, timedelta

def perform_prediction(df):
    df['y'] = df['command'].apply(lambda x: len(x))
    df['ds'] = pd.to_datetime(df['timestamp'])
    df = df[['ds', 'y']]

    model = Prophet()
    model.fit(df)
    future = model.make_future_dataframe(periods=30, freq='S')
    forecast = model.predict(future)

    forecast.to_csv("future_forecast.csv", index=False)
    print("Prediction complete. Results saved to future_forecast.csv")

def detect_anomalies(df):
    df['y'] = df['command'].apply(lambda x: len(x))
    df['ds'] = pd.to_datetime(df['timestamp'])
    df = df[['ds', 'y']]

    model = Prophet()
    model.fit(df)
    future = model.make_future_dataframe(periods=30, freq='S')
    forecast = model.predict(future)

    df['anomaly'] = df['y'] > forecast['yhat_upper']
    df.to_csv("command_anomalies.csv", index=False)
    forecast.to_csv("command_forecast.csv", index=False)

    df_ip = df.groupby('ip').size().reset_index(name='counts')
    df_ip['ds'] = pd.to_datetime(df_ip['ip'])
    df_ip = df_ip[['ds', 'counts']]

    model = Prophet()
    model.fit(df_ip)
    future = model.make_future_dataframe(periods=30, freq='D')
    forecast = model.predict(future)

    df_ip['anomaly'] = df_ip['counts'] > forecast['yhat_upper']
    df_ip.to_csv("ip_anomalies.csv", index=False)
    forecast.to_csv("ip_forecast.csv", index=False)

    print("Anomaly detection complete. Results saved to command_anomalies.csv, command_forecast.csv, ip_anomalies.csv, and ip_forecast.csv")

def generate_graphs(df):
    top_ips = df['ip'].value_counts().head(10)
    print("Top 10 most connected IP addresses:")
    print(top_ips)

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    last_24_hours = df[df['timestamp'] > datetime.now() - timedelta(days=1)]
    connections_per_hour = last_24_hours.set_index('timestamp').resample('H').size()

    plt.figure(figsize=(10, 6))
    top_ips.plot(kind='bar')
    plt.title('Top 10 Most Connected IP Addresses')
    plt.xlabel('IP Address')
    plt.ylabel('Number of Connections')
    plt.savefig('top_ips.png')
   