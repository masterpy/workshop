#!/usr/bin/python
# -*- coding:utf-8 -*-

# date:2015-11-26
# desc: recursive get all files in the directory
# author: Jianblog@live.com

import os,sys
import shutil
import time



def get_origin_list():
    root = '/tmp_share/webroot/offerwall/4logs'

    for path, subdir, files in os.walk(root):
        for f in files:
            print(os.path.join(path,f))
        

def compare_target(s, t):
    source_base_dir = s
    target_base_dir = t

    for path, subdir, files in os.walk(source_base_dir):
        for file in files:
            target = file.replace(source_base_dir, target_base_dir)
            if not os.path.isfile(target):
                print(file)


def sync_files(file_list):
    source_base_dir = '/run/media/appmon/4a3cf23e-f9cb-4df8-a13b-e4929e20896c'
    target_base_dir = '/tmp_share'

    with open(file_list, 'r') as f:
       for file in f:
           file = file.strip()
           target = file.replace(source_base_dir, target_base_dir)
           target_dir = os.path.dirname(target)

           if not os.path.isdir(target_dir):
               os.makedirs(target_dir)
           while True:
               try:
                   shutil.copyfile(file, target)
                   print(file)
                   break
               except OSError as e:
                   print(e, " : ", file)
                   print("sleep 10s...")
                   time.sleep(10)



if __name__ == '__main__':

    '''
       for cause of bad disk and not in same host,run separately:

       1. call et_origin_list to get full file list of source directory
       2. call compare_target to find files not exist in target directory but exist in source directory
       3. copy these files got from 2 to target directory

    '''

    #1
    get_origin_list()

    #2
    compare_target(sys.argv[1], sys.argv[2])

    #3
    #sync_files(sys.argv[1])
