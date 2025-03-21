import streamlit as st
import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model
import pickle
from sklearn.preprocessing import LabelEncoder, RobustScaler
import matplotlib.pyplot as plt
import time
import os
from collections import deque

# Initialize session state variables if they don't exist
if 'simulation_started' not in st.session_state:
    st.session_state.simulation_started = False

if 'simulation_paused' not in st.session_state:
    st.session_state.simulation_paused = False

if 'params_set' not in st.session_state:
    st.session_state.params_set = False
    st.session_state.window_size = 30
    st.session_state.future_window = 5
    st.session_state.chunk_size = 100
    st.session_state.update_interval = 0.5
    st.session_state.initial_threshold = 0.0
    st.session_state.alpha_raise = 0.5
    st.session_state.alpha_fall = 0.05
    st.session_state.anomaly_window = 5
    st.session_state.min_anomalies = 3

# Initialize simulation state storage
if 'sim_state' not in st.session_state:
    st.session_state.sim_state = {
        'chunk_idx': 0,
        'accumulated_data': None,
        'threshold': 0,
        'all_real_values': [],
        'all_predicted_values': [],
        'all_anomalies': [],
        'thresholds': [],
        'errors': [],
        'time_points': [],
        'current_time': 0,
        'alert_count': 0,
        'recent_anomalies': [],
        'df': None,
        'total_chunks': 0,
        'label_encoders': None,
        'model': None,
        'current_scaler': None
    }

# Set page config
st.set_page_config(
    page_title="Anomaly Detection Dashboard",
    page_icon="🔍",
    layout="wide"
)

# Title and description
st.title("Real-time Anomaly Detection Dashboard")
st.markdown("""
This dashboard simulates real-time anomaly detection in time series data using a TFT (Temporal Fusion Transformer) model.
Adjust the parameters using the sliders on the sidebar to fine-tune the anomaly detection sensitivity.
""")

# Function to set parameters
def set_params():
    st.session_state.window_size = window_size
    st.session_state.future_window = future_window
    st.session_state.chunk_size = chunk_size
    st.session_state.update_interval = update_interval
    st.session_state.initial_threshold = initial_threshold
    st.session_state.alpha_raise = alpha_raise
    st.session_state.alpha_fall = alpha_fall
    st.session_state.anomaly_window = anomaly_window
    st.session_state.min_anomalies = min_anomalies
    st.session_state.params_set = True

# Function to toggle pause state
def toggle_pause():
    st.session_state.simulation_paused = not st.session_state.simulation_paused

# Sidebar for parameters
st.sidebar.header("Parameters")

# File uploader for CSV
uploaded_file = st.sidebar.file_uploader("Upload CSV data file", type=["csv"])

# File uploader for model
uploaded_model = st.sidebar.file_uploader("Upload Keras model file", type=["h5", "keras"])

# File uploader for label encoders
uploaded_encoders = st.sidebar.file_uploader("Upload label encoders pickle file", type=["pkl"])

# Only show parameter setup if simulation hasn't started
if not st.session_state.simulation_started:
    # Simulation parameters
    window_size = st.sidebar.slider("Input Window Size", min_value=5, max_value=100, value=st.session_state.window_size)
    future_window = st.sidebar.slider("Prediction Window Size", min_value=1, max_value=20, value=st.session_state.future_window)
    chunk_size = st.sidebar.slider("Chunk Size", min_value=10, max_value=500, value=st.session_state.chunk_size)
    update_interval = st.sidebar.slider("Update Interval (seconds)", min_value=0.1, max_value=5.0, value=st.session_state.update_interval, step=0.1)

    # Anomaly detection parameters
    st.sidebar.header("Anomaly Detection Parameters")
    initial_threshold = st.sidebar.slider("Initial Threshold", min_value=0.0, max_value=1.0, value=st.session_state.initial_threshold, step=0.01)
    alpha_raise = st.sidebar.slider("Alpha Raise (↑ for more sensitivity)", min_value=0.0, max_value=1.0, value=st.session_state.alpha_raise, step=0.01)
    alpha_fall = st.sidebar.slider("Alpha Fall (↓ for more sensitivity)", min_value=0.0, max_value=0.5, value=st.session_state.alpha_fall, step=0.01)
    anomaly_window = st.sidebar.slider("Anomaly Window Size", min_value=3, max_value=10, value=st.session_state.anomaly_window)
    min_anomalies = st.sidebar.slider("Min Anomalies for Alert", min_value=1, max_value=5, value=st.session_state.min_anomalies)
    
    # Button to set parameters
    st.sidebar.button("Apply Parameters", on_click=set_params)
