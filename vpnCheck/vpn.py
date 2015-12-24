#!/usr/bin/python
# coding = utf-8
'''
    data: 2015-12-21
    desc: test vpn config
    pptpsetup return string:
    the first two line can be ignored:
        'Using interface ppp0\n', 
        'Connect: ppp0 <--> /dev/pts/5\n'
    the third line diff in success or fail result:
        when success: 
            'CHAP authentication succeeded\n'
        when fail(time out:)
            'LCP: timeout sending Config-Requests\n'
    last line :
        when success:
            'remote IP address 12.12.12.12\n'


    restore route:
        after success, first 'poff', 
                    then delete vpn route info ,
                    then delete vpn config
'''
##  python 3.5
import logging, argparse, csv
import os, socket, json
import pickle

def read_localcfg(filename):
    '''
        require a local ip.tables config file, with following:
        localip=101.251.217.14
        gatewayip=101.251.217.1

        when clear then route, they will be used.
    '''
    if os.path.isfile(filename):
        host = {}
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                items = line.split('=')
                if len(items) <=1:
                    continue
                host[items[0].strip()] = items[1].strip()
        return host

def read_vpncfg(filename):

    ## read csv format vpn list
    vpn_list = []
    try:
        with open(filename) as f:
            reader = csv.reader(f, delimiter=',', skipinitialspace=True)
            vpn_list = list(reader)
            return vpn_list
            #for row in reader:
            #    vpn_map[row[0]] = {}
            #    vpn_map[row[0]]['server'], vpn_map[row[0]]['user'], vpn_map[row[0]]['passwd'] = row[1:]
            #return vpn_map
    except Exception as e:
        print("read local " + filename + " error:" + str(e))
        exit(1)

