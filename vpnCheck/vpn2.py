import os, re
import logging
class VpnClient:
    '''
        date: 2016-01-06
        author: Jianblog
        note: an vpn connect tools
    '''

    def __init__(self, vpnname):
        self.name = vpnname
        vpnaccount = self.getVpnbyName()
        if vpnaccount:
            self._vpnserver, self._vpnuser, self._vpnpasswd = vpnaccount
        else:
            exit(1)
        # init an log
        self.local_dir = os.path.dirname(os.path.abspath(__file__))

    def getLocalgw(self, localfile):
        dic_local = {}
        with open(localfile) as f:
            for line in f:
                line = line.strip()
                items = line.split("=")
                dic_local[items[0]] = items[1]
        return dic_local

    def getVpnbyName(self):
        '''
            note:after config vpn on server, the vpn account was saved in files,
            and we can run shell 'pon alias_name' to startup a vpn connection.
            so this function is to get the full info(server, user, password) by a configured alias_name

        '''
        peers_file = os.path.join("/etc/ppp/peers", self.name)
        server, user, passwd = ('', '', '')
        try:
            with open(peers_file, 'r') as peer:
                for line in peer:
                    if line.startswith('pty'):
                        server = line.split()[2]
                    if line.startswith('name'):
                        user = line.split()[1]
                        break
            with open("/etc/ppp/chap-secrets", 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        passwd = line.split()[2].strip('"')
                        break
        except Exception as e:
            print("error read ppp config file:" + str(e))
            exit(1)
        if server and user and passwd:
            return (server, user, passwd)
        else:
            return None


    def startVpn(self):
        conn_str = "/usr/sbin/pptpsetup --create " + self.name + " --server " + \
                        self._vpnserver + " --username " + self._vpnuser + " --password " + self._vpnpasswd +" --start"
        err = Exception()
        try:
            vpn_conn = os.popen(conn_str).readlines()
            for line in vpn_conn:
                if self.searchip(line):
                    return (True, vpn_conn)
                else:
                    return (False, vpn_conn)
        except Exception as e:
            return (False, str(e))


    def addVpnRoute(self, *routes):
        vpnserverip, gatewayip, localip = routes
        route_str1 = "ip route replace " + vpnserverip + " via " + gatewapip + " dev eth0 src " +localip
        route_str2 = "ip route replace default dev ppp0"
        op.system(route_str1)
        op.system(route_str2)

    
    def stopVpn(self):
        rt = os.popen("poff").readlines()
        for num in range(20):
            isdead = os.system("pppstats")
            if isdead:  #pptp is off return code 1
                return isdead
        return None

        pass 
    def clearRoute(self, *route):
        vpnserverip,gatewayip = route[:2]
        os.system("ip route del " + vpnserverip)
        os.system("ip route add default via " + gatewayip)

    def getWanip(self):
        ## try twice with different api
        
        method1 = os.popen("curl -s -m 10 http://ad-bg.adwo.com/admin_v/api/ip.jsp").read()
        hasip = self.searchip(method1):
        if hasip:
            return hasip
        method2 = os.popen("curl -s -m 10 http://www.ip.cn").read()
        hasip = self.searchip(method2)
        if hasip:
            return hasip
        return None

    def searchip(self, strings):
        pattern_ip = re.compile("\d+\.\d+\.\d+\.\d+")
        match = re.search(pattern_ip, strings)
        if match:
            return match.group()
        else:
            return None

if __name__ == '__main__':
    if len(sys.argv) >= 1:
        _stop_vpn, _start_vpn = sys.argv[:1]
    else:
        print("useage: app  stop_vpn  start_vpn")

    localdic = vpnStoper.getLocalgw(os.path.join(localdir, 'ip.local'))
    vpnStoper = VpnClient(_stop_vpn)
    stopvpnip = socket.gethostbyname(vpnStoper._vpnserver)

    if vpnStoper.stopVpn():        
        vpnStoper.clearRoute(localdic['gatewayip'], stopvpnip)
    else:
        print("vpn still alive")
        exit(1)
    del vpnStoper

    vpnStarter = VpnClient(_start_vpn)
    startvpnip = socket.gethostbyname(vpnStarter._vpnserver)
    rt, info = vpnStarter.startVpn()
    if rt:
        print("connect ok")
        vpnStarter.addVpnRoute(startvpnip, localdic['gatewayip'], localdic['localip'])
        ownip = vpnStarter.getWanip()
        if ownip:
            print("get vpn ip")
    else:
        print("connect fail")



