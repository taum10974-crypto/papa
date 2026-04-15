import socket
import threading
import sys
import os
import ssl
import time

# Add libs to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'libs'))
try:
    import websocket
except ImportError:
    print("[!] Error: websocket-client library not found")
    sys.exit(1)

class PersistentBridge:
    def __init__(self, local_port, remote_ws_url):
        self.local_port = local_port
        self.remote_ws_url = remote_ws_url
        self.client_sock = None
        self.ws = None
        self.running = True

    def on_message(self, ws, message):
        if self.client_sock:
            try:
                if isinstance(message, bytes):
                    self.client_sock.sendall(message)
                else:
                    self.client_sock.sendall(message.encode('utf-8'))
            except Exception as e:
                print(f"[*!] Error: {e}")
                self.close_client()

    def on_error(self, ws, error):
        if "timeout" not in str(error).lower():
            print(f"[!] Error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("[*] WebSocket Connection Closed. Retrying...")
        time.sleep(2)

    def on_open(self, ws):
        print(f"[*] WebSocket Connected to {self.remote_ws_url}")

    def ws_thread(self):
        while self.running:
            self.ws = websocket.WebSocketApp(
                self.remote_ws_url,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close
            )
            # Use skip_utf8_validation for better performance with binary/stratum
            self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE}, ping_interval=30, ping_timeout=10)
            if not self.running: break
            time.sleep(5)

    def close_client(self):
        if self.client_sock:
            try: self.client_sock.close()
            except: pass
            self.client_sock = None

    def t_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('127.0.0.1', self.local_port))
        server.listen(1)

        while self.running:
            conn, addr = server.accept()
            self.close_client()
            self.client_sock = conn
            
            try:
                while True:
                    data = self.client_sock.recv(4096)
                    if not data: break
                    if self.ws and self.ws.sock and self.ws.sock.connected:
                        self.ws.send(data)
            except Exception as e:
                print(f"[!] Error: {e}")
            finally:
                self.close_client()

    def start(self):
        threading.Thread(target=self.ws_thread, daemon=True).start()
        self.t_server()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 bridge.py <local_port> <ws_url>")
        sys.exit(1)
    
    local_port = int(sys.argv[1])
    ws_url = sys.argv[2]
    bridge = PersistentBridge(local_port, ws_url)
    bridge.start()
