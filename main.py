from sys import path as sys_path
from os import path
sys_path.append(path.abspath(path.join(path.dirname(path.abspath(__file__)), "core/")))
from wg_monitor import wg_monitor

if __name__ == '__main__' :
    wg_monitor.run()