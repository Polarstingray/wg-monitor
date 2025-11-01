from dotenv import load_dotenv
from os import getenv, getlogin, path, makedirs
load_dotenv()

def get_int(var, default=0) :
    try :
        val = getenv(var)
        if not val :
            return default
        return int(val)
    except ValueError:
        return default

def get_bool(var, default=False):
    val = getenv(var)
    if not val:
        return default
    return (val.lower() in ['true', '1', 'yes', 'on'])


# setup
WEBHOOK_URL = getenv("WEBHOOK", "http://localhost:5000/api/wg/update")
WEB_EXT = get_bool("WEBEXT", False)
WEB_COOLDOWN = get_int("WEB_COOLDOWN", 6)

INTERVAL = get_int('INTERVAL', 5)
WG_OWNER =  getenv('WGMON_OWNER', getlogin())
WG_GROUP = getenv('WGMON_GROUP', 'serv-api')

BASE_DIR = path.join(path.dirname(path.abspath(__file__)), '../')
STATE_FILE = path.join(BASE_DIR, "tmp/state.json")
makedirs(path.join(BASE_DIR, "tmp/"), exist_ok=True)

if not WEB_EXT :
    print(f"Not sending POST requests to: {WEBHOOK_URL}")
else :
    print(f"Sending updates to: {WEBHOOK_URL}")

