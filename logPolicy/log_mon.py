#!env python
# conding = utf-8

'''
    date: 2015-12-23
    author: jianblog
    note:   policy is an rules for log retain period,  
            every type log match a different policy.
            when app runs, it decide what to do according the policy definition
    
            policy{'gz': 30, 'retain': 90}  means: after 30 days, gzip it, after 90 days delete it.
'''
import os, time, datetime, re
import logging

class LogPolicy():
    '''
        log manage policy
    '''
    def __init__(self, policy):
        self.policy = policy

    def matchPolicy(self, file, pattern):
        '''
            decide the file matched by re.pattern in which kind of policy rules
            return a dict, the k:True mean act with the rule
        '''
        basename = os.path.basename(file)
        string_date = pattern.search(basename)
        if string_date:     #by filename pattern
            year,mon,day = string_date.groups()
            file_date = datetime.date(int(year), int(mon), int(day))
        else:               # by file last access time 
            file_date = datetime.date.fromtimestamp(os.path.getmtime(file))
        diff = datetime.date.today() - file_date
        match = {}
        for k,v in self.policy.items():
            if v == -1:     # unlimited
                continue
            if diff.days > v:
                match[k] = True
        return match

if __name__ == '__main__':
    log_policy = { 'short_p': {'gz': 7, 'retain': 7},
                   'normal_p': {'gz': 7, 'retain': 30},
                   'middle_p': {'gz': 7, 'retain': 60},
                   'long_p': { 'gz': 7, 'retain': 90}
                    }
    log_group = [['/data/tomcatapp/apache-tomcat-7.0.57/logs', log_policy['long_p']],
                 ['/data/tomcatapp/apache-tomcat-7.0.57/temp', log_policy['short_p']],
                 ['/data/vlogs/ios/exception', log_policy['normal_p']],
                 ['/data/vlogs/ios/show', log_policy['long_p']],
                 ['/data/vlogs/android/show', log_policy['long_p']],
                 ['/data/vlogs/android/fsshow', log_policy['long_p']],
                 ['/data/vlogs/send_url', log_policy['middle_p']],
                 ['/data/vlogs/send_exception', log_policy['long_p']]
                ]

    local_dir = os.path.dirname(os.path.abspath(__file__))            
    logging.basicConfig(level = logging.DEBUG,
                        format = '%(asctime)s [line:%(lineno)d] [%(levelname)s] %(message)s',
                        datefmt = '%Y-%m-%d %H:%M:%S',
                        filename = os.path.join(local_dir, 'vpn.log'),
                        filemode = 'a')
    _OUT = False

    ## log file datetime pattern, use it to get the file create date
    patt = re.compile(r'(\d{4})-(\d{2})-(\d{2})')
    for log_loc, policy in log_group:
        if os.path.isdir(log_loc):
            manager = LogPolicy(policy)
            for log in os.listdir(log_loc):
                logfile = os.path.join(log_loc, log)
                file_rules = manager.matchPolicy(logfile, patt)

                if file_rules.get('retain'):
                    if _OUT:
                        logging.info("read to delete: " + logfile)
                    os.unlink(logfile)
                    continue
                if file_rules.get('gz'):
                    if not logfile.endswith('gz'):
                        if _OUT:
                            logging.info("read to gzip: " + logfile)
                        os.system("/bin/gzip " + logfile)

