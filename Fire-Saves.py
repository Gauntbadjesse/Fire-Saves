import cv2
import numpy as np
import sounddevice as sd
import queue
import threading
import time
from pathlib import Path
from datetime import datetime
import mss
import tkinter as tk
from tkinter import messagebox
from pynput import keyboard
import os
import requests
from PIL import Image, ImageTk  # To use images as background
import logging




import requests
import os
import subprocess
import sys

CURRENT_VERSION = '1.0.0'  # Replace with your current version
UPDATE_CHECK_URL = 'https://example.com/latest-version'  # URL to check the latest version
UPDATE_DOWNLOAD_URL = 'https://example.com/downloads/my_app_v2.0.zip'  # URL to the update package
INSTALL_DIR = '/path/to/your/app'  # Directory where your app is located
TEMP_UPDATE_FILE = 'my_app_update.zip'

def check_for_updates():
    try:
        response = requests.get(UPDATE_CHECK_URL)
        response.raise_for_status()
        latest_version = response.text.strip()  # Assuming the response is the latest version
        
        if latest_version != CURRENT_VERSION:
            print(f"New version available: {latest_version}")
            return latest_version
        else:
            print("App is up to date.")
            return None
    except requests.RequestException as e:
        print(f"Error checking for updates: {e}")
        return None

def download_update(update_url, output_file):
    try:
        response = requests.get(update_url, stream=True)
        response.raise_for_status()
        
        with open(output_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Update downloaded successfully.")
        return True
    except requests.RequestException as e:
        print(f"Failed to download update: {e}")
        return False

def install_update(zip_file, install_dir):
    try:
        # Extract the update package
        subprocess.run(['unzip', zip_file, '-d', install_dir], check=True)
        
        # Optionally, you may want to run the app after update
        subprocess.run(['python', os.path.join(install_dir, 'app.py')], check=True)
        print("Update installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install update: {e}")
        return False

def main():
    new_version = check_for_updates()
    if new_version:
        print(f"Updating to version {new_version}...")
        if download_update(UPDATE_DOWNLOAD_URL, TEMP_UPDATE_FILE):
            if install_update(TEMP_UPDATE_FILE, INSTALL_DIR):
                print("Update complete.")
                sys.exit(0)  # Exit the app gracefully
            else:
                print("Failed to apply the update.")
        else:
            print("Update download failed.")
    else:
        print("No updates available.")

    # Your existing code here...


# Constants
CLIP_LENGTH = 5 * 60  # 5 minutes
FRAME_RATE = 30

# Buffers
video_buffer = queue.Queue(maxsize=FRAME_RATE * CLIP_LENGTH)
audio_buffer = queue.Queue(maxsize=CLIP_LENGTH * 441000)

# Screen Size
with mss.mss() as sct:
    SCREEN_WIDTH = sct.monitors[1]["width"]
    SCREEN_HEIGHT = sct.monitors[1]["height"]

# Dynamically get the Desktop path for the current user
user_desktop = Path(os.path.join(os.path.expanduser("~"), "Desktop"))
SAVE_PATH = user_desktop / "clips"
SAVE_PATH.mkdir(parents=True, exist_ok=True)

# Global variables for recording state
is_recording = False
start_time = time.time()

# Check if the app is being opened for the first time
FIRST_RUN_FLAG_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), ".first_run")
first_run = not os.path.exists(FIRST_RUN_FLAG_PATH)

if first_run:
    # Create a file to mark that the app has been opened before
    with open(FIRST_RUN_FLAG_PATH, "w") as f:
        f.write("First run")

# Screen Recording Function
def record_screen():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        while True:
            if is_recording:
                frame = np.array(sct.grab(monitor))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                video_buffer.put(frame)
                if video_buffer.qsize() > FRAME_RATE * CLIP_LENGTH:
                    video_buffer.get()
            time.sleep(1 / FRAME_RATE)

# Audio Recording Callback
def audio_callback(indata, frames, time, status):
    if status:
        logging.warning(f"Audio status: {status}")
    audio_buffer.put(indata.copy())

# Start audio recording
audio_stream = sd.InputStream(callback=audio_callback, channels=2, samplerate=44100)
audio_stream.start()

