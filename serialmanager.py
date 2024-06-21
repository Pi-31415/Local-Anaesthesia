"""
The Local Anesthesia Simulation Device Manager manages syringe and cheek retractor devices. This application detects devices automatically, processes and filters data to ensure it starts with specific keywords ("Quat" for syringes and "Cheek" for cheek retractors), and monitors data continuously. It uses UDP to transmit filtered data directly to Unity or other platforms for simulation.

Author: Pi Ko (pi.ko@nyu.edu)

Requirements: Install the pyserial library with

pip install pyserial


Attributes:
    udp_ip (str): The IP address for UDP communication. Default is '127.0.0.1'.
    udp_port (int): The port number for UDP communication. Default is 5005.
    udp_socket: A socket object for UDP communication.
    device_status (dict): A dictionary to track the status of connected devices.
    continuous_read_threads (list): A list to store threads for continuous reading.
    active_threads (list): A list to store active threads for device scanning.

Methods:
    __init__: Initializes the SerialApp with the specified UDP IP and port, sets up the GUI, and initializes necessary attributes.
    init_ui: Initializes the user interface components of the application.
    log: Logs a message to the data_text widget.
    scan_devices: Scans for connected devices and starts threads for initial connection and reading.
    check_threads: Checks the status of active threads and displays results when all threads are completed.
    initial_connect_and_read: Establishes an initial connection with a device and reads data from it.
    process_data: Processes the data received from a device and updates the device status.
    start_continuous_read: Starts a thread for continuous reading from a device.
    continuous_read: Continuously reads data from a device and sends it over UDP to a specified IP and port.
    display_results: Displays the detection results of connected devices in the GUI.
"""

import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports
from threading import Thread
import socket
import time

class SerialApp(tk.Tk):
    def __init__(self, udp_ip='127.0.0.1', udp_port=5005):
        super().__init__()
        self.title("Local Anesthesia Simulation Device Manager")
        self.geometry("600x400")
        self.udp_ip = udp_ip
        self.udp_port = udp_port
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.device_status = {"Syringe": None, "Cheek Retractor": None}  # Track device status
        self.init_ui()
        self.log("App started...")
        self.continuous_read_threads = []
        self.active_threads = []

    def init_ui(self):
        self.info_label = tk.Label(self, text="Local Anastetia Simulation Device Manager\nby AIMLAB, NYU Abu Dhabi.\nProgrammer: Pi Ko (pi.ko@nyu.edu).\n\nConnect both devices then click scan. It will send data to Unity automatically.", font=("Helvetica", 10), wraplength=400)
        self.info_label.pack(pady=(10, 0))
        
        self.scan_button = ttk.Button(self, text="Scan", command=self.scan_devices)
        self.scan_button.pack(pady=20)
        
        self.result_label = tk.Label(self, text="", font=("Helvetica", 16))
        self.result_label.pack(pady=10)
        
        self.data_text = tk.Text(self, height=10, width=70)
        self.data_text.pack(pady=10)

    def log(self, message):
        self.data_text.insert(tk.END, message + "\n")
        self.data_text.see(tk.END)

    def scan_devices(self):
        self.log("Scanning devices...")
        ports = serial.tools.list_ports.comports()
        if not ports:
            self.log("No devices found.")
        else:
            self.active_threads = []
            for port in ports:
                self.log(f"Attempting to connect to {port.device}...")
                thread = Thread(target=self.initial_connect_and_read, args=(port.device,))
                thread.start()
                self.active_threads.append(thread)
            self.after(100, self.check_threads)

    def check_threads(self):
        if all(not thread.is_alive() for thread in self.active_threads):
            self.display_results()
        else:
            self.after(100, self.check_threads)

    def initial_connect_and_read(self, port):
        try:
            with serial.Serial(port, 115200, timeout=1) as ser:
                start_time = time.time()
                while time.time() - start_time < 4:
                    if ser.in_waiting > 0:
                        data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                        self.process_data(data, port)
        except Exception as e:
            self.log(f"Error with {port}: {str(e)}")
        finally:
            if port in [self.device_status["Syringe"], self.device_status["Cheek Retractor"]]:
                self.start_continuous_read(port)

    def process_data(self, data, port):
        if "Quat" in data and not self.device_status["Syringe"]:
            self.device_status["Syringe"] = port
        if "Cheek" in data and not self.device_status["Cheek Retractor"]:
            self.device_status["Cheek Retractor"] = port

    def start_continuous_read(self, port):
        thread = Thread(target=self.continuous_read, args=(port,))
        thread.start()
        self.continuous_read_threads.append(thread)

  
    def continuous_read(self, port):
        buffer = ""  # Initialize an empty buffer
        try:
            with serial.Serial(port, 115200, timeout=1) as ser:
                first_message = True
                while True:
                    if ser.in_waiting > 0:
                        data = ser.read(ser.in_waiting).decode('utf-8', errors='replace')
                        buffer += data  # Append new data to the buffer
                        lines = buffer.split('\n')  # Split buffer into lines
                        buffer = lines.pop()  # Keep the last partial line in the buffer

                        for line in lines:  # Process complete lines
                            if line.startswith("Quat") or line.startswith("Cheek"):
                                self.udp_socket.sendto(line.encode(), (self.udp_ip, self.udp_port))
                                if first_message:
                                    self.log(f"Sending data to Unity from {port}...")
                                    first_message = False
        except Exception as e:
            self.log(f"Error with continuous read {port}: {str(e)}")
    def display_results(self):
        result_text = ""
        if self.device_status["Syringe"]:
            result_text += f"Syringe Detected at {self.device_status['Syringe']}\n"
        else:
            result_text += "Syringe not detected.\n"
            
        if self.device_status["Cheek Retractor"]:
            result_text += f"Cheek Retractor Module Detected at {self.device_status['Cheek Retractor']}\n"
        else:
            result_text += "Cheek Retractor Module not detected.\n"
            
        self.result_label.config(text=result_text)
        self.log("Device detection and status update complete.")

if __name__ == "__main__":
    app = SerialApp()
    app.mainloop()
