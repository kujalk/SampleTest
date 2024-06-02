import threading
import queue
import csv
import time
import random

# Placeholder for the my_custom function
def my_custom():
    # Generate a random sleep time between 1 and 15 seconds
    sleep_time = random.randint(1, 15)
    random_num = random.randint(1, 3000)
    print(f"Hello, I am a thread with value {random_num}, and I am going to sleep for {sleep_time}")
    time.sleep(sleep_time)  # Simulate delay
    return {"random_num": random_num, "sleep_time": sleep_time}

# Worker thread function to call my_custom() and put the result in the queue
def worker_thread(q):
    result = my_custom()
    q.put(result)

# Function to read from the queue and write to a CSV file
def process_queue(q, csv_filename):
    with open(csv_filename, mode='a', newline='') as csvfile:
        fieldnames = ['random_num', 'sleep_time']  # Adjust this based on your actual dictionary keys
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        while True:
            try:
                entry = q.get_nowait()
                writer.writerow(entry)
            except queue.Empty:
                break

def main():
    num_threads = 10  # Number of threads to create
    csv_filename = 'output.csv'  # CSV file to write to
    q = queue.Queue()

    # Create and start worker threads
    threads = []
    for i in range(8):
        for _ in range(num_threads):
            thread = threading.Thread(target=worker_thread, args=(q,))
            thread.start()
            threads.append(thread)

        # Join all threads to ensure they complete before proceeding
        for thread in threads:
            thread.join()

    # Process the queue and write to CSV in a linear manner
    process_queue(q, csv_filename)

    print("Completed")

if __name__ == '__main__':
    main()
