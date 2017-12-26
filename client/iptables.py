#-*- encoding: utf-8 -*-
import sys
import os
import subprocess
import config
class iptables(object):
    def __init__(self,eth='eth0',oldip='',oldp = ''):
        self.stat = 'down'
        self.myruleList = []
        #iptables -t    nat -A OUTPUT --destination remote.host.ip -p tcp --dport 22 -j DNAT --to-destination remote.host.ip: 222
        #iptables -t     nat -A PREROUTING --destination remote.host.ip -p tcp  --dport 22 -j DNAT --to-destination remote.host.ip:222
        if oldip != '' and oldp != '':
            self.rule = '-t    nat -A OUTPUT --destination %s -p tcp --dport %s -j DNAT --to-destination %s: %s',eth,oldip,oldp,config.forwardip,config.forwardport
        else:
            self.rule = ''

    @staticmethod
    def startTcpforward():
        subprocess.call(['echo 1 > /proc/sys/net/ipv4/ip_forward'], shell=True)


    def setIptables(self):
        if self.rule!= "":
            self.myruleList.append(self.rule)
            subprocess.call(['iptables  %s' %self.rule], shell = True)
            subprocess.call(['service iptables save'], shell = True)

    def cleanIptables(self):
        for rule in self.myruleList:
            #替换-A -I
            rule << 2
            rule = '-D' + rule
            self.setIptables(rule)

    def getMyiptable(self):
        return self.myruleList
