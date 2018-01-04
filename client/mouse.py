#-*- encoding: utf-8 -*-
import sys
import os
import platform
import trafficfilter
import iptablesfilter
import proxy
import config
import time
import subprocess

def kill_before(port):
    str = "lsof -i:%s | awk '{if (NR>1){print $2}}' | xargs kill -9" % port
    subprocess.call([str], shell=True)

def main():
    openStat = 0
    sysstr = platform.system()
    if (sysstr == "Windows"):
        #print("Call Windows tasks")
        sys.exit(0)
    elif (sysstr == "Linux"):
        #print("Call Linux tasks")
        openStat =1
    else:
        #print("Other System tasks")
        sys.exit(0)

    if openStat == 1:
        cg=config.config()
        kill_before(cg.forwardport)
        proxyser = proxy.tcpproxy(cg.forwardport, cg.dhost, cg.dport, cg.user)
        # proxy.start_server()
        proxyser.start_proxy()
        time.sleep(3)


        #TODO
        #proxyser._connect('49368', '', '', False)


        ipfilter = iptablesfilter.iptablesfilter()
        ipfilter.startTcpforward()
        traffic = trafficfilter.Traffic('', 'tcp', proxyser)
        traffic.setfind('\"jsonrpc\":\"2.0\",\"method\":\"keepalived\"')
        traffic.TrafficProcess()


if __name__ == "__main__":
    main()