else:
    # Display the current parameters but don't allow changing
    st.sidebar.subheader("Current Parameters (Simulation Running)")
    st.sidebar.text(f"Input Window Size: {st.session_state.window_size}")
    st.sidebar.text(f"Prediction Window Size: {st.session_state.future_window}")
    st.sidebar.text(f"Chunk Size: {st.session_state.chunk_size}")
    st.sidebar.text(f"Update Interval: {st.session_state.update_interval} seconds")
    st.sidebar.text(f"Initial Threshold: {st.session_state.initial_threshold}")
    st.sidebar.text(f"Alpha Raise: {st.session_state.alpha_raise}")
    st.sidebar.text(f"Alpha Fall: {st.session_state.alpha_fall}")
    st.sidebar.text(f"Anomaly Window Size: {st.session_state.anomaly_window}")
    st.sidebar.text(f"Min Anomalies for Alert: {st.session_state.min_anomalies}")

# Info about alpha parameters
st.sidebar.markdown("""
### Sensitivity Guide
- **Less Sensitive**: Lower Alpha Raise (0.1-0.3), Higher Alpha Fall (0.1-0.2)
- **Moderate**: Medium Alpha Raise (0.4-0.6), Medium Alpha Fall (0.05-0.1)
- **More Sensitive**: Higher Alpha Raise (0.7-1.0), Lower Alpha Fall (0.01-0.04)
""")

# Function to reset simulation
def reset_simulation():
    st.session_state.simulation_started = False
    st.session_state.simulation_paused = False
    # Reset simulation state
    st.session_state.sim_state = {
        'chunk_idx': 0,
        'accumulated_data': None,
        'threshold': 0,
        'all_real_values': [],
        'all_predicted_values': [],
        'all_anomalies': [],
        'thresholds': [],
        'errors': [],
        'time_points': [],
        'current_time': 0,
        'alert_count': 0,
        'recent_anomalies': [],
        'df': None,
        'total_chunks': 0,
        'label_encoders': None,
        'model': None,
        'current_scaler': None
    }
    # Clean up temporary files
    for temp_file in ["temp_data.csv", "temp_model.keras", "temp_encoders.pkl"]:
        if os.path.exists(temp_file):
            os.remove(temp_file)

# Add reset button if simulation is running
if st.session_state.simulation_started:
    # Add pause/resume button
    pause_button_text = "Resume Simulation" if st.session_state.simulation_paused else "Pause Simulation"
    st.sidebar.button(pause_button_text, on_click=toggle_pause)
    
    # Add reset button
    st.sidebar.button("Reset Simulation", on_click=reset_simulation)

# Function to preprocess data
def preprocess_data(df, label_encoders):
    # Create a copy to avoid modifying the original
    df = df.copy()
    
    # Handle missing columns if needed
    required_cols = ['forest', 'adsite', 'target', 'datacenter', 'testsource', 
                   'domain', 'targetenvironment', 'transactiontime']
    
    for col in required_cols:
        if col not in df.columns:
            st.error(f"Required column '{col}' not found in the data!")
            return None, None
    
    # Merge 'forest' and 'adsite' into 'forest_adsite'
    df['forest_adsite'] = df['forest'] + '_' + df['adsite']
    
    # Initialize scaler
    scaler = RobustScaler()
    
    # Encode categorical features
    for col in ['target', 'datacenter', 'testsource', 'domain', 'forest', 'targetenvironment', 'forest_adsite']:
        if col not in label_encoders:
            label_encoders[col] = LabelEncoder()
            df[col] = label_encoders[col].fit_transform(df[col])
        else:
            try:
                df[col] = label_encoders[col].transform(df[col])
            except ValueError:
                # Handle unknown categories
                st.warning(f"Unknown categories in column '{col}', fitting new encoder")
                label_encoders[col] = LabelEncoder()
                df[col] = label_encoders[col].fit_transform(df[col])
    
    # Scale numerical features
    df['transactiontime'] = scaler.fit_transform(df[['transactiontime']])
    
    # Drop columns that are no longer needed
    drop_cols = ['adsite', 'result'] 
    if 'timestamp' in df.columns:
        drop_cols.append('timestamp')
    
    df.drop(columns=[col for col in drop_cols if col in df.columns], inplace=True)
    
    return df, scaler

