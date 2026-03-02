from importlib.resources import read_binary
import os
import shutil
from posixpath import split
import time
import asyncio
import logging
import re
from tkinter import Label, Tk, mainloop, messagebox,Entry,Button
import traceback
from turtle import left
from xml.etree.ElementTree import tostring
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, LoggingEventHandler
import  socket
from threading import Thread
import threading
EMPNUM =""
FIXTURE=""
LINE=""
SFISIP=""
SFISPORT=""
EC=""
PRE_SN=""
retry_SN_list=[]
retrycont_list=[]
retryfilelocation_list=[]
retryinitiallocation_list=[]
panelization=""
panelization_CNT=0
panelization_Limit=0
retrycont=0
retryfilelocation=""
retryinitiallocation=""
retrymergelocation=""
retrystate=0
pre1=""
lastline=0
retryres=""
EC_Enable=False
datefmt=time.strftime("%Y-%m-%d")#只有日期
mypath = "SFISSENDLOG\\"+datefmt
if not os.path.isdir(mypath):
    os.makedirs(mypath)
##############################################################
def initial():
    def initialset():
        global EMPNUM,FIXTURE,LINE,SFISIP,SFISPORT,mypath,panelization_CNT
        EMPNUM=EMP_NUM.get()
        FIXTURE=FIXTURE_NUM.get()
        LINE=LINE_NUM.get()
        panelization_CNT=panelization.get()
        #SFISIP=IP_add.get()
        #SFISPORT=PORT_add.get()
        #SFISIP="10.0.5.47"
        #SFISPORT=21347
        SFISIP="127.0.0.1"
        SFISPORT=1024
        if(EMP_NUM=="" or FIXTURE=="" or LINE==""):
            pleasecheckinput()
        elif(SFISIP=="" or SFISPORT==""):
            notsetsfis()
        elif(int(panelization_CNT)<=0 or int(panelization_CNT)>=255 ):
            numinputerror()
        else:
            with open(mypath+'\\'+"SFISRESULT"+".txt",'a') as f:
                f.write("EMPNUM="+EMPNUM+'\n')
                f.write("FIXTURE_NUM="+FIXTURE+'\n')
                f.write("LINE_NAME="+LINE+'\n')
                f.write("SFISIP="+SFISIP+'\n')
                f.write("SFISPORT="+str(SFISPORT)+'\n')
                date=time.strftime("%Y-%m-%d %H:%M:%S")
                f.write("Start Time="+date+'\n')
                f.write("#################"+'\n')
            InitialWindow.destroy()
    InitialWindow = Tk(className="Key_in_EMP_and_Fixture_NUM")
    InitialWindow.attributes('-topmost', 'true')
    width = 400
    heigh = 400
    screenwidth = InitialWindow.winfo_screenwidth()
    screenheight = InitialWindow.winfo_screenheight()
    InitialWindow.geometry('%dx%d+%d+%d'%(width, heigh, (screenwidth-width)/2, (screenheight-heigh)/2))
    InitialWindow.overrideredirect(1)
    EMP=Label(InitialWindow, text='EMP:') 
    EMP.pack()
    EMP_NUM = Entry(InitialWindow)
    EMP_NUM.pack()
    FIXTURE_NUMBER = Label(InitialWindow, text='FIXTURE_NUM:')
    FIXTURE_NUMBER.pack()
    FIXTURE_NUM = Entry(InitialWindow)
    FIXTURE_NUM.pack()
    LINE_NAME = Label(InitialWindow, text='LINE_NAME:')
    LINE_NAME.pack()
    LINE_NUM = Entry(InitialWindow)
    LINE_NUM.pack()
    panelization_NUM = Label(InitialWindow, text='panelization_NUM')
    panelization_NUM.pack()
    panelization = Entry(InitialWindow)
    panelization.pack()
    #SFISIPadd = Label(InitialWindow, text='SFISIPadd:')
    #SFISIPadd.pack()
    #IP_add = Entry(InitialWindow)
    #IP_add.pack()
    #SFISPORTadd = Label(InitialWindow, text='SFISPORTadd:')
    #SFISPORTadd.pack()
    #PORT_add = Entry(InitialWindow)
    #PORT_add.pack()
    SetEMPandFIXTURE=Button(InitialWindow, text="Set",command=initialset)
    SetEMPandFIXTURE.pack() 
    InitialWindow.mainloop()
