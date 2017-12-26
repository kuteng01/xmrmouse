#-*- encoding: utf-8 -*-
import pcap
import dpkt
import threading
import iptables
from threading import Timer
import time

class Traffic(object):
    def __init__(self,eth='eth0',filter=''):
        self.eth = eth
        self.filter = filter
        self.cap = pcap.pcap(self.eth)
        self.cap.setfilter(self.filter)
        self.timer = 600 #10min
        self.ticketCnt = 10 #1hour
        self.files4out = {}

    def setfind(self,content):
        self.findContent = content

    def getTraffic(self):
        #item = [src_tag, sp_tag, dst_tag, dp_tag, self.ticketCnt, iptablesObj]
        for ptime, pktdata in self.cap:
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
            FLAG = 0



            FLAG = 1
            src_tag = sip
            dst_tag = dip
            sp_tag = str(sport)
            dp_tag = str(dport)
            if ord(list(ipdata.src)[0]) > ord(list(ipdata.dst)[0]):
                temp = dst_tag
                dst_tag = src_tag
                src_tag = temp

            if sport > dport:
                temp = sp_tag
                sp_tag = dp_tag
                dp_tag = temp

            name = src_tag + '_' + sp_tag + '_' + dst_tag + '_' + dp_tag
            if (name) in self.files4out:
                 item = self.files4out[name]
                 item[4] = self.timer
            else:
                appdata = tcpdata.data
                if appdata.find(content) == -1:
                    break;
                iptablesObj = iptables()
                item = [src_tag, sp_tag, dst_tag, dp_tag, self.ticketCnt , iptablesObj]
                self.files4out[name] = item


    def timerProcess(self):
        #args是关键字参数，需要加上名字，写成args=(self,)
        for name in self.files4out:
            item  = self.files4out[name]
            item[4] -= 1
            if(item[4] <= 0):
                item[5].cleanIptables()
                del self.files4out[name]

    def TrafficProcess(self):
        #args是关键字参数，需要加上名字，写成args=(self,)
        th1 = threading.Thread(target=Traffic.getTraffic, args=(self,))
        th1.start()
        th1.join()

    def TrafficTimer(self):
        t = Timer(self.timer, self.timerProcess())
        t.start()


def main():
     traffic = Traffic('eth0','tcp')
     traffic.setfind('\"id\":1,\"jsonrpc\":\"2.0\"')
     traffic.getTraffic()


if __name__=="__main__":
    main()


