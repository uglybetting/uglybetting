#!/usr/bin/env python
__author__ = "Rob Cartwright"

import  time
import  sys
from    src.data_collect.get_nap_data import NapData

sys.path.insert(0, 'D:/Python/uglybetting')
nd = NapData()

def update_loop():
    # run from 0600 - 2200. Scheduler is set to run from 0600
    sleep_len = 120
    loops = 480
    cnt = 0
    while cnt <= loops:
        nd.update_today_table()
        cnt += 1
        time.sleep(sleep_len)
        print(cnt)

if __name__ == "__main__":
    update_loop()