from io import StringIO
import logging
from os import makedirs, path
from subprocess import run

BASE_DIR = path.join(path.dirname(path.abspath(__file__)), '../')
LOG_DIR = path.join(BASE_DIR, "log/")

class UpdateLogger :
    def __init__(self, log_dir=LOG_DIR) :
        self.log_dir = log_dir
        makedirs(self.log_dir, exist_ok=True)

        self.log_stream = StringIO()
        self.update_logger = logging.getLogger('update_logger')
        self.update_logger.setLevel(logging.INFO)
        self._setup_handlers()

    def _setup_handlers(self):
        format = '%(message)s - %(levelname)s - %(asctime)s'
        # update log handler
        update_handler = logging.FileHandler(f'{self.log_dir}/updates.log')
        update_handler.setFormatter(
            logging.Formatter(format)
        )
        self.update_logger.addHandler(update_handler)

        # captures log message
        stream_handler = logging.StreamHandler(self.log_stream)
        stream_handler.setFormatter(
            logging.Formatter(format)
        )
        self.update_logger.addHandler(stream_handler)

        # Error log handler
        error_handler = logging.FileHandler(f'{self.log_dir}/errors.log')
        error_handler.setFormatter(
            logging.Formatter(format)
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
        update = []
        if not updated_peers :
            return update
        for state, peers in updated_peers.items() :
            status = '[+] UP' if (state == "connected") else '[-] DOWN'
            for name, peer_info in peers.items() :
                try :
                    self.update_logger.info(f'{status} {name} [{peer_info.get("ip")}] from [{peer_info.get("endpoint", {}).get("ip")}]')
                except Exception as e :
                    print(f"Error: {str(e)}") 
                    self.update_logger.error(
                        f"Error: {str(e)}",
                        exc_info=True
                    )
                    raise
                self.log_stream.seek(0)
                notification = self.log_stream.getvalue()
                update.append(notification)
            if (state == "connected") : run(['wall', f'[wg-monitor] Updated peers: \n{''.join(update)}']) # Notify server
        return update

update_logger = UpdateLogger()
