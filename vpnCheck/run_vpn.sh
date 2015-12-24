. /etc/profile
rm -f /data/vpn/testvpn/vpn.dmp
for ((i=1;i<=10;i++));
do
    /usr/local/python35/bin/python3 /data/vpn/testvpn/vpn.py -f v.lst
    sleep 15
done
