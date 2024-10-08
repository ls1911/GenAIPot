# Copyright (C) 2024 Nucleon Cyber. All rights reserved.
#
# This file is part of GenAIPot.
#
# GenAIPot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# GenAIPot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GenAIPot. If not, see <http://www.gnu.org/licenses/>.
#
# For more information, visit: www.nucleon.sh or send email to contact[@]nucleon.sh
#

"""
This module provides functions for analyzing command data, detecting anomalies, 
and generating graphs for visualization in GenAIPot.
"""

from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from prophet import Prophet

def perform_prediction(df):
    """
    Perform predictions on the length of commands over time using Prophet.

    Args:
        df (DataFrame): DataFrame containing 'timestamp' and 'command' columns.

    Returns:
        None
    """
    df['y'] = df['command'].str.len()
    df['ds'] = pd.to_datetime(df['timestamp'])
    df = df[['ds', 'y']]

    model = Prophet()
    model.fit(df)
    future = model.make_future_dataframe(periods=30, freq='S')
    forecast = model.predict(future)

    forecast.to_csv("future_forecast.csv", index=False)
    print("Prediction complete. Results saved to future_forecast.csv")

def detect_anomalies(df):
    """
    Detect anomalies in the command lengths and IP address connection frequencies.

    Args:
        df (DataFrame): DataFrame containing 'timestamp', 'command', and 'ip' columns.

    Returns:
        None
    """
    # Ensure 'timestamp', 'command', and 'ip' columns are present
    if not all(col in df.columns for col in ['timestamp', 'command', 'ip']):
        raise ValueError("DataFrame must contain 'timestamp', 'command', and 'ip' columns")

    # Prepare the DataFrame for command length anomaly detection
    df['y'] = df['command'].str.len()
    df['ds'] = pd.to_datetime(df['timestamp'])
    df_command = df[['ds', 'y']].copy()  # Use a copy to avoid SettingWithCopyWarning

    model_command = Prophet()
    model_command.fit(df_command)
    future_command = model_command.make_future_dataframe(periods=30, freq='S')
    forecast_command = model_command.predict(future_command)

    # Align the indices of the DataFrame and forecast
    forecast_command = forecast_command.set_index('ds').reindex(df_command['ds']).reset_index()

    df_command['anomaly'] = df_command['y'] > forecast_command['yhat_upper']
    df_command.to_csv("command_anomalies.csv", index=False)
    forecast_command.to_csv("command_forecast.csv", index=False)

    # Prepare the DataFrame for IP connection frequency anomaly detection
    df_ip = df.groupby('ip').size().reset_index(name='counts')
    df_ip['ds'] = pd.to_datetime(df_ip['ip'], errors='coerce')
    df_ip = df_ip.dropna().reset_index(drop=True)  # Drop rows with NaT ds values

    model_ip = Prophet()
    model_ip.fit(df_ip)
    future_ip = model_ip.make_future_dataframe(periods=30, freq='D')
    forecast_ip = model_ip.predict(future_ip)

    # Align the indices of the DataFrame and forecast
    forecast_ip = forecast_ip.set_index('ds').reindex(df_ip['ds']).reset_index()

    df_ip['anomaly'] = df_ip['counts'] > forecast_ip['yhat_upper']
    df_ip.to_csv("ip_anomalies.csv", index=False)
    forecast_ip.to_csv("ip_forecast.csv", index=False)

    print("Anomaly detection complete. Results saved to command_anomalies.csv, command_forecast.csv, ip_anomalies.csv, and ip_forecast.csv")
    
def generate_graphs(df):
    """
    Generate and save graphs for top connected IPs and connections over the last 24 hours.

    Args:
        df (DataFrame): DataFrame containing 'ip' and 'timestamp' columns.

    Returns:
        None
    """
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
    plt.show()

    plt.figure(figsize=(10, 6))
    connections_per_hour.plot(kind='line')
    plt.title('Connections in the Last 24 Hours')
    plt.xlabel('Hour')
    plt.ylabel('Number of Connections')
    plt.savefig('connections_last_24_hours.png')
    plt.show()

    print("Graphs have been generated and saved.")
