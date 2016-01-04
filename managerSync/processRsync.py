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
        20160103: change struct of the dict
        object ={ 
                'source' = '',        # source directory
                '_targethost' = '',   #when app run, this will point to single target
                '_targetdir' = '',
                '_dict' = {             #_dict will saved in local
                            'target' = [(target_host, target_dir),],        # one source map mulit target , different column means different rsync transcation
                            'synced' = { file : [1, 0],      #user 1,0 point to different target rsync status( 1: synced, 0: not synced)
                            }     
              }
        step:
        1. load dict file, get history, or init new dict
        2. scan current directory, get file list
        3. compare current list with history send list, filter new_list
        4. process these new list for rsync
        5. update dict, add these success files and clean old list
    '''
    def __init__(self, *argv):
        self._source = os.path.normpath(argv[0]) + os.path.sep
        
        if len(argv) > 2:
            self._targethost, self._targetdir = argv[1:]
        
        self.DICT_FILE = "syncedDict"
        dictFile = os.path.join(self._source, self.DICT_FILE)

        if os.path.isfile(dictFile):
            with open(dictFile, 'rb') as f:
                self._dict = pickle.load(f)
        else:
            # create an dict file first
            self._dict = self.customDict(argv[1], argv[2])

    def customDict(self, *argv):
        '''
            if not found local dict files, then input some parameters init
        '''        
        cusdict = {}
        cusdict['target'] = []
        cusdict['synced'] = {}
        
        target_host, target_dir = '', ''
        if len(argv) == 1:
            target_host = argv[0]
        if len(argv) > 1:
            target_host, target_dir = argv
            
        if not target_host:
            target_host = input("please input the target host ip for rsync to: ")  or exit(1)
        # test if host available
        try_count = 0
        for i in range(3):
            try:
                try_count += 1
                if socket.gethostbyaddr(target_host):
                    break
            except (socket.gaierror,socket.herror) as e:
                pass
            if try_count == 3:  #all 5 time try failed
                print("host not available, try again")
                exit(1)
                
        if not target_dir:
            target_dir = input("please input the target sync dir module name for rsync to: ") or exit(1)
        self._targethost, self._targetdir = target_host, target_dir
        
        cusdict['target'].append( (target_host, target_dir) )
        return cusdict

    def compareDiff(self):
        # first scan local directory, get recent list
        current_snap = set()
        sync_index = self._dict['target'].index( (self._targethost, self._targetdir) )      # the index decide the which column synced file should marked
        
        for dir, subdir, files in os.walk(self._source):
            for file in files:
                filename = os.path.join(dir,file)
                relative_name = filename.replace(self._source, '')  # the rsync files-from config file use relative filename
                current_snap.add(relative_name)
        for expired_file in ( set(self._dict['synced'].keys()) - current_snap ):    #clean deleted file from sent_list
            self._dict['synced'][expired_file][sync_index] = 1
            if not 0 in self._dict['synced'][expired_file]:
                del self._dict['synced'][expired_file]      # all rsync transaction have done

        # compare current with sent ok history)
        incr_set = current_snap - {k for k in self._dict['synced'].keys() if self._dict['synced'][k][sync_index]}
        incr_list = list(incr_set)
        incr_list.sort()
        return incr_list

    def process(self, rsyncobj, newlist=[]):
        '''
            here need another object:processor  to solve the real work and return an ok list
        '''
        newlist = self.compareDiff()
        sent_ok = rsyncobj.syncList(newlist)

        self.updatelocalDict(sent_ok)       # call update


    def updatelocalDict(self, sent_list):
        '''
            update local dict file, for next using
        '''
        # update sent_list, delete those not in disk already(they have deleted)
        sync_index = self._dict['target'].index( (self._targethost, self._targetdir) )
        
        for file in sent_list:
            self._dict['synced'].setdefault( file, [0]* len(self._dict['target']) )
            self._dict['synced'][file][sync_index] = 1
        with open(os.path.join(self._source, self.DICT_FILE), 'wb') as w:
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
    if len(sys.argv) > 3 and os.path.isdir(sys.argv[1]):
        dirpro = ProcessDir(sys.argv[1], sys.argv[2], sys.argv[3])
        dirpro.process(RsyncProc(dirpro._source, dirpro._targethost, dirpro._targetdir))
    else:
        print("useage: python processFiles.py  directory")



