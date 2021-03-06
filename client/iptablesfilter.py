#-*- encoding: utf-8 -*-
import sys
import os
import subprocess
import config
import time
class iptablesfilter(object):
    def __init__(self,eth='eth0',oldip='',oldp = ''):
        self.stat = 'down'
        self.myruleList = []
        cg = config.config()
        self.rule=''
        #iptables -t    nat -A OUTPUT --destination remote.host.ip -p tcp --dport 22 -j DNAT --to-destination remote.host.ip: 222
        #iptables -t     nat -A PREROUTING --destination remote.host.ip -p tcp  --dport 22 -j DNAT --to-destination remote.host.ip:222
        if oldip != '' and oldp != '':
            self.rule = '-t    nat -A OUTPUT --destination %s -p tcp --dport %s -j DNAT --to-destination %s:%s' %(oldip,oldp,cg.forwardip,cg.forwardport)
        else:
            self.rule = ''

    @staticmethod
    def startTcpforward():
        #print('startTcpforward echo 1> ip_forward\n')
        subprocess.call(['echo 1 > /proc/sys/net/ipv4/ip_forward'], shell=True)
        subprocess.call(['service iptables start'], shell=True)
        time.sleep(2)
        subprocess.call(['iptables -t nat -F'], shell=True)


    def setIptables(self):
        #print('in setIptables\n')
        if self.rule!= "":
            self.myruleList.append(self.rule)
            #print self.rule
            ipstr = 'iptables %s' %self.rule
            subprocess.call([ipstr], shell = True)
            subprocess.call(['service iptables save'], shell = True)

    def cleanIptables(self):
        #print('in cleanIptables\n')
        for rule in self.myruleList:
            #替换-A -I
            rule << 2
            rule = '-D' + rule
            self.setIptables(rule)

    def getMyiptable(self):
        return self.myruleList