##############################################################
def ERROR_CHECK(path,modified_sn):
    def dontsend():
        global retrycont,retrystate,retryfilelocation,retryinitiallocation,retry_SN_list
        retrycont=0
        retrystate=0
        retryfilelocation=""
        retryinitiallocation=""
        FailWindow.destroy()
    def ECget():
        global retrycont,retrystate,retryfilelocation,retryinitiallocation
        retrycont=0
        retrystate=0
        retryfilelocation=""
        retryinitiallocation=""
        global EC_Enable,mypath,EC
        EC=ERROR_CODE.get()
        with open(mypath+'\\'+"SFISRESULT"+".txt",'a') as f:
                f.write("ERROR_CODE="+EC+'\n')
        #print("ERROR_CODE="+EC)
        if(EC==""):EC_Enable=False
        else:EC_Enable=True
        FailWindow.destroy()
    def retry():
        global retry_SN_list,retrycont_list,retryfilelocation_list,retryinitiallocation_list
        #global retrycont,retrystate,retryfilelocation,retryinitiallocation
        if (len(retry_SN_list)==0):
            retry_SN_list.append(modified_sn)
            retrycont_list.append(1)
            retryinitiallocation_list.append(path)
            retryfilelocation_list.append(path)
        else:
            SNnotin=1
            for i in range(len(retry_SN_list)):
                if(modified_sn in retry_SN_list[i]):
                    retrycont_list[i]=retrycont_list[i]+1
                    retryfilelocation_list[i]=path
                    SNnotin=0
                    break
            if(SNnotin):    
                retry_SN_list.append(modified_sn)
                retrycont_list.append(1)
                retryinitiallocation_list.append(path)
                retryfilelocation_list.append(path)
            #print(SNnotin)
            
        #if(retrycont==0):
        #    retrycont=retrycont+1
        #    retryinitiallocation=path
        #    retryfilelocation=path
        #    retrystate=1
        #elif(retrycont>0):
        #    retrycont=retrycont+1
        #    retryfilelocation=path
        #    retrystate=1
            
        FailWindow.destroy()
    FailWindow = Tk(className="fail")
    FailWindow.attributes('-topmost', 'true')
    width = 400
    heigh = 400
    screenwidth = FailWindow.winfo_screenwidth()
    screenheight = FailWindow.winfo_screenheight()
    FailWindow.geometry('%dx%d+%d+%d'%(width, heigh, (screenwidth-width)/2, (screenheight-heigh)/2)) 
    FailWindow.overrideredirect(1)
    EC = Label(FailWindow, text='ERROR_CODE:')
    EC.pack()
    ERROR_CODE = Entry(FailWindow)
    ERROR_CODE.pack()   
    Dontsend=Button(FailWindow, text="NOT Send",command=dontsend)
    Dontsend.pack()
    SendEC=Button(FailWindow, text="Send EC",command=ECget)
    SendEC.pack()
    Retry=Button(FailWindow, text="Retry",command=retry)
    Retry.pack()
    SN = Label(FailWindow, text="SN:"+modified_sn)
    SN.pack()
    FailWindow.mainloop()
##############################################################
def pleasecheckinput():
    pleasecheckinputWindow = Tk(className="pleasecheckinput")
    width = 400
    heigh = 400
    pleasecheckinputWindow.attributes('-topmost', 'true')
    screenwidth = pleasecheckinputWindow.winfo_screenwidth()
    screenheight = pleasecheckinputWindow.winfo_screenheight()
    pleasecheckinputWindow.geometry('%dx%d+%d+%d'%(width, heigh, (screenwidth-width)/2, (screenheight-heigh)/2))
    pleasecheckinputWindow.overrideredirect(1)
    ERROR_MESSAGE = Label(pleasecheckinputWindow, text='SOME_INPUT_IS_EMPTY_PLEASE_RECHECK') 
    ERROR_MESSAGE.pack()
    Confirm=Button(pleasecheckinputWindow, text="Confirm",command=pleasecheckinputWindow.destroy)
    Confirm.pack()
    pleasecheckinputWindow.mainloop()
