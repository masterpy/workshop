#!/bin/sh

_STOP_VPN=$1
_START_VPN=$2

vpn_alter_mails="liujianbo@adwo.com zuohaijun@adwo.com yangzhixin@adwo.com"
_NOT_ALTER_NUM=20


_VPN_RUN_DIR=`dirname $0`
. ${_VPN_RUN_DIR}/ip.local

_HISTORY_LOG="${_VPN_RUN_DIR}/ip.history.log"
_VPN_CONFIG_DIR="/etc/ppp/peers/"



vpn_name=$1

getvpnserverip(){
vpnserver=`grep "nolaunchpppd" /etc/ppp/peers/${vpn_name} | awk '{print $3}'`
vpnserverip=`dig +short ${vpnserver}`

}

add_vpn_route(){

ip route replace ${vpnserverip} via ${gatewayip} dev eth0 src ${localip} 
ip route replace default dev ppp0

}



del_vpn_route(){
 ip route  del ${vpnserverip} via ${gatewayip} dev eth0 src ${localip}
 ip route add default via ${gatewayip}
}




clean_failed(){
sed -i "/\<$1\>/d" ${_VPN_RUN_DIR}/failed.tmp
}



alter_failed(){
#${_VPN_RUN_DIR}/failed.tmp


_FIRST_LINE=(`grep $1 ${_VPN_RUN_DIR}/failed.tmp | head -1`)

_FIRST_T=${_FIRST_LINE[0]}
_NOW_T=`date +%s`
_D_T=$((_NOW_T-_FIRST_T))

#if failed great then N then send mail.
_FAILED_C=`grep $1 ${_VPN_RUN_DIR}/failed.tmp | wc -l | awk '{print $1}'`
if  [ "${_FAILED_C}" -gt ${_NOT_ALTER_NUM} ]
then

_VPN_CONFIG_NAME=`grep ^remotename ${_VPN_CONFIG_DIR}/$1 | awk '{print $2}'`
_VPN_USER=`grep ^name ${_VPN_CONFIG_DIR}/$1 | awk '{print $2}'`
_VPN_SERVER=`grep ^pty ${_VPN_CONFIG_DIR}/$1 | awk '{print $3}'`

##sendmail
/usr/local/bin/sendEmail -f jiance@adwo.com -t ${vpn_alter_mails}  -s mail.adwo.com -u "vpn:${_VPN_CONFIG_NAME} ${_FAILED_C} failed " -m " From:${localip1} \n server:${_VPN_SERVER} \n user:${_VPN_USER}"  -xu jiance@adwo.com -xp adwo8888 && clean_failed $1 && return 0
fi

if [ "${_D_T}" -gt 3600 ]
then
#clean failed count
clean_failed $1
fi

}






start_vpn(){
vpn_name=$1
getvpnserverip
VPN=`ip add |grep mtu | grep ppp0`
echo $VPN


if [ -z "$VPN" ]
then

	echo "`date +%F_%T` vpn connect starting..."  | tee -a ${_HISTORY_LOG}

	/usr/sbin/pon $1
	echo "`date +%F_%T` vpn connect return code:$?."

	on_num=0
	while true
	do
		echo "vpn:${_START_VPN} ${on_num} `ip add | grep  ppp0 | grep inet`"  | tee -a ${_HISTORY_LOG}
		ip add | grep  ppp0 | grep inet && break
		sleep 0.5
		if [ ${on_num} -gt 30 ]
			then
				return 1
		fi


		on_num=$((on_num+1))
	done
	#sleep 5 
 is_link=`ip add | grep mtu | grep -c ppp0`
 if [ ${is_link} -eq 1 ]
  then
	echo "`date +%F_%T` route replace starting..."
	add_vpn_route
	echo "`date +%F_%T` route replace end."
 fi
 
else
	echo "ERROR:A $VPN has already started." | tee -a ${_HISTORY_LOG}
	return 1
fi
}





stop_vpn(){

vpn_name=$1
getvpnserverip

_STOP_STAT=0
echo "`date +%F_%T` vpn stoping..."  | tee -a ${_HISTORY_LOG}
is_link=`ip add | grep mtu | grep -c ppp0`
if [ ${is_link} -eq 1 ]
then

        #/usr/sbin/poff $1
        /usr/sbin/poff
        echo "`date +%F_%T` vpn connect stop return code:$?."
        #sleep 5
        off_num=0
        while true
        do

        ip add  | grep ppp0 | grep inet || break
        sleep 0.5
        if [ ${off_num} -gt 20 ]
	then
		_STOP_STAT=1	
		break
	else
        	off_num=$((off_num+1))
	fi
        done
 
echo "`date +%F_%T` restoring route..."
fi
 del_vpn_route
echo "`date +%F_%T` vpn stoped."


return ${_STOP_STAT}
}


get_wan_ip(){

wan_ip_loop=0

sleep 0.5
while [ ${wan_ip_loop} -lt 1 ]
do
	echo "vpn:${_START_VPN} `date +%F_%T` Get vpn_wan_ip ..." | tee -a ${_HISTORY_LOG}
	vpn_wan_ip=`curl -s -m 10 http://ad-bg.adwo.com/admin_v/api/ip.jsp`
	[ -z "${vpn_wan_ip}" ] && vpn_wan_ip=`curl -s -m 10  www.ip.cn | awk -F "：" '{print $2}' | awk -F " " '{print $1}' | grep -E "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}"`
        [ -z "${vpn_wan_ip}" ] && vpn_wan_ip=`curl -s -m 10 ifconfig.me`

	if [ -z "${vpn_wan_ip}" ]
	then
		wan_ip_loop=$((wan_ip_loop+1))
		vpn_wan_ip=1
		sleep 1
	else
		break
	fi
done
}






####stop first
stop_vpn ${_STOP_VPN}


sleep 2

[ -z "${_START_VPN}" ] && exit


if [ -e ${_VPN_RUN_DIR}/failed.tmp ]
then
	alter_failed	${_START_VPN} &
fi

start_loop=1
while [ ${start_loop} -le 2 ]
do
if start_vpn ${_START_VPN}
then
	sleep 1
	get_wan_ip
        echo -e "${vpn_wan_ip}     \t\t${_START_VPN} \t`date +%F_%T`" | tee ${_VPN_RUN_DIR}/ip.txt | tee -a ${_VPN_RUN_DIR}/ip.history.log
	break
else
	stop_vpn ${_START_VPN}
	vpn_wan_ip=1
        echo -e "${vpn_wan_ip}     \t\t${_START_VPN} \t`date +%F_%T`" | tee ${_VPN_RUN_DIR}/ip.txt | tee -a ${_VPN_RUN_DIR}/ip.history.log
	echo -e "`date +%s` \t${_START_VPN} failed" | tee -a ${_VPN_RUN_DIR}/failed.tmp

fi


start_loop=$((start_loop+1))
done