# Function to update the threshold using EMA
def update_threshold(current_threshold, error, alpha_raise, alpha_fall):
    if error > current_threshold:
        # Use alpha_raise to increase the threshold quickly
        new_threshold = (1 - alpha_raise) * current_threshold + alpha_raise * error
    else:
        # Use alpha_fall to decrease the threshold slowly
        new_threshold = (1 - alpha_fall) * current_threshold + alpha_fall * error
    return new_threshold

# Function to create sequences for the model
def create_sequences(data, sequence_length=30, future_window=5):
    X = []
    for i in range(len(data) - sequence_length - future_window + 1):
        X.append(data.iloc[i:(i + sequence_length)].values)
    return np.array(X)

def get_default_files():
    # Define default file paths for when user doesn't upload files
    default_files = {
        'data_path': "default_data.csv",
        'model_path': "default_model.keras",
        'encoders_path': "default_encoders.pkl"
    }
    
    # Check if the default files exist
    missing_files = []
    for file_type, path in default_files.items():
        if not os.path.exists(path):
            missing_files.append(f"{file_type} ({path})")
    
    if missing_files:
        st.warning(f"Default files not found: {', '.join(missing_files)}. Please upload files manually.")
        return None, None, None
    
    return default_files['data_path'], default_files['model_path'], default_files['encoders_path']
    
