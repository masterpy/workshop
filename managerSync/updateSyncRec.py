#!python3

import os, pickle, sys, datetime, time
import socket

'''
    scirpt: updateSyncRec.py
    date:  2015-01-18
    author: jianblog
    note: a shedule job after rsync, it's purpose is to update local rsync dict records. 
    to solve the problem: when rsync return file list, check it still not exist at the same time.  
    so run this script after sync to update local dict.
'''

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DICT_DIR = os.path.join(APP_DIR, 'rconf')

if __name__ == '__main__':
    dict = {}

    if len(sys.argv) < 2:
        print("useage: updateSyncRec.py sync.dict")
        exit(1)

    if len(sys.argv) >= 3:
        rconf_file = sys.argv[1]
        day_diff = sys.argv[2]
    if len(sys.argv) == 2:
        rconf_file = sys.argv[1]
        day_diff = 7

    if not os.path.isfile(os.path.join(DICT_DIR, rconf_file)):
            print('not found rsync dict file')
            exit(1)
    with open(os.path.join(DICT_DIR, rconf_file), 'rb') as f:
        dict = pickle.load(f)

    indx = 0    # position of file   file:[1,0]
    for group in dict['group']:
        target_path = group[2]
        option = " -mtime -" + day_diff 
        recent_list = os.popen("find " + target_path + option)


        for file in recent_list:
            file = file.strip()
            if os.path.isfile(file):
                rela = file.replace(os.path.normpath(target_path) + os.path.sep, '')
                if rela.endswith('.gz'):
                    rela = rela[:-3]

                if not dict['records'].get(rela):   #rencet synced file not in record, then add it
                    dict['records'][rela] = [0] * len(dict['group'])

                if len(dict['records'][rela]) < (indx + 1):    # first add position
                    dict['records']['rela'].append(0)

                if dict['records'][rela][indx] == 0:    
                    dict['records'][rela][indx] = 1
                    print("update: ", rela)
        indx += 1

    with open(os.path.join(DICT_DIR, rconf_file), 'wb') as f:
        pickle.dump(dict, f)
