#-*- encoding: utf-8 -*-
import sys
import os
import platform
import trafficfilter
import iptablesfilter
def main():
    openStat = 0
    sysstr = platform.system()
    if (sysstr == "Windows"):
        print("Call Windows tasks")
    elif (sysstr == "Linux"):
        print("Call Linux tasks")
        openStat =1
    else:
        print("Other System tasks")

    if openStat == 1:
        iptablesfilter.startTcpforward()
        traffic = trafficfilter.Traffic('', 'tcp')
        traffic.setfind('\"id\":1,\"jsonrpc\":\"2.0\"')
        traffic.getTraffic()


if __name__ == "__main__":
    main()
