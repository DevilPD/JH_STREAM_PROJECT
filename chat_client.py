# QThread - pyqtSignal/Slot Example https://m.blog.naver.com/townpharm/220959370280
# 모달방식 윈도우 제어 https://notstop.co.kr/479/
from threading import Thread
from PyQt5 import uic 
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot, QBasicTimer
from queue import Queue
from socket import *
from os.path import getsize
import time
import sys
import select
import os.path
import string

getItem = ''

send_queue = Queue()
msg1_queue = Queue()
msg2_queue = Queue()
get_queue = Queue()

check_queue_f = Queue()
check_queue_res = Queue()

send_queue_d = Queue()
end_queue = Queue()

list_queue = Queue()
select_queue = Queue()
select_queue_ok = Queue()

upload_queue = Queue() # 업로드 버튼을 누를시 'upload' 를 queue에 넣어 서버 연결 시작
upload_queue_s = Queue() # 업로드 버튼을 누른 후 선택한 파일이 들어가는 queue

enter_num = 0
cnt = 0
cnt2 = 0

now_size_queue = Queue() # prograssbar Value
test = 0 # prograssbar MaxValue


host = 'localhost'

# 39.125.60.175
# localhost
# 192.168.252.128

def FileUpload():

    global host
    global test

    port = 12345

    print('Thread FileUpload Start')
    while True:
        msg = upload_queue_s.get()
    
        if msg != '':
            try:
                upload_socket = socket(AF_INET, SOCK_STREAM)
                upload_socket.connect((host, port))
            except Exception as e:
                print(e)
                break

            print('업로드 소켓 연결 완료..')
            print(msg + '를 업로드 시작합니다')

            filename = msg.split('/')

            upload_socket.send(filename[-1].encode())
            sig = upload_socket.recv(1024)
            print(sig.decode('utf-8'))
            test = getsize(msg)
            print('업로드할 파일 용량 : ' + str(test))

            try:
                data = 0
                data_transferred = 0
                with open(msg, 'rb') as f:
                    try:
                        data = f.read(1024) #1024바이트 읽는다
                        while data: #데이터가 없을 때까지
                            data_transferred += upload_socket.send(data) #1024바이트 보내고 크기 저장
                            now_size_queue.put(data_transferred)
                            data = f.read(1024) #1024바이트 읽음
                    except Exception as ex:
                        print(ex)
                
                print("전송완료 , 전송량 %d" %(data_transferred))
                print('서버와의 접속을 종료합니다.')
                upload_socket.close()

            except Exception as e:
                print(e)
                upload_socket.close()
                break
        else:
            print('파일 선택 안함.')


def FileDown(filename):

    global host
    global test
    port = 23456
    
    data = 0
    data_transferred = 0

    while True:
        try:
            client_socket = socket(AF_INET, SOCK_STREAM)
            client_socket.connect((host, port))
            break
        except Exception as e:
            print(e)
            time.sleep(1)
            pass
    
    size = client_socket.recv(1024)
    print('용량 : ' + size.decode('utf-8'))
    test = size.decode('utf-8')

    sig = client_socket.send('ok'.encode())
    
    data = client_socket.recv(1024)

    nowdir = os.getcwd()
    print('파일 다운 시작..')
    try:
        with open(nowdir + "\\" + filename, 'wb') as f:  # 현재dir에 filename으로 파일을 받는다
            try:
                while data:  # 데이터가 있을 때까지
                    f.write(data)  # 1024바이트 쓴다
                    data_transferred += len(data)
                    now_size_queue.put(data_transferred)
                    data = client_socket.recv(1024)  # 1024바이트를 받아 온다
                    print('현재 다운량: ' + str(round(data_transferred / 1048576, 3)) + 'MB') # round(data_transferred / 1048576, 1)
            except Exception as ex:
                print('1')
                print(ex)
                pass
    except Exception as e:
        print('2')
        print(e)

    print('파일 %s 받기 완료. 전송량 %d' % (filename,data_transferred))
    client_socket.close()
    print("접속을 종료합니다.")

