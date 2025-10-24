
from subprocess import run
from os import path
from json import load

peer_states = {}

class WgAPI :

    def __init__(self, base_dir=path.dirname(path.abspath(__file__)), iface='wg0') :
        self.lib_dir = path.join(base_dir, "lib")
        self.config_dir = path.join(base_dir, "config")
        self.iface = iface
        with open(path.join(self.config_dir, "ip-map.json")) as f:
            self.ip_map = load(f)

    def get_peer_name(self, ip):
        return self.ip_map.get(ip, "Unknown peer")

    def run_wg_command(self, command, *args):
        """Run a command from library and return its output."""
        cmd_path = path.join(self.lib_dir, command)
        cmd = [cmd_path] + list(args)
        try :
            result = run(cmd, text=True, timeout=3, capture_output=True, check=True)
            return result.stdout.strip()
        except Exception as e:
            raise RuntimeError(f"[WgAPI] Command failed: {' '.join(cmd)} — {e}")
        
    def get_peers(self) :
            output = self.run_wg_command(command="wg-show-handshake")
            return self.parse_wg_output(output)

    def parse_wg_output(self, output):
        """Parse the output of the wg command into a structured format."""
        
        # lines = "\n".join(output.splitlines()[3:])
        tmp_peers = ("\n".join(output.splitlines()[3:])).split("\n\n") 
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

                match key:
                    case "latest handshake":
                        value = self.format_time(value)
                        is_recent = self.is_recent_handshake(value)
                        peer_dict["connected"] = is_recent
                    case "allowed ips":
                        key, value = "ip", value[:value.find("/")] # extract only the IP address part
                    case "transfer":
                        value = self.format_transfer(value)
                    case "endpoint":
                        value = self.format_endpoint(value)
                    
                peer_dict[key] = value
            peers[self.get_peer_name(peer_dict["ip"])] = peer_dict
        return peers
    
    def format_endpoint(self, value) :
        tmp = value.split(":")
        return {"ip" : tmp[0], "port" : tmp[1]}

    def format_transfer(self, value) :
        tmp = value.split(", ")
        tmp[0], tmp[1] = tmp[0].split(" ")[:-1], tmp[1].split(" ")[:-1]
        return {"recieved" : {tmp[1][1] : tmp[1][0]}, "sent" : {tmp[0][1] : tmp[0][0]}}

    def get_connected(self, peers):
        recent_peers = {}
        for name, peer_info in peers.items():
            if peer_info.get("connected") : #and self.is_reachable(peer_info.get("ip")):
                recent_peers[name] = peer_info
        return recent_peers

    def is_reachable(self, ip) :
        reachable = self.run_wg_command("wg-ping", ip)
        return reachable == "True"


    def get_pubkey(self, ip):
        output = self.run_wg_command("wg-pubkey")
        peers = output.split("\n\n")
        for peer in peers:
            if ip in peer:
                parts = peer.splitlines()
                return parts[0].split(": ", 1)[1]
        return None

    def format_time(self, handshake) :
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

    def is_recent_handshake(self, handshake_time):
        """Check if the handshake time is within the last 2 minutes."""
        return handshake_time <= 130


wg_api = WgAPI()


