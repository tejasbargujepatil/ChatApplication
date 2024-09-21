import socket
import threading
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Generate RSA key pair for the server
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)
public_key = private_key.public_key()
public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

def handle_client(client_socket):
    try:
        # Send the public key to the client
        client_socket.send(public_pem)

        # Receive the encrypted AES key from the client
        encrypted_aes_key = client_socket.recv(256)

        # Decrypt the AES key using the server's private RSA key
        aes_key = private_key.decrypt(
            encrypted_aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        # Receive the IV from the client
        iv = client_socket.recv(16)

        # Initialize the AES cipher
        cipher = Cipher(algorithms.AES(aes_key), modes.CFB(iv), backend=default_backend())
        decryptor = cipher.decryptor()

        while True:
            encrypted_message = client_socket.recv(1024)
            if not encrypted_message:
                break
            try:
                decrypted_message = decryptor.update(encrypted_message)
                print(f"Received: {decrypted_message.decode('utf-8', errors='ignore')}")
            except Exception as e:
                print(f"Decryption failed: {e}")
                break

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        client_socket.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 9999))
    server.listen(5)
    print("Server listening on port 9999")

    while True:
        client_socket, addr = server.accept()
        print(f"Accepted connection from {addr}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

start_server()