def FileAns(sock, UDP_IP, IN_PORT):
    while True:
        try:
            ans = select_queue_ok.get()
            print(ans)

            msg = ans.encode()
            sock.sendto(msg, (UDP_IP, IN_PORT))
            print('send')
            FileDown(ans)
        except Exception as e:
            print(e)
            pass


def FileCheck(sock, UDP_IP, IN_PORT):

    while True:
        try:
            cnt_u = 0
            data = check_queue_f.get() # check_queue에 'f'를 넣으면 서버 측 Files 폴더 내 파일을 불러옴
            print(data)
            msg = data.encode()
            sock.sendto(msg, (UDP_IP, IN_PORT))
            nm, addr_u = sock.recvfrom(1024)
            count = nm.decode('utf-8')
            print(count)
            while True:
                if cnt_u < int(count) :
                    cnt_u += 1
                    data, addr_u = sock.recvfrom(1024)
                    msg = data.decode('utf-8')
                    print(msg)
                    list_queue.put(msg)
                    data = 0
                else:
                    break
        except Exception as e:
            print(e)
            pass

def send(sock):

    global msg2_queue

    while True:
        print('...')
        msg = msg2_queue.get()
        sendData = bytes(msg.encode())
        sock.send(sendData)
        print('메세지를 보냈습니다 >> ' + msg)


def recv(sock):

    while True:
        getData = sock.recv(1024).decode()
        get_queue.put(getData)
        print('받은 메세지 : ' + getData)

def file_conn():
    print('Thread for FileCheck Start')

    try:
        global host
        UDP_IP = host
        IN_PORT = 10012
        IN_PORT_2 = 30033

        check_socket = socket(AF_INET, SOCK_DGRAM)
        check_socket.connect((UDP_IP, IN_PORT))

        ans_socket = socket(AF_INET, SOCK_DGRAM)
        ans_socket.connect((UDP_IP, IN_PORT_2))

        checker = Thread(target=FileCheck, args=(check_socket, UDP_IP, IN_PORT), daemon=True)
        answer = Thread(target=FileAns, args=(ans_socket, UDP_IP, IN_PORT_2), daemon=True)
        uploader_s = Thread(target=FileUpload, daemon=True)

        uploader_s.start()
        checker.start()
        answer.start()

    except Exception as e:
        print(e)
        pass



def sock_conn():
    global host
    # 서버와 연결하는 쓰레드
    print('Connect Thread Start')
    try:
        # 39.125.60.175
        # localhost
        # 192.168.252.128
        port = 20022
        # port_d = 23456

        client_socket = socket(AF_INET, SOCK_STREAM)
        client_socket.connect((host, port))

        sock = socket(AF_INET, SOCK_DGRAM)

        sender = Thread(target=send, args=(client_socket,), daemon=True)
        recver = Thread(target=recv, args=(client_socket,), daemon=True)

        sender.start()
        recver.start()

        print('접속에 성공했습니다.')

    except Exception as e:
        print('접속 실패.. 재접속 시도중')
        print(e)
        time.sleep(3)
        # break

class subWorker(QObject):

    sig_u = pyqtSignal([str])

    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)

    @pyqtSlot()
    def startList(self):
        while True:
            try:
                msg3 = list_queue.get()
                self.sig_u.emit(msg3)
            except Exception as e:
                print(e)
                pass

class Progress(QObject):
    
    sig_p_n = pyqtSignal([int])

    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)

    @pyqtSlot()           
    def startProgress(self):
        while True:
            try:
                size = now_size_queue.get()
                self.sig_p_n.emit(size)
            except Exception as e:
                print(e)
                pass

class Worker(QObject):
    
    sig = pyqtSignal([str])
    

    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)

    @pyqtSlot()           
    def startWork(self):
        while True:
            try:
                msg2 = get_queue.get()
                self.sig.emit(msg2)
                print('worker 에서 받음 : msg2')
            except Exception as e:
                print(e)
                pass

