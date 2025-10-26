
#!/bin/python3

from os import path, system, makedirs, fsync, replace
from time import sleep
from sys import stdout, path as sys_path
import json, tempfile
from requests import post
from logger import update_logger

# WEBHOOK_URL = "http://localhost:5000/api/peer-update"

BASE_DIR = path.join(path.dirname(path.abspath(__file__)), '../')
STATE_FILE = path.join(BASE_DIR, "tmp/state.json")
sys_path.append(path.abspath(path.join(BASE_DIR, "core/"))) # add core/ to imports directory
makedirs(path.join(BASE_DIR, "tmp/"), exist_ok=True)

from wg_api.wg_api import wg_api

def write_to_json(peers, filepath=STATE_FILE) :
    dirpath = path.dirname(filepath)
    with tempfile.NamedTemporaryFile("w", dir=dirpath, delete=False) as tmpfile :
        json.dump(peers, tmpfile, indent=2)
        tmpfile.flush()
        fsync(tmpfile.fileno())
        tempname = tmpfile.name
    replace(tempname, filepath)

# def notify_web_app(updated_peers, status=0, url=WEBHOOK_URL) :
#     try :
#         payload = {
#             "status" : "connected" if (status==0) else "disconnected",
#             "timestamp" : datetime.now().isoformat(),
#             "peers" : updated_peers
#         }
#         post(url, json=payload, timeout=2)
#     except Exception as e :
#         print(f'[!] Failed to send update to web app: {e}')

def console_log(connected, disconnected, update) :
    # Console output
    print("="*20 + "Peer Status" + "="*20)
    for peer, peer_info in connected.items():
        print(f"[+] {peer} - Recent handshake:\n {peer_info}")

    for peer in disconnected:
        print(f"[-] {peer} - Disconnected peer")

    for notification in update :
        print(f'  [NOTIFICATION]: {notification.strip()}')

class WgMonitor :
    def __init__(self) :
        self.prev_states = set()

    def run(self, interval=5): 
        while True:
            try :
                self.check_peers()
                wg_monitor.delay(interval)
            except Exception as e:
                print(f"Error: {e}")

    def check_peers(self) :
        # querry peer handshakes
        peers = wg_api.get_peers()
        connected = wg_api.get_connected(peers) 
        disconnected = [k for k in peers.keys() if k not in connected.keys()] # peers xor connected

        curr_peers = set(connected.keys())
        update = []
        if curr_peers != self.prev_states:
            write_to_json(peers) # update all states in tmp/state.json
            newly_updated = self.get_newly_updated(peers, curr_peers)
            update = update_logger.log(newly_updated)
        self.prev_states = curr_peers        
        console_log(connected, disconnected, update)

    def get_newly_updated(self, peers, curr) :
            connected = list(curr - self.prev_states)
            disconnected = list(self.prev_states - curr)
            newly_updated = {}
            if connected :
                newly_updated["connected"] = {k: peers[k] for k in connected}
            if disconnected :
                newly_updated["disconnected"] = {k: peers[k] for k in disconnected}
            return newly_updated

    @staticmethod
    def delay(interval=5, verbose=True) :
        # clears terminal output and displays loading (...)s
        if (not verbose) :
            for i in range(1, interval+1) :
                sleep(1)
                if i % interval == 0 :
                    print(".")
                    stdout.write("\033[1A" + "\x1b[2K") # ANSI esc seq for    cursor up + clear line
                else :
                    print(".", end="")
                stdout.flush()
            system('clear')
        else :
            sleep(interval)
            
wg_monitor = WgMonitor()

if __name__ == "__main__":
    wg_monitor.run()
    pass
