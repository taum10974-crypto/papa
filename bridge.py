import socket
import threading
import sys
import os
import json
import base64

# Add libs to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'libs'))
import websocket

class StratumBridge:
    def __init__(self, local_port, remote_ws_url):
        self.local_port = local_port
        self.remote_ws_url = remote_ws_url
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def handle_client(self, client_sock):

        ws = websocket.create_connection(self.remote_ws_url)
        
        def tcp_to_ws():
            try:
                while True:
                    data = client_sock.recv(4096)
                    if not data: break
                    # Stratum lines usually end with \n
                    messages = data.decode('utf-8').split('\n')
                    for msg in messages:
                        if msg.strip():
                            ws.send(msg + '\n')
            except Exception as e:
                print(f"[!] TCP to WS error: {e}")
            finally:
                ws.close()
                client_sock.close()

        def ws_to_tcp():
            try:
                while True:
                    msg = ws.recv()
                    if not msg: break
                    client_sock.sendall(msg.encode('utf-8'))
            except Exception as e:
                print(f"[!] WS to TCP error: {e}")
            finally:
                ws.close()
                client_sock.close()

        threading.Thread(target=tcp_to_ws, daemon=True).start()
        threading.Thread(target=ws_to_tcp, daemon=True).start()

    def run(self):
        self.server_sock.bind(('127.0.0.1', self.local_port))
        self.server_sock.listen(5)
        
        while True:
            client, addr = self.server_sock.accept()
            self.handle_client(client)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python3 bridge.py <local_port> <ws_url>")
        sys.exit(1)
    
    local_port = int(sys.argv[1])
    ws_url = sys.argv[2]
    bridge = StratumBridge(local_port, ws_url)
    bridge.run()
