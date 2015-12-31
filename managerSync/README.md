
rsync manage tools：
  date: 2015-12-31
  author: jianblog@live.com
  
  begin:rsync is a sync files between two sides, if target host changed those files transfered before, the original files will transfer again.

environment：
  1. we have one middle host run rsync to sync logs from many front hosts; 
  2. need to transfer logs from middle to back host for storage permanent;
  3. so deploy this on middle host, it do these things:
    a. scan target directory and compare with last send by rsync list, filter whom did not send
    b. call rsync to transfer these files, update local send ok list, save some infos in to target directory
  4. so we can compress or other action to files in back host, rsync only transfer files we defined, not full logs
  5. next i will deploy jobs on front hosts and middle host to delete very old logs files
  
  the local dict saved file struct( still in plan):
    ​dict = { source_dir = '', 
              (target_ip, target_name) :  #may one source sync to many target
                                          { 'send_history': (),  
                                            'last_time' : '',
                                            'enable': True,
                                          }
