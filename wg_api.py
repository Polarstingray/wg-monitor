
from subprocess import run
from os import path
from json import load

BASE_DIR = path.dirname(path.abspath(__file__))
LIB_DIR = path.join(BASE_DIR, "lib")
CONFIG_DIR = path.join(BASE_DIR, "config")

peer_states = {}

with open(path.join(CONFIG_DIR, "ip-map.json")) as f:
    IP_MAP = load(f)
class WgAPI :

    @staticmethod
    def get_peer_name(ip):
        return IP_MAP.get(ip, "Unknown peer")

    @staticmethod
    def run_wg_command(command="wg-show-handshake", args=""):
        """Run a command from library and return its output."""
        cmd = [f"{LIB_DIR}/{command}"]
        if args:
            cmd.append(args)
        
        result = run(cmd, text=True, timeout=2, capture_output=True)
        if result.returncode != 0:
            raise Exception(f"Command failed: {cmd}\n{result.stderr}")
        return result.stdout.strip()

    @staticmethod
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
                    value = WgAPI.format_time(value)
                    is_recent = WgAPI.is_recent_handshake(value)
                    peer_dict["is recent"] = is_recent
                elif key == "allowed ips":
                    key, value = "ip", value[:value.find("/")] # extract only the IP address part
                elif key == "transfer":
                    value = WgAPI.format_transfer(value)
                elif key == "endpoint":
                    value = WgAPI.format_endpoint(value)
                    
                peer_dict[key] = value

            peers[WgAPI.get_peer_name(peer_dict["ip"])] = peer_dict
        return peers
    
    @staticmethod
    def format_endpoint(value) :
        endpoint = {}
        tmp = value.split(":")
        endpoint["ip"] = tmp[0]
        endpoint["port"] = tmp[1]
        return endpoint

    @staticmethod
    def format_transfer(value) :
        transfer, tmp = {}, value.split(", ")
        tmp[0], tmp[1] = tmp[0].split(" ")[:-1], tmp[1].split(" ")[:-1]
        transfer["recieved"] = {tmp[1][1] : tmp[1][0]}
        transfer["sent"] = {tmp[0][1] : tmp[0][0]}
        return transfer

    @staticmethod
    def get_connected(peers):
        recent_peers = {}
        for name, peer_info in peers.items():
            if peer_info.get("is recent") and WgAPI.is_reachable(peer_info.get("ip")):
                recent_peers[name] = peer_info
        return recent_peers

    @staticmethod
    def is_reachable(ip) :
        reachable = WgAPI.run_wg_command("wg-ping", ip)
        return reachable == "True"


    @staticmethod
    def get_pubkey(ip):
        output = WgAPI.run_wg_command("wg-pubkey")
        peers = output.split("\n\n")
        for peer in peers:
            if ip in peer:
                parts = peer.splitlines()
                return parts[0].split(": ", 1)[1]
        return None

    @staticmethod
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

    @staticmethod
    def is_recent_handshake(handshake_time):
        """Check if the handshake time is within the last 2 minutes."""
        return handshake_time <= 120





