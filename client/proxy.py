#-*- encoding: utf-8 -*-
#!/usr/bin/env python
# coding=utf-8

'''
filename:proxy.py
'''

import socket
import sys
import threading
import time

class tcpproxy(object):
    def __init__(self, sport):
        self.serverport = sport
        self.defaultremoteip = '103.91.217.5'
        self.defaultremoteport='80'
        self.servlist={}
        self.remotelist={}
        self.wait_time = 36
        self.try_cnt = 5



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
                        print "clean remote list failed"

                try:
                    item.shutdown(socket.SHUT_RDWR)
                    item.close()
                    self.servlist.remove(item)
                except:
                    print "clean server list failed"
        except :
            print "clean item  failed."


    def clean_outstream(self, item):
        try:
            if item != None:
                outflow=self.remotelist[item]
                if outflow != None:
                    try:
                        outflow[1].shutdown(socket.SHUT_RDWR)
                        outflow[1].close()
                        self.remotelist.pop(item)
                    except:
                        print "clean remote list failed"
        except :
            print "clean item  failed."



    def localoutstream(self):
        '''
        交换内向外两个流的数据
        '''
        try:
            while True:
                #item = ['ip','port']
                for item in self.servlist:
                    conn = self.servlist[item]
                    #注意，recv函数会阻塞，直到对端完全关闭（close后还需要一定时间才能关闭，最快关闭方法是shutdow）
                    buff = conn[0].recv(1024)
                    if len(buff) == 0: #对端关闭连接，读不到数据
                        print "one closed"
                        self.clean_proxy_chain(item)
                        continue

                    outflow = self.remotelist[item]
                    if outflow != None:
                        outflow[1].sendall(buff)
                        print "c>s:",buff
                    else:
                        newoutflow = self._connect(item,'','',True)
                        newoutflow[1].sendall(buff)
                        print "c>s:", buff

        except :
            print "one connect closed."



    def remoteinstream(self):
        '''
        交换外向内两个流的数据
        '''
        try:
            while True:
                #item = ['ip','port']
                for conn in self.remotelist:
                    #注意，recv函数会阻塞，直到对端完全关闭（close后还需要一定时间才能关闭，最快关闭方法是shutdow）
                    buff = self.remotelist[conn][1].recv(1024)
                    if len(buff) == 0: #对端关闭连接，读不到数据
                        print "one closed"
                        self.clean_outstream(conn)
                        continue


                    outflow = self.servlist[conn]
                    if outflow != None:
                        outflow[1].sendall(buff)
                        print "s>c:", buff
                    else:
                        self.clean_outstream(conn)
                        continue

        except :
            print "one connect closed."

    def _server(self):
        '''
        处理服务情况,num为流编号（第0号还是第1号）
        '''
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('0.0.0.0', int(self.serverport)))
        srv.listen(1)
        while True:
            conn, addr = srv.accept()
            print "connected from:", addr
            #客户端加入队列
            item = [conn, addr[0]]
            #以本地发起连接端口为主键
            self.servlist[addr[1]] = item


    def _connect(self, lport, host, port, default):
        '''	处理连接，num为流编号（第0号还是第1号）

        @note: 如果连接不到远程，会sleep 36s，最多尝试200(即两小时)
        '''
        if default == True:
            host = self.defaultremoteip
            port = self.defaultremoteport

        not_connet_time = 0
        while True:
            if not_connet_time > self.try_cnt:
                print('cant not connected')
                return None

            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                conn.connect((host, port))
            except Exception as e:
                print('can not connect %s:%s!' % (host, port))
                not_connet_time += 1
                time.sleep(self.wait_time)
                continue

            #以本地发起端口为主键
            item = [default, conn, host, port]
            self.remotelist[lport] = item
            return item

    def start_server(self):
        t=threading.Thread(target=self._server(), args=(self))
        t.start()
        t.join()

    def start_proxy(self):
        out=threading.Thread(target=self.localoutstream(), args=(self))
        out.start()
        out.join()

        remotein=threading.Thread(target=self.remoteinstream(), args=(self))
        remotein.start()
        remotein.join()

    def connect_xmr(self, lport, host, port):
        ret = self._connect(lport, host, port,True)


def test():
    proxy = tcpproxy('9000')
    proxy.start_server()
    proxy.start_proxy()
    proxy.connect_xmr('9999','','')

if __name__ == "__main__":
    test()