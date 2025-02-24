import socket
import threading
import select

class Peer:
    def __init__(self, name, port):
        self.name = name
        self.port = port
        self.peers = set()
        self.chat_history = {}
        self.server_socket = None
        self.running = True
        self.server_ip = socket.gethostbyname(socket.gethostname())

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind(("0.0.0.0", self.port))
            self.server_socket.listen(5)
            print(f"Server listening on {self.server_ip}:{self.port}")
        except Exception as e:
            print(f"Failed to start server: {e}")
            return

        while self.running:
            try:
                readable, _, _ = select.select([self.server_socket], [], [], 1)
                if readable:
                    client_socket, addr = self.server_socket.accept()
                    threading.Thread(target=self.handle_client, args=(client_socket, addr), daemon=True).start()
            except OSError:
                if not self.running: break

    def handle_client(self, client_socket, addr):
        try:
            message = client_socket.recv(1024).decode("utf-8").strip()
            if not message: return

            parts = message.split(' ', 2)
            if len(parts) < 3:
                print("Invalid message format")
                return

            ip_port, team_name, msg = parts
            print(f"Received: {ip_port} {team_name}: {msg}")

            if ip_port not in self.peers and ip_port != f"{self.server_ip}:{self.port}":
                self.peers.add(ip_port)
                print(f"New peer: {ip_port}")

            if ip_port not in self.chat_history:
                self.chat_history[ip_port] = []
            self.chat_history[ip_port].append(f"{team_name}: {msg}")

            if msg.lower() == "exit":
                self.peers.discard(ip_port)
                print(f"{ip_port} disconnected")
                return

            client_socket.sendall(f"ACK from {self.port}".encode("utf-8"))
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()

    def send_message(self):
        ip = input("Enter recipient IP (Enter=localhost): ") or "127.0.0.1"
        port = int(input("Enter recipient port: "))
        message = input("Enter your message: ")
        peer_id = f"{ip}:{port}"
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect((ip, port))
                formatted_msg = f"{self.server_ip}:{self.port} {self.name} {message}"
                s.sendall(formatted_msg.encode("utf-8"))
                
                self.peers.add(peer_id)
                
                if peer_id not in self.chat_history:
                    self.chat_history[peer_id] = []
                self.chat_history[peer_id].append(f"You: {message}")
                
                print(f"Message sent to {peer_id}")
        except Exception as e:
            print(f"Failed to send: {e}")
            self.peers.discard(peer_id)

    def query_peers(self):
        print("\nConnected Peers:" if self.peers else "\nNo connected peers!")
        for peer in sorted(self.peers):
            print(peer)

    def connect_to_peer(self):
        ip = input("Enter peer's IP address: ")
        port = int(input("Enter peer's port number: "))
        peer_id = f"{ip}:{port}"
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect((ip, port))
                msg = f"{self.server_ip}:{self.port} {self.name} Connection request"
                s.sendall(msg.encode("utf-8"))
                
                self.peers.add(peer_id)
                if peer_id not in self.chat_history:
                    self.chat_history[peer_id] = []
                self.chat_history[peer_id].append(f"You: Connection established")
                
                print(f"Connected to {peer_id}")
        except Exception as e:
            print(f"Connection failed: {e}")

    def connect_active_peers(self):
        for peer in list(self.peers):
            ip, port = peer.split(":")
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(5)
                    s.connect((ip, int(port)))
                    msg = f"{self.server_ip}:{self.port} {self.name} Reconnection"
                    s.sendall(msg.encode("utf-8"))
                    print(f"Reconnected to {peer}")
            except Exception as e:
                print(f"Failed to reconnect to {peer}: {e}")

    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        for peer in list(self.peers):
            ip, port = peer.split(":")
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(3)
                    s.connect((ip, int(port)))
                    s.sendall(f"{self.server_ip}:{self.port} {self.name} exit".encode("utf-8"))
            except:
                pass

def main():
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
        
        choice = input("Enter choice: ").strip()
        
        if choice == '1':
            peer.send_message()
        elif choice == '2':
            peer.query_peers()
        elif choice == '3':
            peer.connect_to_peer()
        elif choice == '4':
            peer.connect_active_peers()
        elif choice == '0':
            peer.stop()
            print("Exiting...")
            break
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    main()