class Sub_Window(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        
        self.btn = QPushButton('채팅 서버')
        self.btn_c = QPushButton('파일 서버')
        self.list_g = QListWidget()
        self.list_reset = QPushButton('새로고침')
        self.btn_t = QPushButton('다운로드')
        self.btn_s = QPushButton('업로드')
        self.progess = QProgressBar()

        hbox = QHBoxLayout()

        hbox.addWidget(self.btn_t)
        hbox.addWidget(self.btn_s)

        hbox_b = QHBoxLayout()

        hbox_b.addWidget(self.btn)
        hbox_b.addWidget(self.btn_c)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox_b)
        vbox.addWidget(self.list_g)
        vbox.addWidget(self.list_reset)
        vbox.addLayout(hbox)
        vbox.addWidget(self.progess)

        self.setLayout(vbox)

        self.progess.hide()
        self.btn_c.setDisabled(True)

        self.list_reset.clicked.connect(self.getList)
        self.btn_s.clicked.connect(self.selectItem)
        # self.btn_t.clicked.connect(self.doAction)
        # self.btn_s.clicked.connect(self.doAction)

        # self.move(300, 300)
        self.resize(600, 400)

    def selectItem(self):
        global selec_file

        try:
            s_file = QFileDialog.getOpenFileName(self, 'Open file')
            upload_queue_s.put(s_file[0])
        except Exception as e:
            print(e)

    def getList(self):
        self.list_g.clear()
        check_queue_f.put('f')

    @pyqtSlot(str)
    def updateStatus_u(self, status):
        # print('#########start get status#############')
        # print(status)
        self.list_g.addItem('{}'.format(status))
        # self.list.scrollToBottom()
    
    @pyqtSlot(int)
    def Progress_start(self, status):
        self.progess.show()
        global test
        self.progess.setMaximum(int(test))
        self.progess.setValue(int(status))
        self.btn.setDisabled(True)
        self.btn_t.setDisabled(True)
        self.btn_s.setDisabled(True)
        self.list_reset.setDisabled(True)
        print('파이슬롯 : ' +  str(status))
        if int(test) == int(status):
            time.sleep(0.5)
            self.progess.hide()
            self.btn.setEnabled(True)
            self.btn_t.setEnabled(True)
            self.btn_s.setEnabled(True)
            self.list_reset.setEnabled(True)
            test = 0

class Window(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        self.list = QListWidget()
        self.te = QLineEdit()
        self.btn = QPushButton('보내기')
        self.btn_f = QPushButton('파일 서버')
        self.btn_c = QPushButton('채팅 서버')
        
        hbox = QHBoxLayout()
        hbox.addWidget(self.te)
        hbox.addWidget(self.btn)

        hbox_b = QHBoxLayout()
        hbox_b.addWidget(self.btn_c)
        hbox_b.addWidget(self.btn_f)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox_b)
        vbox.addWidget(self.list)
        vbox.addLayout(hbox)

        self.setLayout(vbox)

        self.btn_c.setDisabled(True)
        # self.move(300, 300)
        self.resize(600, 400)

        self.btn.clicked.connect(self.msgSend)
        self.te.returnPressed.connect(self.msgSend)
        self.btn_f.clicked.connect(self.ChangeWindow)
        self.btn_f.clicked.connect(self.sig_send)
        
    def sig_send(self):
        check_queue_f.put('f')

    def ChangeWindow(self):
        self.subgui = Sub_Window()
        # self.hide()
        # self.subgui.show()
        self.subgui.setWindowTitle('파일송수신')

    def msgSend(self):
        msg = self.te.text()
        self.te.setText('')
        self.list.addItem('나 : ' + msg)
        self.list.scrollToBottom()
        send_queue.put('Send')
        msg1_queue.put(msg)
        msg2_queue.put(msg)


    @pyqtSlot(str)
    def updateStatus(self, status):
        # print(status)
        self.list.addItem('{}'.format(status))
        self.list.scrollToBottom()


