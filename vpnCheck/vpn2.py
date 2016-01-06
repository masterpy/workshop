class VpnClient:
    '''
        date: 2016-01-06
    '''

    def __init__(self, name):
        self.name = name
        pass
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
        return (server, user, passwd)


    def connVpn(self,*vpn):
        server, user, passwd = vpn
        conn_str = "/usr/sbin/pptpsetup --create " + self.name + " --server " + \
                        server + " --username " + user + " --password " + passwd +" --start"
        err = Exception()
        try:
            vpn_conn = os.popen(conn_str).readlines()
            return vpn_conn
        except Exception as e:
            return err


    def addVpnRoute(self, *routes):
        vpnserverip, gatewayip, localip = routes
        route_str1 = "ip route replace " + vpnserverip + " via " + gatewapip + " dev eth0 src " +localip
        route_str2 = "ip route replace default dev ppp0"
        op.system(route_str1)
        op.system(route_str2)

    
    def stopVpn(self):
        rt = os.popen("poff").readlines()
        return rt
    def chkVpnoff(self, vpn):
        for num in range(20):
            isdead = os.system("pppstats")
            if isdead:  #pptp is off
                return isdead
        return 0

        pass
    def clearRoute(self, *route):
        vpnserverip,gatewayip = route[:2]
        os.system("ip route del " + vpnserverip)
        os.system("ip route add default via " + gatewayip)

    