def numinputerror():
    numinputerrorWindow = Tk(className="numinputerror")
    width = 400
    heigh = 400
    numinputerrorWindow.attributes('-topmost', 'true')
    screenwidth = numinputerrorWindow.winfo_screenwidth()
    screenheight = numinputerrorWindow.winfo_screenheight()
    numinputerrorWindow.geometry('%dx%d+%d+%d'%(width, heigh, (screenwidth-width)/2, (screenheight-heigh)/2))
    numinputerrorWindow.overrideredirect(1)
    ERROR_MESSAGE = Label(numinputerrorWindow, text='NUM NEED > 0') 
    ERROR_MESSAGE.pack()
    Confirm=Button(numinputerrorWindow, text="Confirm",command=numinputerrorWindow.destroy)
    Confirm.pack()
    numinputerrorWindow.mainloop()
def SFISPASS(sfisdata):
    SFISPASS = Tk(className="SFISPASS")
    width = 400
    heigh = 400
    SFISPASS.config(bg="Green")
    SFISPASS.attributes('-topmost', 'true')
    screenwidth = SFISPASS.winfo_screenwidth()
    screenheight = SFISPASS.winfo_screenheight()
    SFISPASS.geometry('%dx%d+%d+%d'%(width, heigh, (screenwidth-width)/2, (screenheight-heigh)/2))
    SFISPASS.overrideredirect(1)
    PASS_MESSAGE = Label(SFISPASS, text=sfisdata,bg="Green",anchor="center",font=("Helvetica", 30)) 
    PASS_MESSAGE.pack(expand=True)
    SFISPASS.after(5000, SFISPASS.destroy)
    SFISPASS.mainloop()
def SFISFAIL(sfisdata):
    SFISFAIL = Tk(className="SFISFAIL")
    width = 400
    heigh = 400
    SFISFAIL.config(bg="Red")
    SFISFAIL.attributes('-topmost', 'true')
    screenwidth = SFISFAIL.winfo_screenwidth()
    screenheight = SFISFAIL.winfo_screenheight()
    SFISFAIL.geometry('%dx%d+%d+%d'%(width, heigh, (screenwidth-width)/2, (screenheight-heigh)/2))
    SFISFAIL.overrideredirect(1)
    FAIL_MESSAGE = Label(SFISFAIL, text=sfisdata,bg='Red',anchor="center",font=("Helvetica", 30)) 
    FAIL_MESSAGE.pack(expand=True)
    SetEMPandFIXTURE=Button(SFISFAIL, text="CONFIRM",command=SFISFAIL.destroy)
    SetEMPandFIXTURE.pack() 
    SFISFAIL.mainloop()
##############################################################
def notsetsfis():
    notsetsfisWindow = Tk(className="notsetsfis")
    width = 400
    heigh = 400
    screenwidth = notsetsfisWindow.winfo_screenwidth()
    screenheight = notsetsfisWindow.winfo_screenheight()
    notsetsfisWindow.geometry('%dx%d+%d+%d'%(width, heigh, (screenwidth-width)/2, (screenheight-heigh)/2))
    notsetsfisWindow.overrideredirect(1)
    ERROR_MESSAGE = Label(notsetsfisWindow, text='SFIS_SETTING_IS_EMPTY_PLEASE_RECHECK') 
    ERROR_MESSAGE.pack()
    SetEMPandFIXTURE=Button(notsetsfisWindow, text="SURE",command=notsetsfisWindow.destroy)
    SetEMPandFIXTURE.pack() 
    notsetsfisWindow.mainloop()
##############################################################
def Delay_Time():#讀黨延遲
    global Time_Flag
    time.sleep(2)
    Time_Flag=0

