
#!/bin/python3

import subprocess
import os
import json
from time import sleep

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.join(BASE_DIR, "lib")
CONFIG_DIR = os.path.join(BASE_DIR, "config")

peer_states = {}

with open(os.path.join(CONFIG_DIR, "ip_map.json")) as f:
        IP_MAP = json.load(f)

def get_peer_name(ip):
    return IP_MAP.get(ip, "Unknown peer")

def run_wg_command(command="wg-show-handshake", args=""):
    """Run a shell command and return its output."""
    cmd = [f"{LIB_DIR}/{command}"]
    if args:
        cmd.append(args)
    
    result = subprocess.run(cmd, text=True, timeout=2, capture_output=True)
    if result.returncode != 0:
        raise Exception(f"Command failed: {cmd}\n{result.stderr}")
    return result.stdout.strip()

def parse_wg_output(output):
    """Parse the output of the wg command into a structured format."""
    lines = "\n".join(output.splitlines()[3:])
    tmp_peers = lines.split("\n\n")
    peers = {}
    for i in range(len(tmp_peers)):
        peer = tmp_peers[i]
        if ("allowed ips" not in peer) or ("latest handshake" not in peer) or ("transfer" not in peer):
            continue
        peer_lines = peer.splitlines()
        peer_dict = {} # value for each peer

        for line in peer_lines:
            key, value = line.split(":", 1)
            key, value = key.strip().lower(), value.strip()

            if key == "latest handshake":
                value = format_time(value)
                is_recent = is_recent_handshake(value)
                peer_dict["is_recent"] = is_recent
            elif key == "allowed ips":
                value = value[:value.find("/")] # extract only the IP address part
            peer_dict[key] = value

        peers[get_peer_name(peer_dict["allowed ips"])] = peer_dict
    return peers

def get_recent_handshakes(peers):
    recent_peers = {}
    for name, peer_info in peers.items():
        if peer_info.get("is_recent") and is_reachable(peer_info.get("allowed ips")):
            # ip = peer_info.get("allowed ips")
            # reachable = is_reachable(peer_info.get("allowed ips"))
            # print(f'wg-ping {ip} -- {reachable}')
            recent_peers[name] = peer_info
    return recent_peers

def is_reachable(ip) :
    reachable = run_wg_command("wg-ping", ip)
    return reachable == "True"


def get_pubkey(ip):
    output = run_wg_command("wg-pubkey")
    peers = output.split("\n\n")
    for peer in peers:
        if ip in peer:
            parts = peer.splitlines()
            return parts[0].split(": ", 1)[1]
    return None


def format_time(handshake) :
    handshake = handshake.replace(" ago", "")
    units = handshake.split(", ")
    total_seconds = 0
    for unit in units:
        if "Now" in unit :
            return 0
        number, label = unit.split(" ", 1)
        number = int(number)
        if "second" in label:
            total_seconds += number
        elif "minute" in label:
            total_seconds += number * 60
        elif "hour" in label:
            total_seconds += number * 3600
        elif "day" in label:
            total_seconds += number * 86400
    return total_seconds

def is_recent_handshake(handshake_time):
    """Check if the handshake time is within the last 2 minutes."""
    return handshake_time <= 120


def monitor_wg(interval=5): 
    
    while True:
        print("="*20 + " Checking for recent handshakes " + "="*20)
        output = run_wg_command()
        peers = parse_wg_output(output)
        connected = get_recent_handshakes(peers)

        disconnected = [k for k in peers.keys() if k not in connected.keys()]

        for allowed_ips, peer_info in connected.items():
            print(f"[+] Recent handshake for peer: \n{allowed_ips}: {peer_info}")

        for peer in disconnected:
            print(f"[-] Disconnected peer: \n{peer}: {peers[peer]}")

        sleep(interval)

def main():
    monitor_wg()


if __name__ == "__main__":
    main()
       