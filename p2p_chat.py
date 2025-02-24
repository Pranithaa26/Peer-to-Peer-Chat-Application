import socket
import threading
import select

class Peer:
    def __init__(self, name, port):
        self.name = name
        self.port = port
        self.peers = set()
        self.server_socket = None
        self.running = True

    def start_server(self):
        """Starts the server to listen for incoming connections."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind(("0.0.0.0", self.port))
            self.server_socket.listen(5)
            host_ip = socket.gethostbyname(socket.gethostname())
            print(f"[SERVER] Listening on {host_ip}:{self.port}")
        except Exception as e:
            print(f"[ERROR] Failed to start server: {e}")
            return

        while self.running:
            try:
                readable, _, _ = select.select([self.server_socket], [], [], 1)
                if readable:
                    client_socket, addr = self.server_socket.accept()
                    threading.Thread(target=self.handle_client, args=(client_socket, addr), daemon=True).start()
            except OSError:
                if not self.running:
                    print("[SERVER] Server shutting down.")
                    break

    def handle_client(self, client_socket, addr):
        """Handles messages received from connected peers."""
        try:
            message = client_socket.recv(1024).decode("utf-8").strip()
            if not message:
                return

            parts = message.split(" ", 2)
            if len(parts) == 3:
                sender_ip_port, team_name, chat_message = parts
                sender_ip, sender_port = sender_ip_port.split(":")
                sender_port = int(sender_port)
                
                print(f"{sender_ip}:{sender_port} {team_name}: {chat_message}")
                self.add_peer(sender_ip, sender_port)
                
                if chat_message.lower() == "exit":
                    print(f"[INFO] Peer {sender_ip}:{sender_port} disconnected.")
                    self.peers.discard((sender_ip, sender_port))
            else:
                print(f"[RECEIVED] Invalid format from {addr}: {message}")

            client_socket.sendall(f"[ACK] Message received from {self.port}".encode("utf-8"))
        except Exception as e:
            print(f"[ERROR] Handling client {addr}: {e}")
        finally:
            client_socket.close()

    def send_message(self, ip, port, message):
        """Sends a message to a peer following the required format."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.settimeout(5)
                client_socket.connect((ip, port))
                
                sender_ip = socket.gethostbyname(socket.gethostname())
                formatted_message = f"{sender_ip}:{self.port} {self.name} {message}"
                
                client_socket.sendall(formatted_message.encode("utf-8"))
                print(f"[SENT] {formatted_message}")

                response = client_socket.recv(1024).decode("utf-8").strip()
                print(f"[RECEIVED] {response}")

                self.add_peer(ip, port)  
        except (socket.timeout, ConnectionRefusedError):
            print(f"[ERROR] Peer {ip}:{port} is unreachable. Removing from list.")
            self.peers.discard((ip, port)) 
        except Exception as e:
            print(f"[ERROR] Sending message to {ip}:{port}: {e}")

    def add_peer(self, ip, port):
        """Adds a peer to the list if not already present."""
        peer = (ip, port)
        if peer not in self.peers:
            self.peers.add(peer)
            print(f"[PEER] Added {peer} to the list.")

    def query_peers(self):
        """Displays active peers."""
        if self.peers:
            print("Connected Peers:")
            for ip, port in sorted(self.peers):
                print(f"{ip}:{port}")
        else:
            print("No Connected Peers")

    def connect_to_peer(self, ip, port):
        """Establishes a connection with a peer."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((ip, port))
                sender_ip = socket.gethostbyname(socket.gethostname())
                connect_message = f"{sender_ip}:{self.port} {self.name} Connected"
                client_socket.sendall(connect_message.encode("utf-8"))
                
                print(f"[CONNECTED] To {ip}:{port}")
                
                response = client_socket.recv(1024).decode("utf-8").strip()
                print(response)
                
                self.add_peer(ip, port)
        except ConnectionRefusedError:
            print(f"[ERROR] Connection refused by {ip}:{port}. Ensure the peer is running.")
        except Exception as e:
            print(f"[ERROR] Connecting to {ip}:{port}: {e}")

    def connect_to_active_peers(self):
        """Attempts to connect to all known active peers."""
        for ip, port in list(self.peers):
            self.connect_to_peer(ip, port)

    def stop(self):
        """Stops the server and closes the socket."""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
            print("[SERVER] Server socket closed.")


def main():
    """Main menu for peer-to-peer messaging."""
    name = input("Enter your team name: ")
    port = int(input("Enter your port number: "))
    peer = Peer(name, port)
    
    server_thread = threading.Thread(target=peer.start_server, daemon=True)
    server_thread.start()
    
    while True:
        print("\n***** Menu *****")
        print("1 . Send message")
        print("2 . Query connected peers")
        print("3 . Connect to a peer")
        print("4 . Connect to active peers")
        print("0 . Quit")
        choice = input("Enter choice: ")
        
        if choice == "1":
            ip = input("Enter the recipient’s IP address: ")
            port = int(input("Enter the recipient’s port number: "))
            message = input("Enter your message: ")
            peer.send_message(ip, port, message)
        elif choice == "2":
            peer.query_peers()
        elif choice == "3":
            ip = input("Enter peer’s IP address: ")
            port = int(input("Enter peer’s port number: "))
            peer.connect_to_peer(ip, port)
        elif choice == "4":
            peer.connect_to_active_peers()
        elif choice == "0":
            peer.stop()
            print("Exiting...")
            break
        else:
            print("[ERROR] Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
