import pcap  
import dpkt  
  
cap = pcap.pcap('eth1')      
cap.setfilter('tcp port 80')  
files4out = {}  
url = 'www.baidu.com'  
  
for ptime,pktdata in cap:    
    print 'cap in'
    pkt = dpkt.ethernet.Ethernet(pktdata)  
    if pkt.data.data.__class__.__name__ <> 'TCP':  
        continue  
    ipsrc_tag = 0  
    ipdst_tag = 0  
    sport_tag = 0  
    dport_tag = 0  
  
    ipdata = pkt.data  
    sip='%d.%d.%d.%d'%tuple(map(ord,list(ipdata.src)))  
    dip='%d.%d.%d.%d'%tuple(map(ord,list(ipdata.dst)))  
  
    tcpdata = pkt.data.data  
    sport = tcpdata.sport  
    dport = tcpdata.dport  
      
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
  
    content = url  
    FLAG = 0  
      
    appdata = tcpdata.data  
    if appdata.find(content) <> -1:  
        print 'find'  
        FLAG = 1  
      
    name = src_tag + '_' + dst_tag + '_' + sp_tag + '_' + dp_tag  
    if (name) in files4out:  
        item = files4out[name]  
        fi = 0  
        cnt = item[1]  
        if cnt < 6 and item[3] <> 1:  
            item[1] += 1  
            item[2].append(pktdata)  
            if FLAG == 1:  
                item[3] = 1  
        elif item[3] == 1:  
            for index in range(cnt+1):  
                pktdatai = item[2][index]  
                pkti = dpkt.ethernet.Ethernet(pktdatai)  
                ipdatai = pkti.data  
                tcpdatai = pkti.data.data  
                sipi='%d.%d.%d.%d'%tuple(map(ord,list(ipdatai.src)))  
                dipi='%d.%d.%d.%d'%tuple(map(ord,list(ipdatai.dst)))  
                sporti = tcpdatai.sport  
                dporti = tcpdatai.dport  
                print '[datai]' + sipi + ':' + str(sporti) + '-' + dipi + ':' + str(dporti)  
            item[1] = -1  
              
            print '[data]' + sip + ':' + str(sport) + '-' + dip + ':' + str(dport)  
        else:  
            del files4out[name]  
              
              
    else:  
        item = [0, 0, [], 0, 0]  
  
        item[2].append(pktdata)  
        files4out[name] = item  
