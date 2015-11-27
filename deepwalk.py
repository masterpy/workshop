#!/usr/bin/python
# -*- coding:utf-8 -*-

# date:2015-11-26
# desc: recursive get all files in the directory
# author: Jianbo

import os,sys
import shutil



def get_origin_list():
    root = '/run/media/appmon/4a3cf23e-f9cb-4df8-a13b-e4929e20896c/webroot/offerwall/sendMsg'

    for path, subdir, files in os.walk(root):
        for f in files:
            print(os.path.join(path,f))
        

def compare_target(source_list):
    source_base_dir = '/run/media/appmon/4a3cf23e-f9cb-4df8-a13b-e4929e20896c' 
    target_base_dir = '/data'

    with open(source_list, 'r') as f:
        for file in f:
            file = line.strip()
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
           try:
               shutil.copyfile(file, target)
               print(file)
           except OSError as e:
               print(e)
               exit()



if __name__ == '__main__':

'''
   for cause of bad disk and not in same host,run separately:

   1. call et_origin_list to get full file list of source directory
   2. call compare_target to find files not exist in target directory but exist in source directory
   3. copy these files got from 2 to target directory
'''

   #1
   # get_origin_list()

   #2
   # compare_target(sys.argv[1])

   #3
   sync_files(sys.argv[1])
