#!python3

import os, pickle, sys

'''
    scirpt: updateSyncRec.py
    date:  2015-01-18
    author: jianblog
    note: a shedule job after rsync, it's purpose is to update local rsync dict records. 
    to solve the problem: when rsync return file list, check it still not exist at the same time.  
'''

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DICT_DIR = os.path.join(APP_DIR, 'rconf')

if __name__ == '__main__':
    dict = {}

    if len(sys.argv) == 4:
        remote_ip = sys.argv[1]
        remote_dir = sys.argv[2]
        local_dir = os.path.normpath(sys.argv[3])
        dict['group'] = []
        dict['group'].append( (remote_ip, remote_dir, local_dir) )
        dict['records'] = {}
    else:
        print("useage: updateSyncRec.py sync.dict")
        exit(1)

    recent_list = os.popen("find " + local_dir + "/")    #here need / or it dont search sub dir


    for file in recent_list:
        file = file.strip()
        if os.path.isfile(file):
            rela = file.replace(os.path.normpath(local_dir) + os.path.sep, '')
            if rela.endswith('.gz'):
                rela = rela[:-3]

            if not dict['records'].get(rela):   #rencet synced file not in record, then add it
                dict['records'][rela] = [1]

    rconf_file = remote_ip + "_" + remote_dir + ".dic"
    with open(os.path.join(DICT_DIR, rconf_file), 'wb') as f:
        pickle.dump(dict, f)