class Example(QObject):

    global selectitem

    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)

        global pos_chat

        self.gui = Window()
        self.subgui = Sub_Window()

        pos_chat = str(self.gui.frameGeometry())

        self.worker = Worker()               # 백그라운드에서 돌아갈 인스턴스 소환
        self.worker_thread = QThread()       # 따로 돌아갈 thread를 하나 생성
        self.worker.moveToThread(self.worker_thread)# worker를 만들어둔 쓰레드에 넣어줍니다
        self.worker_thread.start()           # 쓰레드를 실행합니다.

        self.sub_worker = subWorker()
        self.sub_worker_thread = QThread()
        self.sub_worker.moveToThread(self.sub_worker_thread)
        self.sub_worker_thread.start()

        self.Progress = Progress()
        self.Progress_thread = QThread()
        self.Progress.moveToThread(self.Progress_thread)
        self.Progress_thread.start()

        self._connectSignals()               # 시그널을 연결하기 위한 함수를 호출
        
        self.gui.show()
        self.gui.setWindowTitle('채팅 프로그램')

    def _connectSignals(self):
        
        global cnt
        global cnt2

        self.gui.btn.clicked.connect(self.worker.startWork)
        self.gui.te.returnPressed.connect(self.worker.startWork)
        self.gui.btn_f.clicked.connect(self.changingWindowtoFile)

        self.subgui.list_reset.clicked.connect(self.sub_worker.startList)
        self.subgui.btn.clicked.connect(self.changingWindowtoChat)
        self.subgui.list_g.itemClicked.connect(self.list_sig)
        self.subgui.btn_t.clicked.connect(self.printitem)
        self.subgui.btn_s.clicked.connect(self.uploaditem)
        self.subgui.btn_t.clicked.connect(self.Progress.startProgress)
        self.subgui.btn_s.clicked.connect(self.Progress.startProgress)

        if cnt == 0:
            self.gui.windowTitleChanged.connect(self.worker.startWork)
            cnt += 1
        
        if cnt2 == 0:
            self.subgui.windowTitleChanged.connect(self.sub_worker.startList)
            cnt2 += 1

        self.worker.sig.connect(self.gui.updateStatus)

        self.sub_worker.sig_u.connect(self.subgui.updateStatus_u)

        self.Progress.sig_p_n.connect(self.subgui.Progress_start)
        
        # self.gui.button_cancel.clicked.connect(self.forceWorkerReset)

    def uploaditem(self):
        upload_queue.put('upload')
        
    def printitem(self):
        global getItem

        if select_queue.qsize() == 0 :
            # print(getItem)
            select_queue_ok.put(getItem)
        else :
            getItem = select_queue.get()
            # print(getItem)
            select_queue_ok.put(getItem)

    def list_sig(self):
        selectitem = self.subgui.list_g.selectedItems()

        for item in selectitem:
            while select_queue.qsize() != 0:
                select_queue.get()
            select_queue.put(item.text())

    def changingWindowtoChat(self):

        self.subgui.hide()
        self.gui.show()

    def changingWindowtoFile(self):

        self.gui.hide()
        self.subgui.show()
        self.subgui.list_g.clear()
        self.subgui.setWindowTitle('파일송수신')
        
    def forceWorkerReset(self):
        if self.worker_thread.isRunning():  
            self.worker_thread.terminate()  
            self.worker_thread.wait()       
            self.worker_thread.start() 

if __name__ == "__main__":

    sock_conn = Thread(target=sock_conn,)
    sock_conn.daemon = True
    sock_conn.start()

    file_conn = Thread(target=file_conn, daemon=True)
    file_conn.start()

    app = QApplication(sys.argv)
    example = Example(app)
    sys.exit(app.exec_())