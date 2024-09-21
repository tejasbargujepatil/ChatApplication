import socket
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

# Generate AES key for the client
aes_key = os.urandom(32)

def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('server_public_ip_or_domain', 9999))  # Replace with actual server IP

    # Receive the server's public key
    server_public_key_pem = client.recv(1024)
    server_public_key = serialization.load_pem_public_key(
        server_public_key_pem,
        backend=default_backend()
    )

    # Encrypt the AES key with the server's public RSA key
    encrypted_aes_key = server_public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    client.send(encrypted_aes_key)

    # Generate and send IV
    iv = os.urandom(16)
    client.send(iv)

    # Initialize AES cipher for encryption
    cipher = Cipher(algorithms.AES(aes_key), modes.CFB(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    while True:
        message = input("Enter message: ")
        encrypted_message = encryptor.update(message.encode('utf-8'))
        client.send(encrypted_message)

start_client()
