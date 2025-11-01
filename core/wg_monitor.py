
#!/bin/python3

import os, json, tempfile, time
from pwd import getpwnam
from grp import getgrnam
from sys import stdout
from time import sleep
from subprocess import run
from dotenv import load_dotenv
from requests import post

from logger import update_logger, log_format
from wg_api.wg_api import wg_api
import config


# BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../')
# STATE_FILE = os.path.join(BASE_DIR, "tmp/state.json")
# os.makedirs(os.path.join(BASE_DIR, "tmp/"), exist_ok=True)

def console_log(connected, disconnected, updates) :
    # Console output
    print("="*20 + "Peer Status" + "="*20)
    for peer, peer_info in connected.items():
        print(f"[+] {peer} - Recent handshake:\n {peer_info}")

    for peer in disconnected:
        print(f"[-] {peer} - Disconnected peer")

    notification = []
    for event in updates :
        notice = log_format(event)
        if event.get('status') :
            notification.append(notice)
        print(f'  [NOTIFICATION]: {notice}')

    if notification : run(
        ['wall', f"[wg-monitor] Updated peers: \n{'\n'.join(notification)}"]) # Notify server
        
class StateMgr :
    def __init__(self, file_path=config.STATE_FILE, owner=os.getuid(), group='serv-api') :
        self.filepath=file_path
        self.owner = getpwnam(owner).pw_uid if isinstance(owner, str) else (owner or os.getuid())
        self.group=getgrnam(group).gr_gid

    # Issue in being able to read state
    def save(self, peers) :
        dirpath = os.path.dirname(self.filepath)
        with tempfile.NamedTemporaryFile("w", dir=dirpath, delete=False) as tmpfile :
            json.dump(peers, tmpfile, indent=2)
            tmpfile.flush()
            os.fsync(tmpfile.fileno())
            tempname = tmpfile.name
        os.replace(tempname, self.filepath)
        os.chown(self.filepath, self.owner, self.group)
        os.chmod(self.filepath, 0o640)

class WebNotifier :
    def __init__(self, url=config.WEBHOOK_URL, cooldown=config.WEB_COOLDOWN) :
        self.last_update = 0 - cooldown
        self.url = url
        self.cooldown = cooldown
    
    def send_update(self, updates) :
        curr_time = time.time()
        print(curr_time)
        print(curr_time - self.last_update > self.cooldown)
        if (not updates) or (curr_time - self.last_update > self.cooldown):
            return
        try :
            payload = {
                "update" : updates,
            }
            post(self.url, json=payload, timeout=2)
            self.last_update = time.time()
        except Exception as e :
            print(f'[!] Failed to send update to web app: {e}')

class WgMonitor :
    def __init__(self, interval=config.INTERVAL) :
        self.interval=interval
        self.prev_states = set()
        self.peers = {}
        self.state_mgr = StateMgr(owner=config.WG_OWNER, group=config.WG_GROUP) 
        self.web_notifier = WebNotifier()
  
    def run(self): 
        while True:
            try :
                connected, disconnected, updates = self.check_peers()
                console_log(connected, disconnected, updates)
                if (config.WEB_EXT  and updates) : self.web_notifier.send_update(updates)
            except Exception as e:
                print(f"Error: {e}")
            WgMonitor.delay(self.interval)

    def check_peers(self) :
        # querry peer handshakes
        self.peers = wg_api.get_peers()
        connected = wg_api.get_connected(self.peers) 
        disconnected = [k for k in self.peers.keys() if k not in connected.keys()]

        curr_peers = set(connected.keys())
        updates = []
        if curr_peers != self.prev_states:
            self.state_mgr.save(self.peers) # update all states in tmp/state.json

            newly_updated = self.get_newly_updated(curr_peers)
            updates = update_logger.log(newly_updated)
        self.prev_states = curr_peers        

        return connected, disconnected, updates

    def get_newly_updated(self, curr) :
            connected = list(curr - self.prev_states)
            disconnected = list(self.prev_states - curr)
            newly_updated = {}
            if connected :
                newly_updated["connected"] = {k: self.peers[k] for k in connected}
            if disconnected :
                newly_updated["disconnected"] = {k: self.peers[k] for k in disconnected}
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
            os.system('clear')
        else :
            sleep(interval)
            
wg_monitor = WgMonitor()

if __name__ == "__main__":
    wg_monitor.run()
    pass
