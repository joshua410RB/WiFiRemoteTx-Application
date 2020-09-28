import socket
import pygame
import wx
import wx.grid as grid
import txutils
from threading import Thread
from time import sleep

rxIP='0.0.0.0'
dataport=0
dport=[]
conn_state=0
connRow=0
dataSendFlag=0

packet=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
joystickFlag=0

scanList=[]

def updateJoystick():
    global packet
    global joystickFlag
    pygame.joystick.init()
    pygame.display.init()
    while 1:  
        jcount=pygame.joystick.get_count()
        if joystickFlag==1 and jcount>0:
            for event in pygame.event.get():
                if event.type==pygame.QUIT:
                    sys.exit()
                elif event.type==pygame.JOYBUTTONDOWN:
                    pass
        
            for i in range(2):
                packet[2*i]=int(127+(j.get_axis(2*i)*127))
                packet[2*i+1]=int(127-(j.get_axis(2*i+1))*127)
            for i in range (j.get_numbuttons()):
                packet[i+4]=j.get_button(i)
        else:
            if jcount==0:
                if joystickFlag==1:
                    jsLabel.SetLabel("Joystick: ")
                joystickFlag=0
            else:
                j=pygame.joystick.Joystick(0)
                j.init()
                jsNameStr="Joystick: "+j.get_name()
                jsLabel.SetLabel(jsNameStr)
                joystickFlag=1
        sleep(0.001)

def scanFunc():
    global scanList
    #scanList=[]
    scanList.clear()
    scanList=txutils.scanRx()
    if g.GetNumberRows()>0:
        g.DeleteRows(0,g.GetNumberRows())
    rcount=0
    for i in scanList:
        g.AppendRows(1)
        g.SetCellValue(rcount,0,str(i[0]))
        if i[2]==1:
            if i[0]==rxIP:
                g.SetCellValue(rcount,1,"Connected")
                g.SetCellBackgroundColour(rcount,0,(0,255,0))
                g.SetCellBackgroundColour(rcount,1,(0,255,0))
                connRow=rcount
            else:
                g.SetCellValue(rcount,1,"Paired")
        else:
            g.SetCellValue(rcount,1,"Open")
        rcount=rcount+1
    return scanList

def scanEventFunc(event):
    slist=scanFunc()

def connectEventFunc(event):
    global conn_state
    global rxIP
    global dataport
    global connRow
    selrow=0
    if g.GetNumberRows()<1:
        print("No Rx available")
        return
    if conn_state==0:
        selrow=g.GetGridCursorRow()
        rxIP=g.GetCellValue(selrow,0)
        rx_cs=txutils.getConnectionState(rxIP)
        if rx_cs==-1:
            print("CS: error")
            return
        elif rx_cs==1:
            print("Rx is already paired to another device")
            return
        dataport=txutils.getDataPort(rxIP)
        if dataport==-1:
            print("Unable to get data port")
            return
        resp=txutils.connectToRx(rxIP)
        if resp<1:
            print("connection error")
            return
        elif resp==2:
            print("already connected")
            return
        conn_state=1
        connRow=selrow
        csLabel.SetLabel("Connected")
        csLabel.SetForegroundColour((0,222,30))
        rxLabelStr="Receiver: "+str(rxIP)
        rxLabel.SetLabel(rxLabelStr)
        g.SetCellValue(selrow,1,"Connected")
        for i in range(0,g.GetNumberCols()):
            g.SetCellBackgroundColour(selrow,i,(0,255,0))
            g.ForceRefresh()
        connectBtn.SetLabel("Disconnect")
    else:
        txutils.disconnectFromRx(rxIP)
        conn_state=0
        rxIP='0.0.0.0'        
        csLabel.SetForegroundColour((255,0,0))
        csLabel.SetLabel("Not Connected")
        rxLabelStr="Receiver: "
        rxLabel.SetLabel(rxLabelStr)
        for i in range(0,g.GetNumberCols()):
            g.SetCellBackgroundColour(selrow,i,(255,255,255))
            g.ForceRefresh()
        connectBtn.SetLabel("Connect")
        scanFunc()

def dataThread():
    global conn_state
    global rxIP
    global dataport
    global packet
    dataSocket=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    dataSocket.bind((socket.gethostbyname(socket.gethostname()),42844))
    while 1:
        if conn_state==1:
            dataSocket.sendto(bytes(packet),(rxIP,dataport))
        sleep(0.01)

def KAThread():
    global conn_state
    global rxIP
    global connRow
    missCount=0
    ks=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    ks.bind((socket.gethostbyname(socket.gethostname()),42873))
    ks.settimeout(0.005)
    while 1:
        if conn_state==1:
            ks.sendto(b'KA',(rxIP,34710))
            try:
                ksd=b''
                ksd,ksa=ks.recvfrom(4096)
            except:
                pass
            if ksd==b'ok':
                missCount=0
            else:
                missCount=missCount+1
            if missCount>100:
                conn_state=0
                rxIP='0.0.0.0'                
                csLabel.SetForegroundColour((255,0,0))
                csLabel.SetLabel("Not Connected")
                rxLabelStr="Receiver: "
                rxLabel.SetLabel(rxLabelStr)
                connectBtn.SetLabel("Connect")
                scanFunc()
                # g.SetCellValue(connRow,1,"Open")
                # g.SetCellBackgroundColour(connRow,0,(255,255,255))
                # g.SetCellBackgroundColour(connRow,1,(255,255,255))
        sleep(0.001)

kaT=Thread(target=KAThread)
kaT.daemon=True
kaT.start()

daT=Thread(target=dataThread)
daT.daemon=True
daT.start()

app=wx.App()
frame=wx.Frame(None,-1,"WiFi Remote Tx")
frame.SetDimensions(0,0,348,400)

panel=wx.Panel(frame,wx.ID_ANY)
g=grid.Grid(panel,size=wx.Size(186,230),pos=(10,100))
g.CreateGrid(0,2)
g.SetRowLabelSize(25)
g.SetColLabelValue(0,"IP Address")
g.SetColLabelValue(1,"Status")
g.EnableEditing(False)
g.EnableDragColSize(False)
g.EnableDragRowSize(False)

scanBtn=wx.Button(panel,wx.ID_ANY,'Scan',(220,100))
scanBtn.Bind(wx.EVT_BUTTON,scanEventFunc)

connectBtn=wx.Button(panel,wx.ID_ANY,'Connect',(220,135))
connectBtn.Bind(wx.EVT_BUTTON,connectEventFunc)

bigFont=wx.Font(18,wx.DEFAULT,wx.NORMAL,wx.NORMAL)

csLabel=wx.StaticText(panel,-1,"Not Connected",(10,10))
csLabel.SetFont(bigFont)
csLabel.SetForegroundColour((255,0,0))

rxLabel=wx.StaticText(panel,-1,"Receiver: ",(10,50))

jsLabel=wx.StaticText(panel,-1,"Joystick: ",(10,75))

jsT=Thread(target=updateJoystick)
jsT.daemon=True
jsT.start()

scanFunc()



frame.Show()
frame.Centre()
app.MainLoop()