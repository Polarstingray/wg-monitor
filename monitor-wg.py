
#!/bin/python3

from os import path, system, makedirs, fsync, replace
from time import sleep
from sys import stdout
from wg_api import wg_api
import json, tempfile
from datetime import datetime


# BASE_DIR = path.dirname(path.abspath(__file__))
# STATE_FILE = path.join(BASE_DIR, "tmp/state.json")
# makedirs(path.join(BASE_DIR, "tmp/"), exist_ok=True)

# LOG_FILE = path.join(BASE_DIR, "log/connections.log")
# makedirs(path.join(BASE_DIR, "tmp/"), exist_ok=True)


BASE_DIR = path.dirname(path.abspath(__file__))
STATE_FILE = path.join(BASE_DIR, "tmp/state.json")
makedirs(path.join(BASE_DIR, "tmp/"), exist_ok=True)

LOG_FILE = path.join(BASE_DIR, "log/connections.log")
makedirs(path.join(BASE_DIR, "log/"), exist_ok=True)


def write_to_json(peers, filepath=STATE_FILE) :
    dirpath = path.dirname(filepath)
    with tempfile.NamedTemporaryFile("w", dir=dirpath, delete=False) as tmpfile :
        json.dump(peers, tmpfile, indent=2)
        tmpfile.flush()
        fsync(tmpfile.fileno())
        tempname = tmpfile.name
    replace(tempname, filepath)
        
def log(peers, status_=0) :
    print(peers)
    update = ''
    status = '[+] UP' if (status_ == 0) else '[-] DOWN'
    for name, peer_info in peers.items() :
        update += f'{status} {name} [{peer_info.get("ip")}] from [{peer_info.get('endpoint').get('ip')}] - {str(datetime.now())}\n'

    with open(LOG_FILE, 'a') as log :
        log.write(update)

def monitor_wg(interval=5): 
    prev_states = set()
    while True:
        try :
            peers = wg_api.get_peers()
            connected = wg_api.get_connected(peers)
            disconnected = [k for k in peers.keys() if k not in connected.keys()] # peers xor connected

            curr_peers = set(connected.keys())
            if curr_peers != prev_states:
                write_to_json(connected)
                difference = list(curr_peers - prev_states)
                newly_connected = {}
                for key in difference :
                    newly_connected[key] = connected.get(key)
                if newly_connected :
                    log(newly_connected)
            prev_states = curr_peers

            system('clear')
            print("="*20 + "Peer Status" + "="*20)
            for peer, peer_info in connected.items():
                print(f"[+] {peer} - Recent handshake:\n {peer_info}")

            for peer in disconnected:
                print(f"[-] {peer} - Disconnected peer:\n {peers[peer]}")

            delay(interval, verbose=True)

        except Exception as e:
            print(f"Error: {e}")

def delay(interval=5, verbose=False) :
    if (verbose) :
        for i in range(1, interval+1) :
            sleep(1)
            if i % interval == 0 :
                print(".")
                stdout.write("\033[1A" + "\x1b[2K") # ANSI esc seq for    cursor up + clear line
            else :
                print(".", end="")
            stdout.flush()
    else :
        sleep(interval)
        

if __name__ == "__main__":
    monitor_wg()