# Save Clip Function
def save_clip():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    video_file = SAVE_PATH / f"clip_{timestamp}.avi"
    audio_file = SAVE_PATH / f"clip_{timestamp}.wav"

    # Save video
    logging.debug("Saving video...")
    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    out = cv2.VideoWriter(str(video_file), fourcc, FRAME_RATE, (SCREEN_WIDTH, SCREEN_HEIGHT))
    while not video_buffer.empty():
        out.write(video_buffer.get())
    out.release()

    # Save audio
    logging.debug("Saving audio...")
    audio_data = []
    while not audio_buffer.empty():
        audio_data.append(audio_buffer.get())
    audio_data = np.concatenate(audio_data, axis=0)
    sd.write(audio_file, audio_data, 44100)

    logging.info(f"Clip saved to {video_file} and {audio_file}")
    messagebox.showinfo("Clip Saved", f"Clip saved successfully!\n{video_file}\n{audio_file}")

# GUI Class for Recording
class ClipApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MAGMA CLIPPING")
        
        # Set the app icon
        self.root.iconbitmap(r"C:\Users\jesse\Downloads\Logo.ico")  # Update the path to your .ico file

        # Set background image
        self.bg_image = Image.open(r"C:\Users\jesse\Downloads\Bg.ico")  # Update with your image path
        self.bg_image = self.bg_image.resize((SCREEN_WIDTH, SCREEN_HEIGHT), Image.Resampling.LANCZOS)
        self.bg_image_tk = ImageTk.PhotoImage(self.bg_image)

        self.bg_label = tk.Label(self.root, image=self.bg_image_tk)
        self.bg_label.place(relwidth=1, relheight=1)

        # Window size and config
        self.root.geometry("400x250")
        self.root.config(bg="#2C2F38")  # Dark background color
        self.root.resizable(False, False)

        # Status variable
        self.is_recording = False

        # Status label with no background color, fully integrated into the background image
        self.status_label = tk.Label(self.root, text="Status: Stopped", font=("Arial", 16, "bold"), fg="black", bg="#8B0000", relief="flat")
        self.status_label.pack(pady=20)

        # Start/Stop Button with fiery look
        self.start_stop_button = tk.Button(self.root, text="Start", font=("Arial", 14), command=self.toggle_recording, 
                                           width=12, height=2, bg="#FF6347", fg="#FFFFFF", relief="flat", borderwidth=0)
        self.start_stop_button.pack(pady=10)

        # Clip Button with magma color gradient
        self.clip_button = tk.Button(self.root, text="Clip", font=("Arial", 14), command=self.save_clip, 
                                      width=12, height=2, bg="#FF4500", fg="#FFFFFF", relief="flat", borderwidth=0)
        self.clip_button.pack(pady=10)

        # Customize buttons appearance on hover
        self.customize_button_hover_effect(self.start_stop_button, "#FF6347", "#FF7F50")
        self.customize_button_hover_effect(self.clip_button, "#FF4500", "#FF6347")

        # Show first run dialog if it's the first time opening the app
        if first_run:
            self.show_first_run_dialog()

        # Start global key listener in a separate thread
        threading.Thread(target=self.start_key_listener, daemon=True).start()

        # Automatically start recording when app is launched
        self.toggle_recording()

    def show_first_run_dialog(self):
        """Display a dialog on first run with 'Made by Jesse' message"""
        messagebox.showinfo("Welcome!", "Made by Jesse")

    def toggle_recording(self):
        """Start/Stop recording"""
        global is_recording
        if self.is_recording:
            self.status_label.config(text="Status: Stopped", fg="#FF5733")  # Red for stopped
            self.start_stop_button.config(text="Start", bg="#FF6347")
            self.is_recording = False
            is_recording = False  # Stop recording logic
        else:
            self.status_label.config(text="Status: Rolling...", fg="#FFD700")  # Golden for rolling
            self.start_stop_button.config(text="Stop", bg="#FF6347")
            self.is_recording = True
            is_recording = True  # Start recording logic

    def save_clip(self):
        """Save the current clip"""
        save_clip()
        self.status_label.config(text="Clip Saved", fg="#2196F3")  # Blue for saved clip

    def customize_button_hover_effect(self, button, normal_color, hover_color):
        """Add hover effect for buttons"""
        button.bind("<Enter>", lambda e: button.config(bg=hover_color))
        button.bind("<Leave>", lambda e: button.config(bg=normal_color))

    def on_press(self, key):
        """Global key listener callback"""
        try:
            if key.char == '*':
                logging.info("Global key '*' pressed: Saving clip...")
                save_clip()
        except AttributeError:
            pass

    def start_key_listener(self):
        """Start the global key listener"""
        with keyboard.Listener(on_press=self.on_press) as listener:
            listener.join()

# Initialize the main window
root = tk.Tk()

# Initialize the ClipApp instance
app = ClipApp(root)

# Start screen recording in a separate thread
screen_thread = threading.Thread(target=record_screen, daemon=True)
screen_thread.start()

# Start the Tkinter event loop
root.mainloop()

if __name__ == "__main__":
    main()




