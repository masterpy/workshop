#!env python
# -*- encoding=utf-8 -*-
## author:Jianblog
## date:2016-01-13

'''
    note: originally the first edition of rsync app was deploy with the source files, 
            it scan local directory and compare with history then decide which file to rsync. it's a push mode
          now, i decide the second edition, deploy the app in the backuped server, 
          first it also run rsync only get a full file list,
          then compare with history getted before. then run rysnc. it's a get mode
          so the command parameter changeed:
           processRsync.py  -avz --files-from= remoteServer::module   local_dir

        step:
        1. load dict file, get history, or init new dict
        2. run rsync list mode to get fresh list now
        3. compare fresh list with history send list, filter new_list
        4. process these new list for rsync
        5. update dict, add these success files and clean old list

'''
import os, pickle, sys, datetime, time
import socket

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DICT_DIR = os.path.join(APP_DIR, 'rconf')

class ProcessBackup:
    '''
    note:
        monitor specify directory files, when processed(here is rsync) file ok, then mark these files as succ,
        next time if will not processed by processor
        every target directory has an dict file self (pickle), program will read it for process
        20160103: change struct of the dict
        object ={ 
                'remote_server' = '',   # remote server
                'remote_module' = '',   # remote rsync module name configureed in /etc/rsyncd.conf
                'backup_dir' = '',
                'dict' = {}          # set of files sent history
                }
    '''
    def __init__(self, *karg, **kwarg):

        if len(karg) > 2:
            self.remote_server, self.remote_module, self.backup_dir = karg
            if not os.path.isdir(self.backup_dir):
                print("local backup dir not exist, create first")
                exit(1)
        else:
            self.remote_server, self.remote_module = karg
            self.backup_dir = None
        self.addition = {}
        self.dict = {}
        '''
            dict = { 'group': [(remote_server, remote_module, backup_dir),]
                     'records': { filea: [1, 0],   fileb: [1, 1]}
                    }
        '''

        dictfile = os.path.join(DICT_DIR, self.remote_server + '_' + self.remote_module + '.dic')
        if os.path.isfile(dictfile):
            # load
            with open(dictfile, 'rb') as f:
                self.dict = pickle.load(f)
            if not self.backup_dir and len(self.dict['group']) == 1:     # default with no localdir parameter
                self.backup_dir = self.dict['group'][0][2]
            if self.backup_dir in [ grp[2] for grp in self.dict['group'] ]:
                pass    # backup_dir match the dict 
            else:
                # add a new backup directory
                self.dict['group'].append( (self.remote_server, self.remote_module, self.backup_dir) )
        else:   # no dict found
            if not self.backup_dir:
                print(" need define backup directory.")
                exit(1)
            # init new dict
            self.dict['group'] = []
            self.dict['group'].append( (self.remote_server, self.remote_module, self.backup_dir) )
            self.dict['records'] = {}

        for k in kwarg:      # read include and exclude file, save as hash
            dic = {}
            with open(karg[k], 'r') as f:
                for line in f:
                    line = line.strip()
                    dic[line] = 1
            self.addition[k] = dic

    def customDict(self, *argv):
        '''
            if not found local dict files, then input some parameters init
        '''        
        cusdict = {}
        cusdict['target'] = []
        cusdict['synced'] = {}
        
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
        # first run rsync list mode get fresh file list
        current_snap = set()
        sync_index = self.dict['group'].index( (self.remote_server, self.remote_module, self.backup_dir) )      # the index decide the which column synced file should marked
        
        cur_list = os.popen("rsync -r " + self.remote_server + "::" + self.remote_module).readlines()
        for line in cur_list:
            line = line.strip().split()
            if len(line) == 5 and line[4] != '.':
                current_snap.add(line[4])
        for nofile in ( self.dict['records'].keys() - current_snap ):
            del self.dict['records'][nofile]    #if file in local dict but not exist in fresh list, it can delete from dict
        fresh_set = current_snap - {k for k in self.dict['records'].keys() if self.dict['records'][k][sync_index]}
        return fresh_set

    def compareFilter(self, fresh_list):
        sync_list = []
        for fresh in fresh_list:
            if self.addition.get('exclude'):
                if self.addition['exclude'].get(fresh):
                    continue
            if self.addition.get('include'):
                for inc in self.addition['include']:
                    if fresh.startswith(inc):
                        sync_list.append(fresh)
                    else:
                        continue
            sync_list.append(fresh)
        return sync_list
    def writeList(self, cmp_list):
        sync_list = os.path.join(APP_DIR, 'synclist.txt')
        with open(sync_list, 'w') as f:
            for l in cmp_list:
                f.writelines(l + "\n")
        return sync_list

    def process(self, rsyncobj, newlist=[]):
        '''
            here need another object:processor  to solve the real work and return an ok list
        '''
        newlist = self.compareDiff()
        filterlist = self.compareFilter(newlist)
        list_file = self.writeList(filterlist)

        with open(os.path.join(APP_DIR, "rsync_history.log"), 'a') as f:
            f.writelines("<Rsync Begin: " + str(datetime.datetime.today()) + ">\n")
            sent_ok = rsyncobj.syncList(list_file)
            f.writelines(self.remote_server + ":" + self.remote_module + ":" + self.backup_dir + ": " + str(len(sent_ok)) + " total.\n")
            f.writelines("<Rsync End: " + str(datetime.datetime.today()) + ">\n")    
            self.updatelocalDict(sent_ok)
               # call update

    def updatelocalDict(self, sent_list):
        '''
            update local dict file, for next using
        '''
        # update sent_list, delete those not in disk already(they have deleted)
        sync_index = self.dict['group'].index( (self.remote_server, self.remote_module, self.backup_dir) )
        
        for file in sent_list:
            if not self.dict['records'].get(file):
                self.dict['records'][file] = []
            for i in range(len(self.dict['records'][file]), sync_index +1):
                self.dict['records'][file].append(0)    #init with 0
            self.dict['records'][file][sync_index] = 1

        with open(os.path.join(DICT_DIR, self.remote_server + "_" + self.remote_module + ".dic"), 'wb') as w:
            pickle.dump(self.dict, w)


class RsyncProc:
    def __init__(self, remote, module, local_dir):
        self.remote_server = remote
        self.remote_module = module
        self.backup_dir = local_dir 

    def syncList(self, listfile):

        sync_cmd = "/usr/bin/rsync -avz --files-from=" + listfile + " " + self.remote_server + "::" + self.remote_module + " " + self.backup_dir
        sync_result = os.popen(sync_cmd)
        time.sleep(6)       # found when run os.popen after, some file not exist still. so wait a moment
        sent_ok = []
        for line in sync_result:
            line = line.strip()
            if len(line.split()) > 1 or line.endswith("/"):
                continue
            #if os.path.isfile(os.path.join(self.backup_dir, line)):
            sent_ok.append(line)
        return sent_ok


if __name__ == '__main__':
    addi = {}
    if len(sys.argv) > 5:
        addi['include'], addi['exclude'] = sys.argv[4:6]
    elif len(sys.argv) > 4:
        addi['include']= sys.argv[4]
    elif len(sys.argv) > 3 and os.path.isdir(sys.argv[3]):
        para = sys.argv[1:4]
    elif len(sys.argv) > 2:
        para = sys.argv[1:3]
    elif len(sys.argv) < 2:
        print("useage: python processFiles.py  remote_server  remote_module  local_dir")
        exit(1)

    backupman = ProcessBackup(*para, **addi)
    backupman.process(RsyncProc(backupman.remote_server, backupman.remote_module, backupman.backup_dir))
