from io import StringIO
import logging
from os import makedirs, path
from subprocess import run
from datetime import datetime


BASE_DIR = path.join(path.dirname(path.abspath(__file__)), '../')
LOG_DIR = path.join(BASE_DIR, "log/")

class UpdateLogger :
    def __init__(self, log_dir=LOG_DIR) :
        self.log_dir = log_dir
        makedirs(self.log_dir, exist_ok=True)

        self.update_logger = logging.getLogger('update_logger')
        self.update_logger.setLevel(logging.INFO)
        self._setup_handlers()

    def _setup_handlers(self):
        # update log handler
        update_handler = logging.FileHandler(f'{self.log_dir}/updates.log')
        update_handler.setFormatter(
            logging.Formatter('%(message)s')
        )
        self.update_logger.addHandler(update_handler)

        # Error log handler
        error_handler = logging.FileHandler(f'{self.log_dir}/errors.log')
        error_handler.setFormatter(
            logging.Formatter('%(levelname)s - %(message)s - %(asctime)s')
        )
        error_handler.setLevel(logging.ERROR)
        self.update_logger.addHandler(error_handler)

    def log(self, updated_peers) :
        """
        Logs updates about peers' connection status.

        Parameters:
            updated_peers (dict): Dictionary containing peer states and their info.
            filepath (str): Path to the log file where updates are written.
            status_ (int): Status flag to determine if a wall notification should be sent (0 to send).

        Returns:
            str: The log message that was written.
        """
        updates = []
        if not updated_peers :
            return updates
        for state, peers in updated_peers.items() :
            for name, peer_info in peers.items() :
                try :
                    event = {
                        "status": True if state == "connected" else False,
                        "name": name,
                        "ip": peer_info.get("ip"),
                        "endpoint": peer_info.get("endpoint", {}).get("ip"),
                        "timestamp": datetime.now().isoformat()
                    }
                    self.update_logger.info(log_format(event))
                    updates.append(event)
                except Exception as e :
                    self.update_logger.error(
                        f"Error: {str(e)}",
                        exc_info=True
                    )
                    raise
        return updates
    
def log_format(event) :
    status = '[+] UP' if (event.get("status")) else '[-] DOWN'
    return f'{status} - {event.get('name')} [{event.get('ip')}] from [{event.get('endpoint')}] - {event.get('timestamp')}'
                
update_logger = UpdateLogger()
