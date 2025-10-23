from sys import path as sys_path
from os import path
sys_path.append(path.abspath(path.join(path.dirname(path.abspath(__file__)), "core/")))
from monitor_wg import monitor_wg


if __name__ == '__main__' :
    monitor_wg()