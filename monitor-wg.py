
#!/bin/python3

from os import path, system, makedirs
from time import sleep
from sys import stdout
from wg_api import wg_api
import json


BASE_DIR = path.dirname(path.abspath(__file__))
STATE_FILE = path.join(BASE_DIR, "tmp/state.json")
makedirs(path.join(BASE_DIR, "tmp/"), exist_ok=True)

def write_to_file(peers) :
    with open(STATE_FILE, 'w') as f :
        json.dump(peers, f, indent=2)
    return

def monitor_wg(interval=5): 
    prev_states = set()
    while True:
        try :
            output = wg_api.run_wg_command()
            peers = wg_api.parse_wg_output(output)
            connected = wg_api.get_connected(peers)
            disconnected = [k for k in peers.keys() if k not in connected.keys()] # peers xor connected

            curr_peers = set(connected.keys())

            if curr_peers != prev_states:
                write_to_file(peers)
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