# Function to initialize simulation
def initialize_simulation():
    if uploaded_file is None or uploaded_model is None or uploaded_encoders is None:
        # Try to use default files
        default_data_path, default_model_path, default_encoders_path = get_default_files()
        
        if default_data_path is None:
            st.warning("Please upload all required files (CSV data, model, and label encoders).")
            return False
        
        # Use default files
        st.info("Using default files since uploads are missing.")
        
        # Load the model if not already loaded
        if st.session_state.sim_state['model'] is None:
            try:
                st.session_state.sim_state['model'] = load_model(default_model_path)
                st.success("Default model loaded successfully!")
            except Exception as e:
                st.error(f"Error loading default model: {e}")
                reset_simulation()
                return False
        
        # Load the label encoders if not already loaded
        if st.session_state.sim_state['label_encoders'] is None:
            try:
                with open(default_encoders_path, "rb") as f:
                    st.session_state.sim_state['label_encoders'] = pickle.load(f)
                
                st.success("Default label encoders loaded successfully!")
            except Exception as e:
                st.error(f"Error loading default label encoders: {e}")
                reset_simulation()
                return False
        
        # Load the data if not already loaded
        if st.session_state.sim_state['df'] is None:
            try:
                st.session_state.sim_state['df'] = pd.read_csv(default_data_path)
                st.session_state.sim_state['total_chunks'] = (len(st.session_state.sim_state['df']) // st.session_state.chunk_size) + 1
            except Exception as e:
                st.error(f"Error reading default CSV file: {e}")
                reset_simulation()
                return False
    else:
        # Original code for when files are uploaded
        # ...
    
        # Load the model if not already loaded
        if st.session_state.sim_state['model'] is None:
            try:
                # Save the uploaded model to a temporary file
                with open("temp_model.keras", "wb") as f:
                    f.write(uploaded_model.getbuffer())
                
                st.session_state.sim_state['model'] = load_model("temp_model.keras")
                st.success("Model loaded successfully!")
            except Exception as e:
                st.error(f"Error loading model: {e}")
                reset_simulation()
                return False
        
        # Load the label encoders if not already loaded
        if st.session_state.sim_state['label_encoders'] is None:
            try:
                # Save the uploaded encoders to a temporary file
                with open("temp_encoders.pkl", "wb") as f:
                    f.write(uploaded_encoders.getbuffer())
                
                with open("temp_encoders.pkl", "rb") as f:
                    st.session_state.sim_state['label_encoders'] = pickle.load(f)
                
                st.success("Label encoders loaded successfully!")
            except Exception as e:
                st.error(f"Error loading label encoders: {e}")
                reset_simulation()
                return False
        
        # Load the data if not already loaded
        if st.session_state.sim_state['df'] is None:
            # Save the uploaded file to a temporary CSV
            with open("temp_data.csv", "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            try:
                st.session_state.sim_state['df'] = pd.read_csv("temp_data.csv")
                st.session_state.sim_state['total_chunks'] = (len(st.session_state.sim_state['df']) // st.session_state.chunk_size) + 1
            except Exception as e:
                st.error(f"Error reading CSV file: {e}")
                reset_simulation()
                return False
        
        # Initialize accumulated data if not already initialized
        if st.session_state.sim_state['accumulated_data'] is None:
            st.session_state.sim_state['accumulated_data'] = pd.DataFrame()
            
        # Initialize threshold
        if st.session_state.sim_state['threshold'] == 0:
            st.session_state.sim_state['threshold'] = st.session_state.initial_threshold
        
        # Initialize data structures if needed
        max_display_points = 250
        if not st.session_state.sim_state['all_real_values']:
            st.session_state.sim_state['all_real_values'] = deque(maxlen=max_display_points)
            st.session_state.sim_state['all_predicted_values'] = deque(maxlen=max_display_points)
            st.session_state.sim_state['all_anomalies'] = deque(maxlen=max_display_points)
            st.session_state.sim_state['thresholds'] = deque(maxlen=max_display_points)
            st.session_state.sim_state['errors'] = deque(maxlen=max_display_points)
            st.session_state.sim_state['time_points'] = deque(maxlen=max_display_points)
            st.session_state.sim_state['recent_anomalies'] = deque(maxlen=st.session_state.anomaly_window)
        
        return True

# Start the simulation
def start_simulation():
    st.session_state.simulation_started = True
    st.session_state.simulation_paused = False

# Main simulation function
def simulate_real_time_anomaly_detection():
    # Create placeholders for graphs
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Real-time Anomaly Detection")
        timeseries_chart = st.empty()
    
    with col2:
        st.subheader("Threshold Evolution")
        threshold_chart = st.empty()
        
    # Status indicators
    status_col1, status_col2, status_col3 = st.columns(3)
    
    with status_col1:
        data_status = st.empty()
    
    with status_col2:
        anomaly_status = st.empty()
    
    with status_col3:
        alert_status = st.empty()
    
    # Create progress bar
    progress_bar = st.progress(0)
    
    # Initialize simulation if needed
    if not initialize_simulation():
        return
    
    # Get simulation state from session state
    sim_state = st.session_state.sim_state
    
    # Display simulation status
    if st.session_state.simulation_paused:
        st.warning("Simulation is paused. Click 'Resume Simulation' to continue.")
        
        # Show current plots even when paused
        update_plots(sim_state, timeseries_chart, threshold_chart)
        
        # Update status displays
        if sim_state['accumulated_data'] is not None:
            data_status.metric("Data Points", len(sim_state['accumulated_data']), None)
        
        anomaly_count = sum(sim_state['all_anomalies'])
        anomaly_status.metric("Anomalies Detected", anomaly_count, None)
        
        alert_generated = sum(sim_state['recent_anomalies']) >= st.session_state.min_anomalies
        alert_text = f"ALERT ACTIVE! ({sim_state['alert_count']} total)" if alert_generated else "No Active Alerts"
        alert_color = "red" if alert_generated else "green"
        alert_status.markdown(f"<div style='background-color:{alert_color};padding:10px;border-radius:5px;color:white;text-align:center;'><strong>{alert_text}</strong></div>", unsafe_allow_html=True)
        
        return
    
    # Simulation loop
    try:
        # Get current chunk index and continue from there
        chunk_idx = sim_state['chunk_idx']
        df = sim_state['df']
        total_chunks = sim_state['total_chunks']
        
        # Process chunks until paused or finished
        while chunk_idx < total_chunks and not st.session_state.simulation_paused:
            # Update progress
            progress = min(float(chunk_idx) / total_chunks, 1.0)
            progress_bar.progress(progress)
            
            # Get the current chunk
            chunk_start = chunk_idx * st.session_state.chunk_size
            chunk_end = min(chunk_start + st.session_state.chunk_size, len(df))
            chunk = df.iloc[chunk_start:chunk_end].copy()
            
            # Add timestamp if not present
            if 'timestamp' not in chunk.columns:
                chunk['timestamp'] = pd.date_range(start='2024-01-01', periods=len(chunk), freq='T')
            
            # Preprocess the new data
            new_data, current_scaler = preprocess_data(chunk, sim_state['label_encoders'])
            sim_state['current_scaler'] = current_scaler
            
            if new_data is None:
                st.error("Error preprocessing data. Check if your CSV has the required columns.")
                reset_simulation()
                break
            
            # Accumulate data
            sim_state['accumulated_data'] = pd.concat([sim_state['accumulated_data'], new_data], ignore_index=True)
            
            # Update data status
            data_status.metric("Data Points", len(sim_state['accumulated_data']), f"+{len(new_data)}")
            
            # Check if accumulated data has enough rows for a sequence
            if len(sim_state['accumulated_data']) < st.session_state.window_size + st.session_state.future_window:
                st.info(f"Not enough data to form a sequence. Have {len(sim_state['accumulated_data'])} rows, need {st.session_state.window_size + st.session_state.future_window}.")
                time.sleep(st.session_state.update_interval)
                chunk_idx += 1
                sim_state['chunk_idx'] = chunk_idx
                continue
            
            # Create sequences for prediction
            sequences = create_sequences(sim_state['accumulated_data'], st.session_state.window_size, st.session_state.future_window)
            
            # Make predictions
            predictions = sim_state['model'].predict(sequences, verbose=0)
            
            # Process each prediction
            for i in range(len(sequences)):
                # Get the input sequence end index
                seq_end_idx = i + st.session_state.window_size
                
                # Get the actual value (first point of the prediction window)
                if seq_end_idx < len(sim_state['accumulated_data']):
                    actual = sim_state['accumulated_data'].iloc[seq_end_idx]['transactiontime']
                    
                    # Get the predicted value (first point of the prediction)
                    predicted = predictions[i][0]
                    
                    # Inverse transform for display
                    actual_original = current_scaler.inverse_transform([[actual]])[0][0]
                    predicted_original = current_scaler.inverse_transform([[predicted]])[0][0]
                    
                    # Calculate error
                    error = abs(actual_original - predicted_original)
                    
                    # Update threshold
                    sim_state['threshold'] = update_threshold(sim_state['threshold'], error, 
                                                             st.session_state.alpha_raise, 
                                                             st.session_state.alpha_fall)
                    
                    # Detect anomaly
                    is_anomaly = (error > sim_state['threshold']) and (predicted_original < actual_original)
                    
                    # Update tracking collections
                    sim_state['current_time'] += 1
                    sim_state['all_real_values'].append(actual_original)
                    sim_state['all_predicted_values'].append(predicted_original)
                    sim_state['all_anomalies'].append(is_anomaly)
                    sim_state['thresholds'].append(sim_state['threshold'])
                    sim_state['errors'].append(error)
                    sim_state['time_points'].append(sim_state['current_time'])
                    
                    # Track recent anomalies for alert detection
                    sim_state['recent_anomalies'].append(is_anomaly)
            
            # Check for alert condition
            alert_generated = sum(sim_state['recent_anomalies']) >= st.session_state.min_anomalies
            if alert_generated:
                sim_state['alert_count'] += 1
            
            # Update anomaly status
            anomaly_count = sum(sim_state['all_anomalies'])
            anomaly_status.metric("Anomalies Detected", anomaly_count, 
                               f"+{sum(list(sim_state['all_anomalies'])[-len(new_data):])}" if len(new_data) < len(sim_state['all_anomalies']) else None)
            
            # Update alert status with appropriate color
            alert_text = f"ALERT ACTIVE! ({sim_state['alert_count']} total)" if alert_generated else "No Active Alerts"
            alert_color = "red" if alert_generated else "green"
            alert_status.markdown(f"<div style='background-color:{alert_color};padding:10px;border-radius:5px;color:white;text-align:center;'><strong>{alert_text}</strong></div>", unsafe_allow_html=True)
            
            # Update plots
            update_plots(sim_state, timeseries_chart, threshold_chart)
            
            # Update chunk index
            chunk_idx += 1
            sim_state['chunk_idx'] = chunk_idx
            
            # Pause to simulate real-time processing
            time.sleep(st.session_state.update_interval)
        
        # Show completion if we've processed all chunks
        if chunk_idx >= total_chunks:
            progress_bar.progress(1.0)
            st.success("Simulation completed!")
            reset_simulation()
        
    except Exception as e:
        st.error(f"Error during simulation: {e}")
        import traceback
        st.code(traceback.format_exc())
        reset_simulation()

# Function to update plots
def update_plots(sim_state, timeseries_chart, threshold_chart):
    # Convert deques to lists for plotting
    time_points_list = list(sim_state['time_points'])
    real_values_list = list(sim_state['all_real_values'])
    predicted_values_list = list(sim_state['all_predicted_values'])
    all_anomalies_list = list(sim_state['all_anomalies'])
    thresholds_list = list(sim_state['thresholds'])
    errors_list = list(sim_state['errors'])
    
    # Plot the time series
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    
    # Ensure we have data to plot
    if time_points_list and real_values_list and predicted_values_list:
        ax1.plot(time_points_list, real_values_list, label='Real Value', color='blue')
        ax1.plot(time_points_list, predicted_values_list, label='Predicted', color='green')
        
        # Plot anomalies
        anomaly_indices = [i for i, anomaly in enumerate(all_anomalies_list) if anomaly]
        if anomaly_indices:
            anomaly_times = [time_points_list[i] for i in anomaly_indices]
            anomaly_values = [real_values_list[i] for i in anomaly_indices]
            ax1.scatter(anomaly_times, anomaly_values, color='red', label='Anomaly', zorder=5)
        
        ax1.set_title('Transaction Time: Real vs Predicted')
        ax1.set_xlabel('Time Step')
        ax1.set_ylabel('Transaction Time')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Display the time series plot
        timeseries_chart.pyplot(fig1)
        plt.close(fig1)
        
        # Plot the threshold evolution
        fig2, ax2 = plt.subplots(figsize=(10, 5))
        ax2.plot(time_points_list, thresholds_list, label='Threshold', color='purple')
        ax2.plot(time_points_list, errors_list, label='Error', color='orange', alpha=0.5)
        
        # Highlight where errors exceed threshold
        for i, (err, thresh) in enumerate(zip(errors_list, thresholds_list)):
            if err > thresh:
                ax2.axvspan(time_points_list[i]-0.5, time_points_list[i]+0.5, color='red', alpha=0.2)
        
        ax2.set_title('Threshold Evolution and Errors')
        ax2.set_xlabel('Time Step')
        ax2.set_ylabel('Value')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Display the threshold plot
        threshold_chart.pyplot(fig2)
        plt.close(fig2)

# Main function
def main():
    # Only show the start button if simulation hasn't started yet
    if not st.session_state.simulation_started:
        start_button = st.button("Start Simulation", on_click=start_simulation)
        
        # Only allow starting if parameters are set
        if not st.session_state.params_set:
            st.info("Please set your parameters using the 'Apply Parameters' button in the sidebar before starting the simulation.")
    
    # Run the simulation if it's already started
    if st.session_state.simulation_started:
        simulate_real_time_anomaly_detection()

if __name__ == "__main__":
    main()