def CopyFileToServer(path,result,PN):#上傳Log與Result與configure至SERVER並依照Work Order分割 
    #source_path=r"C:\EOL\RRGW_v3.0.7\Results" #資料來源
    #dest_path=r"Z:\TEST\T1\16_3"            #要複製到的地方
    walk2=path.split("\\")[0]#檔名
    Logpath=os.path.abspath(walk2).split("\\"+walk2)[0]
    #print(Logpath.split("\\")[-2])
    source_path=Logpath
    #Serverpath="Z:\\"
    Serverpath="D:\\Admin\\Documents\\"+Logpath.split("\\")[-1]
    #print(Serverpath)
    datefmt=time.strftime("%Y-%m-%d")#只有日期
    Time_Flag=2
    read=re.split("./|_",path)
    #read=read[0]
    #Logname=str(read[0:8])#擷取SN當黨名
    #t = threading.Thread(target = Delay_Time)
    #t.start()
    try:
        if(result=="PASS"):
            newpath = Serverpath +'\\SPEA_BACK_UP'+'\\'+PN+'\\'+datefmt+'\\PASS\\'#放測試Result的位置
        elif(result=="FAIL" or result=="INTERRUPTED"):
            newpath = Serverpath +'\\SPEA_BACK_UP'+'\\'+PN+'\\'+datefmt+'\\FAIL\\'#放測試Result的位置
        if not os.path.exists(newpath):#抓資料夾，，沒有就建一個
                os.makedirs(newpath)
        shutil.copy(source_path +'\\' +path, newpath+path)
    except Exception as other:
        traceback.print_exc()
        xx=0
def Autoupdate(srcpath,result,PN):#判斷測試完成自動上傳
    path=srcpath.split("./")[1]#取檔名
    CopyFileToServer(path,result,PN)#複製到SERVER的副程式
##############################################################
##############################################################
def retestmerge(initialpath,path):
    global retrycont,retrystate,retryinitiallocation,retryres,lastline,retry_SN_list,retryfilelocation_list,retryinitiallocation_list
    lines=""
    lines1=""
    keyword=""
    cont=0
    ini=""
    retrycntget=0
    initial=initialpath
    for i in range (len(retry_SN_list)):
        if( path.split('./')[1].split('-')[0] in retry_SN_list[i]):
        #if  path.split('./')[1].split('\\')[1].split('-')[0] in retry_SN_list[i]:
            initial=retryfilelocation_list[i]
            ini=retryinitiallocation_list[i]
            retrycntget=retrycont_list[i]
            break
    source=path
    result=ini+"_retry"+"_"+str(retrycntget)
    with open(initial, 'r') as g:
        lines = g.readlines()
    with open(source,'r') as s:
                lines1=s.readlines()
    falcnt=0
    pn_line=lines[1]
    PN=pn_line.split(";")[2]
    for line in lines:
        if "FAIL(" in line:
            temp=line.split(';')
            #print(temp)
            #if(temp>2):
            #keyword=temp[0]+';'+temp[1]+';'+temp[2]+';'+temp[3]+';'+temp[4]+';'+temp[5]
            keyword=temp[0]+';'+temp[1]+';'+temp[2]+';'+temp[3]+';'+temp[4]+';'
            #print(keyword)
            for line1 in reversed (lines1):
                if keyword in line1:
                    lines[cont]=line1
                    break
        if"BOARDRESULT" in line:
            for line1 in lines1:
                if "BOARDRESULT" in line1:
                    lines[cont]=line1
                    #print(line1)
                    lastline=cont-1
                    break
        #if "END" in line:
        #    for line1 in lines1:
        #        if "END" in line1:
        #            lines[cont]=line1
        #            #print(line1)
        #            break
        cont=cont+1
    cont=0
    find=0
    for line1 in reversed(lines1):
        if(("FAIL(" in line1 or "PASS" in line1) and "BOARDRESULT" not in line1 and ("END" not in line1) ):
            temp=line1.split(';')
            #print(temp)
            keyword=temp[0]+';'+temp[1]+';'+temp[2]+';'+temp[3]+';'+temp[4]+';'
            for line in lines:
                if keyword in line:
                    find=1
                    break
            if(find==0):
                lines.insert(lastline, line1)
        find=0
    lastline=0   
    #print(lines[-1])
    #print(lines1[-1])  
    lines[-1]=lines1[-1]
    #print("AAAAAAAAAAAAAAAaa"+result)
    with open(result, "w") as f:
        f.writelines(lines)
    with open(path, 'r') as g:
        lines=g.readlines()
        last_line = lines[-1]
        retryres=last_line.split(";")[1]
    Autoupdate(path,retryres,PN)
    Connectsfis("./"+result)
