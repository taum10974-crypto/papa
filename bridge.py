import socket
import threading
import sys
import os
import json
import base64
import ssl
import time

# Add libs to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'libs'))
try:
    import websocket
except ImportError:
    print("[!] Error: websocket-client library not found in libs/")
    sys.exit(1)

class StratumBridge:
    def __init__(self, local_port, remote_ws_url):
        self.local_port = local_port
        self.remote_ws_url = remote_ws_url
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def handle_client(self, client_sock):
        try:
            # Skip SSL verification for maximum compatibility on various VPS environments
            ws = websocket.create_connection(
                self.remote_ws_url, 
                sslopt={"cert_reqs": ssl.CERT_NONE},
                timeout=10
            )
        except Exception as e:
            print(f"[!] WS Connection failed: {e}")
            client_sock.close()
            return

        def tcp_to_ws():
            try:
                while True:
                    data = client_sock.recv(4096)
                    if not data: break
                    
                    try:
                        decoded_data = data.decode('utf-8')
                        messages = decoded_data.split('\n')
                        for msg in messages:
                            if msg.strip():
                                ws.send(msg + '\n')
                    except UnicodeDecodeError:
                        # Fallback for binary data if any
                        ws.send(data)
            except Exception as e:
                # Don't print "Connection is already closed" as a scary error if it was a normal closure
                if "closed" not in str(e).lower():
                    print(f"[!] TCP to WS error: {e}")
            finally:
                try: ws.close()
                except: pass
                try: client_sock.close()
                except: pass

        def ws_to_tcp():
            try:
                while True:
                    msg = ws.recv()
                    if not msg: break
                    
                    if isinstance(msg, bytes):
                        client_sock.sendall(msg)
                    else:
                        client_sock.sendall(msg.encode('utf-8'))
            except Exception as e:
                if "closed" not in str(e).lower():
                    print(f"[!] WS to TCP error: {e}")
            finally:
                try: ws.close()
                except: pass
                try: client_sock.close()
                except: pass

        threading.Thread(target=tcp_to_ws, daemon=True).start()
        threading.Thread(target=ws_to_tcp, daemon=True).start()

    def run(self):
        try:
            self.server_sock.bind(('127.0.0.1', self.local_port))
            self.server_sock.listen(10)
            print(f"[*] Bridge listening on 127.0.0.1:{self.local_port}")
            
            while True:
                client, addr = self.server_sock.accept()
                self.handle_client(client)
        except Exception as e:
            print(f"[!] Bridge server error: {e}")
        finally:
            self.server_sock.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 bridge.py <local_port> <ws_url>")
        sys.exit(1)
    
    local_port = int(sys.argv[1])
    ws_url = sys.argv[2]
    bridge = StratumBridge(local_port, ws_url)
    bridge.run()
