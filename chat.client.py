import socket
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import tkinter as tk
import threading

# Generate AES key for the client
aes_key = os.urandom(32)

def receive_messages():
    while True:
        try:
            encrypted_reply = client.recv(1024)
            decrypted_reply = decryptor.update(encrypted_reply)
            chat_box.configure(state=tk.NORMAL)
            chat_box.insert(tk.END, "Server: " + decrypted_reply.decode('utf-8', errors='ignore') + "\n")
            chat_box.configure(state=tk.DISABLED)
            chat_box.yview(tk.END)  # Scroll to the bottom
        except Exception as e:
            print(f"Error receiving message: {e}")
            break

def send_message():
    message = input_box.get()
    if not message:
        return
    encrypted_message = encryptor.update(message.encode('utf-8'))
    client.send(encrypted_message)
    chat_box.configure(state=tk.NORMAL)
    chat_box.insert(tk.END, "You: " + message + "\n")
    chat_box.configure(state=tk.DISABLED)
    input_box.delete(0, tk.END)

def start_client():
    global client, encryptor, decryptor, input_box, chat_box
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('172.17.108.180', 9999))  # Replace with actual server IP

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

    # Initialize AES cipher for encryption and decryption
    cipher = Cipher(algorithms.AES(aes_key), modes.CFB(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    decryptor = cipher.decryptor()

    # Setup UI
    window = tk.Tk()
    window.title("Secure Client - Chat")
    window.configure(bg="black")

    tk.Label(window, text="Secure Client - Encrypted Chat", font=("Arial", 14), fg="cyan", bg="black").pack(pady=10)

    # Chat display
    chat_box = tk.Text(window, height=20, width=50, bg="black", fg="white", state=tk.DISABLED)
    chat_box.pack(pady=10)

    # Message entry
    input_frame = tk.Frame(window, bg="black")
    input_frame.pack()

    input_box = tk.Entry(input_frame, width=40, bg="grey")
    input_box.pack(side=tk.LEFT, padx=5)
    send_button = tk.Button(input_frame, text="Send", command=send_message, bg="grey", fg="black", width=10)
    send_button.pack(side=tk.LEFT)

    # Start a thread to receive messages from the server
    threading.Thread(target=receive_messages, daemon=True).start()

    window.mainloop()

# Run the client
start_client()