##############################################################
def Connectsfis(srcpath):
    global EMPNUM,FIXTURE,LINE,EC,EC_Enable,SFISIP,SFISPORT,mypath,panelization_Limit,panelization_CNT,retry_SN_list,retrycont_list,retryfilelocation_list,retryinitiallocation_list
    SN=""
    PN=""
    modified_sn=""
    testresult=""
    path=srcpath.split("./")[1]
    #print("pathhhhhhhhhhhhhhhh:::::::::::"+path)
    datefmt=time.strftime("%Y-%m-%d")#只有日期
    with open(path, 'r') as g:
        global PRE_SN
        lines=g.readlines()
        last_line = lines[-1]
        sn_line=lines[-3]
        pn_line=lines[1]
        testresult=last_line.split(";")[1]
        SN=sn_line.split("SN")[1]
        PN=pn_line.split(";")[2]
        modified_sn = SN[1:]
        PRE_SN=modified_sn
        with open(mypath+'\\'+"SFISRESULT"+".txt",'a') as f:
                date=time.strftime("%Y-%m-%d %H:%M:%S")
                f.write("Tset FINISH Time="+date+'\n')
                f.write("TEST_RESULT="+testresult+'\n')
                f.write("SN="+modified_sn)
                f.write("EMPNUM="+EMPNUM+'\n')
                f.write("STATION="+FIXTURE+'\n')
    HOST = SFISIP
    PORT = int(SFISPORT)
    max_retries=3
    attempts=0
    while attempts < max_retries :
        try:
            s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)       #定义socket类型，网络通信，TCP
            s.connect((HOST,PORT))        #要连接的IP与端口
            cmd=FIXTURE+","+modified_sn+","+"1"+","+EMPNUM+","+LINE+",,"+"OK"
            s.sendall(bytes(cmd,encoding='utf-8'))   
            data = s.recv( 1024 )
            time.sleep(0.5)   
            if(testresult=="PASS"):
                global retrycont,retrystate
                retrystate=0
                retrycont=0
                s.close()    #关闭连接
                time.sleep(1)
                s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                s.connect((HOST,PORT))        #要连接的IP与端口
                cmd=FIXTURE+","+modified_sn+","+"2"+","+EMPNUM+","+LINE+",,"+"OK"
                s.sendall(bytes(cmd,encoding='utf-8'))   
                data = s.recv( 1024 ) 
                datefmt=time.strftime("%Y-%m-%d")#只有日期 
                with open(mypath+'\\'+"SFISRESULT"+".txt",'a') as f:
                        date=time.strftime("%Y-%m-%d %H:%M:%S")
                        f.write("SEND SFIS TIME="+date+'\n')
                        f.write("SFIS REPLY="+(str(data).split("b")[1]).split("'")[1]+'\n')
                        f.write("####################"+'\n')
                outputdata=("SFIS REPLY="+(str(data).split("b")[1]).split("'")[1]+'\n')
                if("FAIL" not in str(data)):
                    SFISPASS(outputdata)
                else:
                    SFISFAIL(outputdata)
                Autoupdate(srcpath,"PASS",PN)
                s.shutdown(socket.SHUT_RDWR)  
                s.close()    #关闭连接
                panelization_Limit=panelization_Limit+1
            elif(testresult=="FAIL" or testresult=="INTERRUPTED"):  
                s.close()    #关闭连接
                time.sleep(1)
                s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                s.connect((HOST,PORT))        #要连接的IP与端口
                ERROR_CHECK(path,modified_sn)
                if(EC_Enable):
                    cmd=FIXTURE+","+modified_sn+","+"2"+","+EMPNUM+","+LINE+",,"+"FAIL,,"+EC
                    EC_Enable=False
                    panelization_Limit=panelization_Limit+1
                else:
                    #cmd=FIXTURE+","+modified_sn+","+"2"+","+EMPNUM+","+LINE+",,"+"FAIL,,"
                    cmd=FIXTURE+","+modified_sn+","+"1"+","+EMPNUM+","+LINE+",,"+"OK"
                s.sendall(bytes(cmd,encoding='utf-8'))   
                data = s.recv( 1024 )   
                with open(mypath+'\\'+"SFISRESULT"+".txt",'a') as f:
                        date=time.strftime("%Y-%m-%d %H:%M:%S")
                        f.write("SEND SFIS TIME="+date+'\n')
                        f.write("SFIS REPLY="+(str(data).split("b")[1]).split("'")[1]+'\n')
                        f.write("####################"+'\n')
                outputdata=("SFIS REPLY="+(str(data).split("b")[1]).split("'")[1]+'\n')
                Autoupdate(srcpath,"FAIL",PN)
                SFISFAIL(outputdata)
                s.shutdown(socket.SHUT_RDWR)  
                s.close()    #关闭连接
            else:
                s.shutdown(socket.SHUT_RDWR)  
                s.close()    #关闭连接
            time.sleep(0.5)
            if(panelization_Limit==int(panelization_CNT)):
                retry_SN_list=[]
                retrycont_list=[]
                retryfilelocation_list=[]
                retryinitiallocation_list=[]
                panelization_Limit=0
            #print(len(retry_SN_list))
            #print(panelization_Limit)
        except Exception:
            attempts += 1
            time.sleep(1)
        break
