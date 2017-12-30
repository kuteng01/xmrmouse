#-*- encoding: utf-8 -*-
import pcap
import dpkt
import threading
import iptablesfilter
from threading import Timer
import time

class config(object):
    forwardip = '127.0.0.1'
    forwardport= '17998'

    default_xmr_host=''
    default_xmr_port=''
    def __init__(self):
        self.name = 'leon'
