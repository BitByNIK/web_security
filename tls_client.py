#!/usr/bin/python3
import socket
import ssl
import sys
import pprint

import re

hostname = sys.argv[1]
image_path = sys.argv[2] if len(sys.argv) > 2 else None
port = 443
cadir = './certs'

# Set up the TLS context
context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.load_verify_locations(capath=cadir)
context.verify_mode = ssl.CERT_REQUIRED
context.check_hostname = True

# Create TCP connection
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((hostname, port))
input("After making TCP connection. Press any key to continue ...")

# Add the TLS
ssock = context.wrap_socket(sock, server_hostname=hostname,
                            do_handshake_on_connect=False)
ssock.do_handshake()  # Start the handshake

# Print the Certificate in DER format
pprint.pprint(ssock.getpeercert())

# Print the Certificate in PEM format
print("PEM Certificate:")
pprint.pprint(ssl.DER_cert_to_PEM_cert(ssock.getpeercert(True)))

# Print the Cipher used
print("Cipher used:")
pprint.pprint(ssock.cipher())

input("After handshake. Press any key to continue ...")

if not image_path:
    # Send HTTP Request to Server
    print("\nSending empty HTTP request to server:")
    request = b"GET / HTTP/1.0\r\nHost: " + \
        hostname.encode('utf-8') + b"\r\n\r\n"
    print(request)
    ssock.sendall(request)

    # Read HTTP Response from Server
    print("\nResponse from server:")
    response = ssock.recv(2048)
    while response:
        pprint.pprint(response.split(b"\r\n"))
        response = ssock.recv(2048)

if image_path:
    print("\nSending HTTP request for image:")
    image_request = b"GET " + image_path.encode('utf-8') + b" HTTP/1.1\r\nHost: " + \
        hostname.encode('utf-8') + \
        b"\r\nUser-Agent: CustomClient/1.0\r\nAccept: */*\r\nConnection: close\r\n\r\n"
    print(image_request)
    ssock.sendall(image_request)

    print("\nSaving image to file:")
    response = b""
    while True:
        data = ssock.recv(4096)
        if not data:
            break
        response += data
    header_end = response.find(b"\r\n\r\n")
    image_data = response[header_end + 4:]

    core_name = re.sub(r"^www\.|\..*$", "", hostname)
    filename = f"image_{core_name}.png"

    with open(filename, "wb") as f:
        f.write(image_data)

    print(f"Image saved as {filename}")

# Close the TLS Connection
ssock.shutdown(socket.SHUT_RDWR)
ssock.close()