class ScriptEventHandler(FileSystemEventHandler):
    def __init__(self):
        FileSystemEventHandler.__init__(self)
 
    # 文件移动
    def on_moved(self, event):
    #def on_modified(self, event):
        if event.is_directory:#目錄移動
            #print("directory moved from {src_path} to {dest_path}".format(src_path=event.src_path,
            #                                                              dest_path=event.dest_path))
            a=0     
        else:#檔案移動
            #print("file moved from {src_path} to {dest_path}".format(src_path=event.src_path, dest_path=event.dest_path))
            srcpath=(event.src_path)#讀取新LOG move有分目標位置與來源位置 這一個是來源位置
            #if("PASS" in srcpath or"FAIL" in srcpath):#檢查偵測到的檔案是不是LOG
            #    #print("This update")
            #    Autoupdate(srcpath)
            srcpath=(event.dest_path)#讀取新LOG  move有分目標位置與來源位置 這一個是目標位置
            #if("PASS" in srcpath or"FAIL" in srcpath):#檢查偵測到的檔案是不是LOG
            #    #print("This update")
            #    Autoupdate(srcpath)
    # 文件新建
    def on_created(self, event):
        global pre1
        if event.is_directory:#目錄創建
            a=0
            #print("directory created:{file_path}".format(file_path=event.src_path))
        else:#檔案創建
            #srcpath=(event.src_path)#讀取新LOG
            a=0
            #if(pre1 != srcpath):#避免重複抓取
            #    pre1=srcpath
            #if("PASS" in srcpath or"FAIL" in srcpath):#檢查偵測到的檔案是不是LOG
            #    Autoupdate(srcpath)
            #if(pre1 != srcpath ):
            #    pre1 = srcpath
            #    set=True
            #    while(set):
            #        try:
            #            Connectsfis(srcpath)
            #            set=False
            #        except ConnectionRefusedError:
            #            forecclosesocket()
            #print("file created:{file_path}".format(file_path=event.src_path))
 #####################################################################################
    # 文件删除
    def on_deleted(self, event):
        if event.is_directory:#目錄刪除
            a=0
            #print("directory deleted:{file_path}".format(file_path=event.src_path))
        else:#檔案刪除
            #print("file deleted:{file_path}".format(file_path=event.src_path))
            a=0
 #################################################################################
    # 文件修改
    def on_modified(self, event):
    #def on_moved(self, event):
        global pre1,retrystate,retry_SN_list
        if event.is_directory: #目錄變更
            a=0
            #print("directory modified:{file_path}".format(file_path=event.src_path))
        else:#檔案變更
            #print("file modified:{file_path}".format(file_path=event.src_path))
            #a=0
            retrystate=0
            srcpath=(event.src_path)#讀取新LOG
            #if(pre1 != srcpath):#避免重複抓取
            #    pre1=srcpath
            #if(len(retry_SN_list)==0):
            #    retrystate=0
            if(pre1 != srcpath and 'SFIS' not in srcpath and 'Null' not in srcpath and 'SPEA_RESULT' and '11111111111111'  not in srcpath and "retry" not in srcpath ):
                pre1=srcpath
                set=True
                for i in range(len(retry_SN_list)):
                    #print(retry_SN_list[i])
                    #print(srcpath.split('./')[1].split('\\')[1].split('-')[0])
                    #print(srcpath.split('./'))
                    #print(retrystate)
                    if( srcpath.split('./')[1].split('-')[0] in retry_SN_list[i]):
                        retrystate=1
                        break
                while(set):
                    try:
                        global datefmt,mypath
                        datefmt=time.strftime("%Y-%m-%d")#只有日期
                        mypath = "SFISSENDLOG"
                        if not os.path.isdir(mypath):
                            os.makedirs(mypath)
                        mypath = "SFISSENDLOG\\"+datefmt
                        if not os.path.isdir(mypath):
                            os.makedirs(mypath)
                        #if "retry" not in srcpath:
                        if(1):    
                            global retryinitiallocation,PRE_SN
                            oldarc=retryinitiallocation.split('-')[0]
                            #if(retrystate==0  or ((oldarc not in srcpath) and PRE_SN not in srcpath)):
                            #print(retrystate,"  +  ",srcpath)
                            if(retrystate==0 ):
                                #print("normal")
                                retrystate=0
                                Connectsfis(srcpath)
                            else:
                                for i in range(len(retry_SN_list)):
                                    if( srcpath.split('./')[1].split('-')[0] in retry_SN_list[i]):
                                    #if  srcpath.split('./')[1].split('\\')[1].split('-')[0] in retry_SN_list[i]:
                                        if retrycont_list[i]>0:
                                            #print("retry")
                                            retestmerge(retryfilelocation,srcpath)
                                            break           
                                #retestmerge(retryfilelocation,srcpath)
                        set=False
                        #print(len(retry_SN_list))
                    except ConnectionRefusedError:
                        forecclosesocket()
            #if("PASS" in srcpath or"FAIL" in srcpath):#檢查偵測到的檔案是不是LOG
            #    Autoupdate(srcpath)
            #        passfail(srcpath)#目前針對16 17 18
##############################################################
def forecclosesocket():
    global SFISPORT
    kill_port = SFISPORT
    result = os.popen("netstat -ano | findstr {p}".format(p=kill_port))
    readStr = result.readlines()
    if not readStr:
        print("PORT NOT Found，┭┮﹏┭┮")
    ports = set()
    for st in readStr:
        arr = st.split()
        port = arr[4]
        ports.add(port)
    for port in ports:
        res = os.popen("taskkill /f /pid " + port)
        print("SUCCESS，KILL PORT=%s，pid=%s" % (kill_port, port))
async def main():
    while(True):
        #print("F")
        z=1
# #############################################################                      
if __name__ == "__main__":
    initial()
    event_handler1 = ScriptEventHandler()
    observer = Observer()
    watch = observer.schedule(event_handler1,
                              path="./",
                              recursive=True)
 
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')#顯示及時偵測資訊
    event_handler2 = LoggingEventHandler()
    observer.add_handler_for_watch(event_handler2, watch)  # 为watch新添加一个event handler
    observer.start()
    asyncio.run(main())
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
