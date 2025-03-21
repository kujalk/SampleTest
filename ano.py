import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model
import pickle
from sklearn.preprocessing import LabelEncoder, RobustScaler
from datetime import datetime
import matplotlib.pyplot as plt
import time

# Load the model
model = load_model('anomaly_detection_4hr_data_future_win5.keras')

# Load the label encoders from a file
with open('label_encoders.pkl', 'rb') as f:
    label_encoders = pickle.load(f)

print("Label encoders and scaler have been loaded.")

# Function to preprocess data
def preprocess_data(df):
    # Merge 'forest' and 'adsite' into 'forest_adsite'
    df['forest_adsite'] = df['forest'] + '_' + df['adsite']
    
    # Encode categorical features
    for col in ['target', 'datacenter', 'testsource', 'domain', 'forest', 'targetenvironment', 'forest_adsite']:
        if col not in label_encoders:
            label_encoders[col] = LabelEncoder()
            df[col] = label_encoders[col].fit_transform(df[col])
        else:
            df[col] = label_encoders[col].transform(df[col])
    
    # Scale numerical features
    scaler = RobustScaler()
    df['transactiontime'] = scaler.fit_transform(df[['transactiontime']])
    
    # Drop columns that are no longer needed
    df.drop(columns=['adsite', 'result', 'timestamp'], inplace=True)
    
    return df, scaler

# Function to create sequences for the model
def create_sequences(data, sequence_length=30, future_window=5):
    X = []
    for i in range(len(data) - sequence_length - future_window + 1):
        X.append(data.iloc[i:(i + sequence_length)].values)
    return np.array(X)

# Simulate real-time processing and alert detection
def simulate_real_time_processing(csv_file_path, window_size=30, future_window=5, plot_interval=5):
    # Set up parameters
    chunk_size = 100  # Number of rows to process at a time
    
    # Initialize data container
    accumulated_data = pd.DataFrame()
    
    # For plotting
    all_real_values = []
    all_predicted_values = []
    all_anomalies = []
    
    # Create a live plot
    plt.figure(figsize=(12, 6))
    plt.ion()  # Turn on interactive mode
    
    # Read CSV in chunks to simulate real-time data
    for chunk in pd.read_csv(csv_file_path, chunksize=chunk_size, parse_dates=['timestamp']):
        # Preprocess the new data
        new_data, current_scaler = preprocess_data(chunk)
        
        # Accumulate data
        accumulated_data = pd.concat([accumulated_data, new_data], ignore_index=True)
        
        # Check if accumulated data has enough rows for a sequence
        if len(accumulated_data) < window_size + future_window:
            print(f"Not enough data to form a sequence. Have {len(accumulated_data)} rows, need {window_size + future_window}.")
            time.sleep(2)  # Sleep for 2 seconds
            continue
        
        # Create sequences for prediction - FIXED WINDOWING
        sequences = create_sequences(accumulated_data, window_size, future_window)
        
        # Make predictions
        predictions = model.predict(sequences)
        
        # Get the corresponding actual values for comparison
        actuals = []
        for i in range(len(sequences)):
            start_idx = i + window_size
            end_idx = start_idx + future_window
            if end_idx <= len(accumulated_data):
                actuals.append(accumulated_data.iloc[start_idx:end_idx]['transactiontime'].values)
        
        actuals = np.array(actuals)
        
        # Inverse transform predictions and actuals
        predictions_original = current_scaler.inverse_transform(predictions.reshape(-1, 1)).flatten()
        actuals_original = current_scaler.inverse_transform(actuals.reshape(-1, 1)).flatten()
        
        # Calculate errors and determine alerts - using the approach from the screenshot
        aligned_predictions = predictions_original
        aligned_transaction_times = actuals_original
        
        errors = aligned_transaction_times - aligned_predictions  # Only consider when predicted < real
        thresholds = np.percentile(errors, 95)  # Lower percentile for more sensitivity
        print(errors)
        print(thresholds)
        anomalies = (errors > thresholds) & (aligned_predictions < aligned_transaction_times)
        
        # Limit the graph to a maximum of 250 data points
        max_length = 250
        if len(aligned_transaction_times) > max_length:
            start_index = max(0, len(aligned_transaction_times) - max_length)
            aligned_predictions = aligned_predictions[start_index:]
            aligned_transaction_times = aligned_transaction_times[start_index:]
            anomalies = anomalies[start_index:]
        
        # Store values for plotting
        all_real_values = aligned_transaction_times
        all_predicted_values = aligned_predictions
        all_anomalies = anomalies
        
        # Check for at least 3 anomalies in windows of 5
        alert_generated = False
        for i in range(0, len(anomalies) - 4):
            if np.sum(anomalies[i:i+5]) >= 3:
                alert_generated = True
                break
        
        # Plot the results
        plt.clf()
        plt.plot(all_real_values, label='Real Value', color='blue')
        plt.plot(all_predicted_values, label='Predicted Value', color='green')
        
        # Plot anomalies
        anomaly_indices = np.where(all_anomalies)[0]
        if len(anomaly_indices) > 0:
            plt.scatter(anomaly_indices, [all_predicted_values[i] for i in anomaly_indices], color='red', label='Anomaly')
        
        # Add horizontal line for threshold
        plt.axhline(y=thresholds + np.min(all_predicted_values), color='orange', linestyle='--', label='Threshold')
        
        plt.title('Transaction Time Prediction and Anomalies')
        plt.xlabel('Time Step')
        plt.ylabel('Transaction Time')
        plt.legend()
        plt.draw()
        plt.pause(0.01)
        
        # Check if any alert is generated
        if alert_generated:
            print("ALERT GENERATED!")
        else:
            print("No alert.")
        
        # Wait before processing the next chunk
        time.sleep(plot_interval)
    
    # Turn off interactive mode when done
    plt.ioff()
    plt.show()

# Main execution
if __name__ == "__main__":
    # Run the simulation with the CSV file path
    simulate_real_time_processing('synthetic_data_1_server.csv')
