import sys
import time
import numpy as np
from matrix_lite import sensors
from datetime import datetime

MAX_RETRIES = 3  # Maximum number of retries before exiting
RETRY_DELAY = 0.25  # Delay between retries in seconds
HEADING_THRESHOLD = 283  # Threshold for door open/close

def read_magnetometer():
    """Read the magnetometer data from the IMU."""
    data = sensors.imu.read()
    return data.mag_x, data.mag_y

def calculate_heading(mag_x, mag_y):
    """Calculate the heading from the magnetometer data."""
    heading = np.arctan2(mag_y, mag_x)  # Heading in radians
    heading = np.degrees(heading)       # Convert to degrees
    heading = (heading + 360) % 360     # Ensure the heading is between 0-360 degrees
    return heading

def log_door_state(state):
    """Log the current date and time with door state to Door.log."""
    with open("/home/pi/GPT/Door.log", "a") as log_file:  # Open the log file in append mode
        current_time = datetime.now()                      # Get the current date and time
        log_file.write(f"{current_time} Door {state}\n")   # Write to the log file

def log_system_failure():
    """Log the sensor failure before exiting."""
    with open("/home/pi/GPT/Door.log", "a") as log_file:  # Open the log file in append mode
        current_time = datetime.now()                      # Get the current date and time
        log_file.write(f"{current_time} System failure\n") # Log the failure

def save_epoch_timestamp():
    """Save the current Unix epoch timestamp to epoch.txt."""
    with open("/home/pi/GPT/epoch.txt", "w") as epoch_file:
        epoch_time = int(time.time())  # Get current Unix epoch timestamp
        epoch_file.write(f"{epoch_time}\n")  # Write to the file

previous_heading = None  # Initialize previous heading

def main():
    sleep_time = 2
    global previous_heading
    while True:
        save_epoch_timestamp()  # Save the epoch timestamp at the start of each loop iteration

        retry_count = 0
        while retry_count < MAX_RETRIES:
            mx, my = read_magnetometer()
            if mx == 0.0 or my == 0.0:
                retry_count += 1
                if retry_count >= MAX_RETRIES:
                    log_system_failure()
                    sys.exit("Exiting due to sensor failure.")
                time.sleep(RETRY_DELAY)
            else:
                break  # Break out of the retry loop if successful reading

        current_heading = calculate_heading(mx, my)

        # Implement the logic to log "open" and "closed" based on the heading change
        if previous_heading is not None:
            diff=(current_heading-previous_heading)**2
            if (diff >= 1):
                with open("/home/pi/GPT/Motion.log", "a") as door_file:
                    door_file.write(f"Door moved\n")
                sleep_time = 2
            else:
               sleep_time = 3
            if previous_heading >= HEADING_THRESHOLD and current_heading < HEADING_THRESHOLD:
                log_door_state("open")
                sleep_time *= 2
            elif previous_heading < HEADING_THRESHOLD and current_heading >= HEADING_THRESHOLD:
                log_door_state("closed")

        previous_heading = current_heading  # Update the previous heading for the next iteration
        time.sleep(sleep_time)

if __name__ == "__main__":
    main()
