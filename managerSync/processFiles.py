#!env python
# -*- encoding=utf-8 -*-
## author:Jianblog
## date:2015-12-30

import os, pickle, sys
import socket


class ProcessDir:
    '''
    note:
        monitor specify directory files, when processed(here is rsync) file ok, then mark these files as succ,
        next time if will not processed by processor
        every target directory has an dict file self (pickle), program will read it for process

        dict ={ 
                'send_history' = [],   #already processed ok
                'source_dir' = '',
                'target_host' = ip,
                'target_dirname' = name,  # rsync directory name
                'last_suc_time' = date
              }
        step:
        1. load dict file, get history, or init new dict
        2. scan current directory, get file list
        3. compare current list with history send list, filter new_list
        4. process these new list for rsync
        5. update dict, add these success files and clean old list
    '''
    def __init__(self, directory):
        self._directory = os.path.normpath(directory) + "/"
        self._current_list = []
        self.DICT_FILE = "syncedDict"
        dictFile = os.path.join(directory, self.DICT_FILE)

        self._dict = {}
        if os.path.isfile(dictFile):
            with open(dictFile, 'rb') as f:
                self._dict = pickle.load(f)
        else:
            # create an dict file first
            self.buildCustomDict()

    def buildCustomDict(self):
        '''
            if not found local dict files, then input some parameters init
        '''
        self._dict = {}
        self._dict['send_history'] = []
        self._dict['source_dir'] = self._directory
        while True:
            thost = input("please input the target host ip for rsync to: ")
            count = 0
            for i in range(5):
                count = i + 1
                try:
                    if socket.gethostbyaddr(thost):
                        self._dict['target_host'] = thost
                        count -= 1
                        break       # only exit for loop
                except (socket.gaierror,socket.herror) as e:
                    pass
            if count == 5:  #all 5 time try failed
                print("host not available, input again")
            break

        while True:
            tdir = input("please input the target rsync target dir alias name:")  
            if tdir:
                self._dict['target_dirname'] = tdir
                break   
        return

    def compareDiff(self):
        # first scan local directory, get recent list
        for dir, subdir, files in os.walk(self._directory):
            for file in files:
                filename = os.path.join(dir,file)
                relative_name = filename.replace(self._directory, '')
                self._current_list.append(relative_name)
        # compare current with sent ok history)
        sent_last = self._dict['send_history'] 
        new_list = {}.fromkeys(self._current_list).keys() - {}.fromkeys(sent_last).keys()
        return new_list

    def process(self, rsyncobj, newlist=[]):
        '''
            here need another object:processor  to solve the real work and return an ok list
        '''
        newlist = self.compareDiff()
        sent_ok = rsyncobj.syncList(newlist)

        self.updatelocalDict(sent_ok)       # call update


    def updatelocalDict(self, sentlist):
        '''
            update local dict file, for next using
        '''
        # update sent_list, delete those not in disk already(they have deleted)
        for f in self._dict['send_history']:
            if not f in self._current_list:
                self._dict['send_history'].remove(f)
        
        for file in sentlist:
            self._dict['send_history'].append(file)
        with open(os.path.join(self._directory, self.DICT_FILE), 'wb') as w:
            pickle.dump(self._dict, w)


class RsyncProc:
    def __init__(self, source_dir, target_host, target_dirname):
        self._synFromdir = source_dir
        self._synHost = target_host
        self._synTodir = target_dirname 

    def syncList(self, filelist):
        sync_list = os.path.join(self._synFromdir, 'synclist.txt')
        with open(sync_list, 'w') as f:
            for l in filelist:
                f.writelines(l + "\n")
        sync_cmd = "/usr/bin/rsync -avz --files-from=" + sync_list + " " + self._synFromdir + " " + self._synHost + "::" + self._synTodir
        sync_result = os.popen(sync_cmd)
        sent_ok = []
        for line in sync_result:
            line = line.strip()
            if os.path.isfile(os.path.join(self._synFromdir, line)):
                sent_ok.append(line)
        return sent_ok


if __name__ == '__main__':
    if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
        dirpro = ProcessDir(sys.argv[1])
        dirpro.process(RsyncProc(dirpro._directory, dirpro._dict['target_host'], dirpro._dict['target_dirname']))
    else:
        print("useage: python processFiles.py  directory")


