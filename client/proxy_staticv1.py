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
    def __init__(self, sport):
        self.serverport = sport
        self.defaultremoteip = '127.0.0.1'
        self.defaultremoteport='22'
        self.servlist={}
        self.remotelist={}
        self.wait_time = 36
        self.try_cnt = 5
        self.serverqueue = Queue.Queue()
        self.clientqueue = Queue.Queue()
        self.clientmutex = threading.Lock()
        self.servermutex = threading.Lock()



    def clean_proxy_chain(self, item):
        try:
            if item != None:
                outflow=self.remotelist[item]
                if outflow != None:
                    try:
                        outflow[1].shutdown(socket.SHUT_RDWR)
                        outflow[1].close()
                        self.remotelist.pop(item)
                    except:
                        print "clean_proxy_chain clean remote list failed"

                try:
                    localflow = self.servlist[item]
                    localflow[0].shutdown(socket.SHUT_RDWR)
                    localflow[0].close()
                    self.servlist.pop(item)
                except Exception as e:
                    print "clean_proxy_chain clean server list failed:", repr(e)
        except   Exception as e:
            print "clean_proxy_chain clean item  failed.:", repr(e)


    def clean_outstream(self, item):
        try:
            if item != None:
                outflow=self.remotelist[item]
                if outflow != None:
                    try:
                        outflow[1].shutdown(socket.SHUT_RDWR)
                        outflow[1].close()
                        self.remotelist.pop(item)
                    except Exception as e:
                        print "clean_outstream clean remote list failed:", repr(e)
        except  Exception as e:
            print 'clean_outstream clean item  failed.:', repr(e)



    def localoutstream(self):
        '''
        交换内向外两个流的数据
        '''
        print "into localoutstream"
        #epoll_instance=epoll()
        #epoll_instance.register(s.fileno(), EPOLLIN | EPOLLET)
        while True:
            dellist =[]
            print "in localoutstream"
            #item = ['ip','port']

            while not self.serverqueue.empty():
                item = self.serverqueue.get()
                key = item.keys()
                value = item.values()
                print("localoutstream key:%s -> value:%s" % (key[0], value[0]))
                self.servlist[key[0]] = value[0]

            if len(self.servlist) <= 0:
                time.sleep(3)
                continue
            for item in self.servlist:
                try:
                    conn = self.servlist[item]

                    print("read from local:%s item:%s" %(conn[1],item))
                    #注意，recv函数会阻塞，直到对端完全关闭（close后还需要一定时间才能关闭，最快关闭方法是shutdow）
                    buff = conn[0].recv(1024)
                    if len(buff) == 0: #对端关闭连接，读不到数据
                        print "localoutstream one closed"
                        #dellist.append(item)
                        #self.clean_proxy_chain(item)
                        continue

                    print "c>s:"
                    hexdump(buff)

                    #if self.clientmutex.acquire(1):
                    #remotelistcopy = copy.deepcopy(self.remotelist)
                    print("remotelist:%s" % (self.remotelist))


                    if self.remotelist.has_key(item):
                        print "c send to s"
                        outflow = self.remotelist[item]
                        outflow[1].sendall(buff)
                    else:
                        print "new c send to s"
                        newoutflow = self._connect(item,'','',True)
                        newoutflow[item][1].sendall(buff)
                        #self.clientmutex.release()
                except  Exception as e:
                    print 'localoutstream except:',repr(e)
                    print "localoutstream one connect closed."
            #time.sleep(1)

            for conn in dellist:
                self.clean_proxy_chain(conn)

    def remoteinstream(self):
        '''
        交换外向内两个流的数据
        '''
        print "into remoteinstream"

        while True:
            #item = ['ip','port']
            print "in remoteinstream"
            dellist=[]
            while not self.clientqueue.empty():
                item = self.clientqueue.get()
                key = item.keys()
                value = item.values()
                print("remoteinstream key:%s -> value:%s" % (key[0], value[0]))
                self.remotelist[key[0]] = value[0]

            if len(self.remotelist) <= 0:
                time.sleep(3)
                continue
            for conn in self.remotelist:
                try:
                    print("read from server:%s:%s item:%s" %(self.remotelist[conn][2], self.remotelist[conn][3], conn))
                    #注意，recv函数会阻塞，直到对端完全关闭（close后还需要一定时间才能关闭，最快关闭方法是shutdow）
                    buff = self.remotelist[conn][1].recv(1024)

                    if len(buff) == 0: #对端关闭连接，读不到数据
                        print "remoteinstream one closed"
                        #dellist.append(conn)
                        #self.clean_outstream(conn)
                        continue

                    print "s>c:"
                    hexdump(buff)

                    #if self.servermutex.acquire(1):

                    #servlistcopy = copy.deepcopy(self.servlist)
                    print("servlist:%s" % (self.servlist))

                    if self.servlist.has_key(conn):
                        print "s send to c"
                        outflow=self.servlist[conn]
                        print("outflow[0]:%s" % outflow[0])
                        outflow[0].sendall(buff)
                    else:
                        print "server clean"
                        #dellist.append(conn)
                        #self.clean_outstream(conn)
                        continue
                        #self.servermutex.release()
                except Exception as e:
                    print 'remoteinstream except:', repr(e)
                    print "remoteinstream one connect closed."

            for conn in dellist:
                self.clean_outstream(conn)

            #time.sleep(1)



    def _server(self):
        '''
        处理服务情况,num为流编号（第0号还是第1号）
        '''
        print "into _server"
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('0.0.0.0', int(self.serverport)))
        srv.listen(1)
        while True:
            conn, addr = srv.accept()
            #设置非阻塞
            conn.setblocking(0)
            print "connected from:", addr
            print "client port:",addr[1]

            #客户端加入队列
            item = {addr[1]:[conn, addr]}
            #以本地发起连接端口为主键
            #对应servlist
            self.serverqueue.put(item)
            #self.servlist[addr[1]] = item
            print "in server"


    def _connect(self, lport, host, port, default):
        '''	处理连接，num为流编号（第0号还是第1号）

        @note: 如果连接不到远程，会sleep 36s，最多尝试200(即两小时)
        '''
        print "into _connect"
        if default == True:
            host = self.defaultremoteip
            port = int(self.defaultremoteport)
            print("default remote:%s:%s" % (host,port))

        not_connet_time = 0
        while True:
            if not_connet_time > self.try_cnt:
                print('cant not connected')
                return None

            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                conn.connect((host, port))
                conn.setblocking(0)
                print('connect remote%s:%s!' % (host, port))
            except Exception as e:
                print('can not connect %s:%s!' % (host, port))
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
        print "into start_proxy"
        tlist=[]  # 线程列表，最终存放两个线程对象
        t=threading.Thread(target=self._server, args=())
        tlist.append(t)
        out=threading.Thread(target=self.localoutstream, args=())
        tlist.append(out)
        #out.join()

        remotein=threading.Thread(target=self.remoteinstream, args=())
        tlist.append(remotein)

        for t in tlist:
            #print "start thread"
            t.start()
        #for t in tlist:
            #print "join thread"
            #t.join()
        #remotein.join()

    def connect_xmr(self, lport, host, port):
        ret = self._connect(lport, host, port,True)


def test():
    proxy = tcpproxy('9000')
    #proxy.start_server()
    proxy.start_proxy()
    time.sleep(3)
    proxy.connect_xmr('49368','','')

if __name__ == "__main__":
    test()
    sys.exit(0)