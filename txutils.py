import socket
from time import sleep

def scanRx():
    clients=[]
    hostIP=socket.gethostbyname(socket.gethostname())
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
    s.settimeout(1)
    s.bind((hostIP,42821))
    s.sendto(b'TI',('255.255.255.255',34710))
    while 1:
        try:
            data,addr=s.recvfrom(4096)
            if int(data[0])==17:
                clientIP=addr[0]
                tmp=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
                tmp.bind((hostIP,42826))
                tmp.settimeout(0.5)
                tmp.sendto(b'DP',(clientIP,34710))
                d,a=tmp.recvfrom(4096)
                dport=int.from_bytes(d,'little')
                tmp.sendto(b'CS',(clientIP,34710))
                d,a=tmp.recvfrom(4096)
                cstate=int(d[0])
                clients.append((clientIP,dport,cstate))
                tmp.close()
        except:
            break
    s.close()
    return clients

def getDataPort(ip):
    cnsk=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    cnsk.bind((socket.gethostbyname(socket.gethostname()),42877))
    cnsk.settimeout(0.1)
    cnsk.sendto(b'DP',(ip,34710))
    try:
        d,a=cnsk.recvfrom(4096)
    except:
        cnsk.close()
        return -1
    dp=int.from_bytes(d,'little')
    cnsk.close()
    return dp

def getConnectionState(ip):
    cnsk=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    cnsk.bind((socket.gethostbyname(socket.gethostname()),42871))
    cnsk.settimeout(0.1)
    cnsk.sendto(b'CS',(ip,34710))
    try:
        d,a=cnsk.recvfrom(4096)
    except:
        cnsk.close()
        return -1
    cnsk.close()
    return int.from_bytes(d,'little')

def connectToRx(ip):
    cnsk=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    cnsk.bind((socket.gethostbyname(socket.gethostname()),42874))
    cnsk.settimeout(0.1)
    cnsk.sendto(b'OL',(ip,34710))
    try:
        d,a=cnsk.recvfrom(4096)
    except:
        cnsk.close()
        return -1
    cnsk.close()
    if d==b'pair ok':
        return 1
    elif d==b'paired':
        return 2
    else:
        return 0

def disconnectFromRx(ip):
    cnsk=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    cnsk.bind((socket.gethostbyname(socket.gethostname()),42874))
    cnsk.settimeout(0.1)
    cnsk.sendto(b'CL',(ip,34710))
    cnsk.close()
    return 1