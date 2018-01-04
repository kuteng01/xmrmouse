#-*- encoding: utf-8 -*-
import pcap
import dpkt
import threading
import iptablesfilter
from threading import Timer
import time
import proxy
import config
import socket
import os
import subprocess

def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
        ip = None
    return ip

def kill_other(port):
    pid = os.getpid()
    str = "lsof -i:%s | awk '{if (NR>1 && $2 != %s){print $2}}' | xargs kill -9" %(port, pid)
    subprocess.call([str], shell=True)

class Traffic(object):
    def __init__(self,eth='',filter='',proxy=None):
        #print "into init_traffic",eth,filter
        self.eth = "eth1"
        self.filter = filter
        self.cap = pcap.pcap(self.eth)
        self.cap.setfilter(self.filter)
        self.timerout = 600 #10min
        self.ticketCnt = 10 #1hour
        self.files4out = {}
        self.timer = None
        self.iptablelist=[]
        self.proxy = proxy

    def setfind(self,content):
        #print('into setfind\n')
        self.findContent = content

    def getTraffic(self):
        #print ('into getTraffic\n')
        #self.TrafficTimer()
        #item = [src_tag, sp_tag, dst_tag, dp_tag, self.ticketCnt, iptablesObj]
        for ptime, pktdata in self.cap:
            #print "for\n"
            pkt = dpkt.ethernet.Ethernet(pktdata)
            if pkt.data.data.__class__.__name__ <> 'TCP':
                continue
            ipsrc_tag = 0
            ipdst_tag = 0
            sport_tag = 0
            dport_tag = 0

            ipdata = pkt.data
            sip = '%d.%d.%d.%d' % tuple(map(ord, list(ipdata.src)))
            dip = '%d.%d.%d.%d' % tuple(map(ord, list(ipdata.dst)))

            tcpdata = pkt.data.data
            sport = tcpdata.sport
            dport = tcpdata.dport

            content = self.findContent

            src_tag = sip
            dst_tag = dip
            sp_tag = str(sport)
            dp_tag = str(dport)
            #if ord(list(ipdata.src)[0]) > ord(list(ipdata.dst)[0]):
                #temp = dst_tag
                #dst_tag = src_tag
                #src_tag = temp
            dowell = 0
            ip = get_host_ip()
            if ip != None:
                if src_tag != ip:
                    temp=dst_tag
                    dst_tag=src_tag
                    src_tag=temp

                    temp=sp_tag
                    sp_tag=dp_tag
                    dp_tag=temp
                dowell = 1
            if dowell != 1:
                if sport < dport:
                    temp = dst_tag
                    dst_tag = src_tag
                    src_tag = temp

                    temp = sp_tag
                    sp_tag = dp_tag
                    dp_tag = temp

            #name = src_tag + '_' + sp_tag + '_' + dst_tag + '_' + dp_tag
            name=dst_tag + '_' + dp_tag

            cg=config.config()
            if dst_tag in cg.ip_list and dp_tag == cg.dport:
                continue
            #print("%s\n" %name)
            if (name) in self.files4out:
                 item = self.files4out[name]
                 item[4] = self.timerout
                 #print(name,item)
            else:
                appdata = tcpdata.data
                if appdata.find(content) == -1:
                    continue
                #print('new item')

                self.proxy._connect(sp_tag, dst_tag, dp_tag, True)
                iptablesObj = iptablesfilter.iptablesfilter('',dst_tag,dp_tag)
                iptablesObj.setIptables()
                item = [src_tag, sp_tag, dst_tag, dp_tag, self.ticketCnt , iptablesObj]
                self.files4out[name] = item

                kill_other(sp_tag)
    def timerProcess(self):
        #print "into timerProcess"
        while True:
            #args是关键字参数，需要加上名字，写成args=(self,)
            for name in self.files4out:
                item  = self.files4out[name]
                item[4] -= 1
                if(item[4] <= 0):
                    item[5].cleanIptables()
                    del self.files4out[name]
            time.sleep(self.timerout)
            #self.timer = Timer(self.timerout, self.timerProcess())
            #self.timer.start()

    def TrafficProcess(self):
        #print('into TrafficProcess\n')
        #args是关键字参数，需要加上名字，写成args=(self,)
        th1 = threading.Thread(target=self.getTraffic(), args=(self,))
        th1.start()
        #th1.join()

    def TrafficTimer(self):
        #print('into TrafficTimer\n')
            #self.timer = Timer(self.timerout, self.timerProcess())
            #self.timer.start()
        timer = threading.Thread(target=self.timerProcess(),args=(self,))
        timer.start()
        timer.join()