def scan_config(hostcfg, ppp_name=None, log=None):
    ppp_config_dir = os.path.join("/etc/ppp")
    if not ppp_name:    # if not giving a ppp list, then scan all local config
        ppp_configs = os.listdir(os.path.join(ppp_config_dir, 'peers'))

    vpn_config = {}
    for f in ppp_configs:
        vpn_config[f] = {}
        abs_file = os.path.join(ppp_config_dir, 'peers', f)
        with open(abs_file, 'r') as fh:
            try:
                for line in fh:
                    line = line.strip()
                    items = line.split()
                    if items[0] == 'pty':
                        vpn_config[f]['server'] = items[2]
                        continue
                    if items[0] == 'name':
                        vpn_config[f]['user'] = items[1]
                        break

            except Exception as e:
                del vpn_config[f]
                if log:
                    log.warn("read ppp config error:" + f)
                continue
    if not vpn_config:
        log.warn("no ppp configures found.")
        exit(0)
    ## read secret file find match password
    with open(os.path.join(ppp_config_dir, 'chap-secrets'), 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#'):
                continue
            if line:
                items = line.split()
                if vpn_config.get(items[1]):
                    vpn_config[items[1]]['passwd'] = items[2].strip('"')
    
    ## turn hash into an list
    vpn_map = []
    for k in vpn_config.keys():
        row = []
        row.append(hostcfg['localip'])
        row.append(k)
        row.append(vpn_config[k]['server'])
        row.append(vpn_config[k]['user'])
        row.append(vpn_config[k]['passwd'])
        vpn_map.append(row)
    return vpn_map

def conn_vpn(name, vpn_row, log=None):
    if len(vpn_row) < 5:
        log.warn("vpn definition wrong:" + str(vpn_row))
        return None
    loc, name, server, user, passwd, ip = vpn_row

    conn_str = "/usr/sbin/pptpsetup --create " + name + " --server " + \
                    server + " --username " + user + " --password " + passwd + " --start"
    if log:
        log.info("exec:" + conn_str)

    ## connect to vpn, get returns
    os.system("/usr/sbin/pptpsetup --delete " + name)
    try:    
        rt_vpn = os.popen(conn_str).readlines()
        return rt_vpn
    except Exception as e:
        if log:
            log.error(e)
        return None

def clear_vpn(name, vpn_row, host, log=None):
    os.system("/usr/sbin/poff -a")
    os.system("/usr/sbin/pptpsetup --delete " + name)

def set_route(vpn):
    route = "ip route replace default dev ppp0"
    os.system(route)

def clear_route(vpn_ip, host):
    #re_route = "ip route del " + vpn_cfg['server'] + " via " + host['gateway'] + " dev " + host['eth'] + " src " + host['ip']
    re_route = "ip route del " + vpn_ip
    os.system(re_route)

    original = "ip route add default via " + host['gatewayip']
    os.system(original)

def send_email(mail_title, mail_body):
    mail_act = '/usr/local/bin/sendEmail -f jiance@adwo.com -t liujianbo@adwo.com  yangzhixin@adwo.com zuohaijun@adwo.com -s mail.adwo.com -u ' + \
                    '"' + mail_title + '"' + ' -m ' + '"' + mail_body + '"' + ' -xu jiance@adwo.com -xp adwo8888'
    os.system(mail_act)

if __name__ == '__main__':
    

    local_dir = os.path.dirname(os.path.abspath(__file__))
    ## log definition
    logging.basicConfig(level = logging.DEBUG,
                        format = '%(asctime)s [line:%(lineno)d] [%(levelname)s] %(message)s',
                        datefmt = '%Y-%m-%d %H:%M:%S',
                        filename = os.path.join(local_dir, 'vpn.log'),
                        filemode = 'a')

    
    if os.path.isfile(os.path.join(local_dir, 'ip.local')):
        hostcfg = read_localcfg(os.path.join(local_dir, 'ip.local'))
    else:
        print("not found ip file: ip.local\n")
        exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', action='store',  dest='vpn', nargs='+', default=[])     #
    parser.add_argument('-f', action='store', dest='vpn_cfg' )
    args = parser.parse_args()

    run_times = 1 
    vpn_ok = []
    if os.path.isfile(os.path.join(local_dir, 'vpn.dmp')):     # use dump first, then dump contain the err vpn list last running
        with open(os.path.join(local_dir, 'vpn.dmp'), 'rb') as d:      #dump is {} : 'count': run_times, 'suc':succ_list, 'err':err_list
            dmper = pickle.load(d)
            if 'err' in dmper.keys():
                vpn_ready = dmper['err']
            if 'suc' in dmper.keys():
                vpn_ok = dmper['suc']
            run_times = dmper['count']
    else:
    #vpn_map = []
        if args.vpn:     #parameter: use vpn profile name list
            vpn_ready = scan_config(hostcfg, vppp_name=args.vpn, log=logging)
        elif args.vpn_cfg:      #parameter: use local vpn list file
            vpn_file = os.path.join(local_dir, args.vpn_cfg)
            vpn_ready = read_vpncfg(vpn_file)
        else:   # no parameters, default is localhost vpn config
            vpn_ready = scan_config(logging)
 
    if not vpn_ready:
        logging.warn("Not found any vpn configs.")
        exit(1)

    err_list  = []
    succ_list = []      #connect success vpn list
    err_dmp  = []
    ## read the vpn_map, test every vpn server
    for row in vpn_ready:
        name = row[1]
        # row format: [ppp_name, server, user, passwd]
        ## ping vpnserver first
        try:
            serverip = socket.gethostbyname(row[2])
            row.append(serverip)      # add ip address to vpn_map for further using
        except socket.gaierror as e:
            logging.warn("unknown host: " + row[2] + "\n")
            errs = []
            errs.append(str(row))
            errs.append("unknown host")
            err_list.append(errs)
            continue

        ## connect to vpn server now
        results = conn_vpn('vpntest', row, logging)
        if not results:
            logging.error("vpn initial failed:" + name)
            continue
        
        if 'succ' in results[2]:
            vpn_ok.append(row[:-1])     #success vpn 
            logging.info("Success connected with:" + str(row))
            logging.info(str(results[2:]) + "\n")
            #succ_list.append(row)
        else:
            err_dmp.append(row[:-1])        #no need last value: vpn serverIP
            errs = []
            errs.append(str(row))
            errs.append(results[2])
            err_list.append(errs)
            
            logging.error("failed connect with:" + str(row))
            logging.error(str(results[2:]) + "\n")
        clear_vpn('vpntest', row, hostcfg, logging)
        clear_route(row[5], hostcfg)
    

    #all vpn test over. print result until now:
    print("Count: " + str(run_times) + "\n")
    print("sum connect success: " + str(len(vpn_ok)) + "\n")
    print("still connect fail: " + str(len(err_list)) + "\n")

    with open(os.path.join(local_dir, 'vpn.dmp'), 'wb') as d:
        dp = {}
        dp['count'] = run_times + 1
        dp['suc'] = vpn_ok
        dp['err'] = err_dmp
        pickle.dump(dp, d, True)

    if len(err_list) == 0:
        mail_title = "VPN Checking " + str(len(vpn_ok)) + " All Success (send from " + hostcfg['localip'] + ")"
        logging.info("send all success email.")
        send_email(mail_title, ' ')
        exit(0)

    if run_times == 10:
        if vpn_ok:
            mail_body = '' 
            for suc in vpn_ok:
                mail_body += ", ".join(suc) + "\n"
            mail_title = "VPN Checking " + str(len(vpn_ok)) + " Success (send from " + hostcfg['localip'] + ")"
            logging.info("send success list email")
            send_email(mail_title, mail_body)

        if err_list:
            mail_body = ''
            for err in err_list:
                mail_body += ", ".join(err) + "\n"
            mail_title = "VPN Checking " +  str(len(err_list)) + " Failure (send from " + hostcfg['localip'] + ")"
            logging.info("send fail list email")
            send_email(mail_title, mail_body)
