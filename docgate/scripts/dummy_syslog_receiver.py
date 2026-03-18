#!/usr/bin/env python3
"""For quickly test syslog receiver"""

import socket
import sys

UDP_IP = "127.0.0.1"
UDP_PORT = 11514

try:
  # Create a UDP socket
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock.bind((UDP_IP, UDP_PORT))

  # Print startup message
  print(f"📡 Listening on UDP {UDP_IP}:{UDP_PORT} ...")
  print("Press Ctrl+C to stop")
  print("-" * 60)

  while True:
    # Receive data from the socket
    data, addr = sock.recvfrom(4096)

    try:
      # Try to decode the bytes into a string
      message = data.decode("utf-8")

      # Split the message into lines (in case one UDP packet contains multiple logs)
      lines = message.split("\n")
      for line in lines:
        if line.strip():  # Ignore empty lines
          # Print the source IP and the log content
          print(f"[{addr[0]}]: {line.strip()}")

    except UnicodeDecodeError:
      # Handle cases where the data is not valid text
      print(f"[{addr[0]}] [Undecodable binary data, length: {len(data)}]")
    print()

except KeyboardInterrupt:
  # Handle user interruption
  print("\n👋 Listener stopped.")
  sys.exit(0)
except Exception as e:
  # Handle other errors
  print(f"An error occurred: {e}")
