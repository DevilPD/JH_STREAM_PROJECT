from socket import *
import threading
from queue import Queue
import time
import os
from os.path import getsize
import select
import os.path

count = 0
cnt = 0

msg_queue = Queue()

# def end_sig(conn_d):
#     try:
#         while True:
#             msg = send_queue_d.get()
            
#             if(msg == 'End'):
#                 thread2_d = threading.Thread(target=Recv_d, args=(conn_d, count, send_queue_d,))
#                 thread2_d.daemon = True
#                 thread2_d.start()
#     except Exception as e:
#         print(e)
#         pass

def getFile(u_socket, addr):
    data = 0
    data_transferred = 0
    print(str(addr) + '에서 업로드를 시도하고 있습니다.')
    filename = u_socket.recv(1024)
    print('업로드할 파일 이름 : ' + filename.decode('utf-8'))
    u_socket.send('ok'.encode())

    nowdir = os.getcwd()
    print('파일 다운 시작..')
    try:
        with open(nowdir + "\\Files\\" + filename.decode('utf-8'), 'wb') as f:  # 현재dir에 filename으로 파일을 받는다
            try:
                data = u_socket.recv(1024)
                while data:  # 데이터가 있을 때까지
                    f.write(data)  # 1024바이트 쓴다
                    data_transferred += len(data)
                    data = u_socket.recv(1024)  # 1024바이트를 받아 온다
                    print('현재 다운량: ' + str(round(data_transferred / 1048576, 3)) + 'MB') # round(data_transferred / 1048576, 1)
            except Exception as ex:
                print('1')
                print(ex)
                pass
    except Exception as e:
        print('2')
        print(e)

    print('파일 %s 받기 완료. 전송량 %d' % (filename,data_transferred))
    u_socket.close()
    print("접속을 종료합니다.")
    


def upload_f():
    print('Thread Upload Start')
    host = ''
    port = 12345
    try:
        upload_socket = socket(AF_INET, SOCK_STREAM)
        upload_socket.bind((host, port))
        upload_socket.listen(10)
        print('업로드 서버가 성공적으로 열렸습니다!')

        while True:
            u_socket, addr = upload_socket.accept()

            try:
                thread_getFile = threading.Thread(target=getFile, args=(u_socket, addr), daemon=True)
                thread_getFile.start()
            except Exception as e:
                print(e)
                break

    except Exception as e:
        print(e)


def Send_f():
    print('Thread Send for download Start')
    try:
        folder = os.getcwd()
        msg = msg_queue.get()
        print(msg)

        host = ''
        port_d = 23456
        data_transferred = 0

        download_socket = socket(AF_INET, SOCK_STREAM)
        download_socket.bind((host, port_d))
        download_socket.listen(1)
        print('다운로드 서버가 성공적으로 열렸습니다!')

        d_socket, addr = download_socket.accept()
        
        filename = (folder + '\\Files\\' + msg)
        size = getsize(filename)
        print('용량 : ' + str(size))
        d_socket.send(str(size).encode())

        sig = d_socket.recv(1024)
        print(sig.decode())

        try:
            with open(filename, 'rb') as f:
                try:
                    data = f.read(1024) #1024바이트 읽는다
                    while data: #데이터가 없을 때까지
                        data_transferred += d_socket.send(data) #1024바이트 보내고 크기 저장
                        data = f.read(1024) #1024바이트 읽음
                except Exception as ex:
                    print(ex)
            
            print("전송완료 %s, 전송량 %d" %(filename, data_transferred))
            print('클라이언트와의 접속을 종료합니다.')
            download_socket.close()
        
        except Exception as e:
            print(e)
            download_socket.close()

        
    ###    
    except Exception as e:
        print(e)
        download_socket.close()
        pass

def FileInfoGet():

    UDP_IP = ""
    IN_PORT = 30033

    sock = socket(AF_INET, SOCK_DGRAM)
    sock.bind((UDP_IP, IN_PORT)) #서버

    print('Thread For FileInfoGet Start')

    while True:
        try:
            print('Ready FileInfo from client..')
            data, addr = sock.recvfrom(1024)
            print('data Recv')
            msg = data.decode('utf-8')
            msg_queue.put(msg)
            
            send_f = threading.Thread(target=Send_f, daemon=True)
            send_f.start()
        except Exception as e:
            print(e)
            sock.close()
    sock.close()
        

def FileInfo():

    UDP_IP = ""
    IN_PORT = 10011
    folder = os.getcwd()

    try:
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.bind((UDP_IP, IN_PORT)) #서버
    except Exception as e:
        print(e)
        pass

    print('Thread For FileInfo Start')

    while True:
        i = 0
        info = []
        data, addr = sock.recvfrom(1024)
        msg = data.decode('utf-8')

        if(msg != 'f'):
            print('data 받음 : ' + data.decode('utf-8'))
            ## 여기가 업로드 신호 받는 곳 예정 ##
        else:
            for filename in os.listdir(folder + '\\Files\\'):
                ext=filename.split('.')[-1]
                i += 1
                info.append(filename)
            nm = str(i).encode()
            sock.sendto(nm, addr)
            for s in info :
                try:
                    print('정보 보내기 시작')
                    sock.sendto(s.encode(), addr)
                    print(s)
                except Exception as e:
                    print(e)
                    sock.close()
                    break
    sock.close()


def Send(group, send_queue):
    print('Thread Send for chat Start')
    while True:
        try:
            recv = send_queue.get()
            if recv == 'New':
                print('새 그룹을 만듭니다.')
                break

            for conn in group:
                msg = 'Client' + str(recv[2]) + '>>>' + str(recv[0]) # recv[2] 에는 보낸 클라이언트 이름 ,recv[0] 에는 보낸 내용

                if recv[1] != conn:
                    conn.send(bytes(msg.encode()))
                else:
                    print(msg)
                    pass

        except Exception as e:

            print(group)
            print(e)
            pass


def Recv(conn, count, send_queue):

    print('Thread Recv for chat ' + str(count) + ' Start')
    while True:
        try:
            data = conn.recv(1024).decode()
            send_queue.put([data, conn, count])
            print('받은 데이터 send 쓰레드로 이동')
        except:
            print(addr, '와의 연결이 끊겼습니다.')
            print(conn)
            del group[0]
            count = count - 1
            break

if __name__ == '__main__':

    send_queue = Queue()
    host = ''
    port = 20022
    people = 10
    group = []

    try:
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(people)
        print('채팅 서버가 성공적으로 열렸습니다! 최대 접속 가능 인원수 : ', people)
        
    except Exception as e:
        print(e)
        server_socket.close()

    try:
        thread_i = threading.Thread(target=FileInfo, daemon=True)
        thread_i.start()

        thread_f = threading.Thread(target=FileInfoGet, daemon=True)
        thread_f.start()

        thread_u = threading.Thread(target=upload_f, daemon=True)
        thread_u.start()



        while True:
            count = count + 1

            try:
                conn, addr = server_socket.accept()
            except Exception as e:
                print(e)

            group.append(conn)
            # group_d.append(conn_d)
            print('####################################')
            print(str(addr) + ' join the server.')
            print('채팅소켓 : ' + str(addr))
            # print('다운소켓 : ' + str(addr_d))

            if count > 1:
                send_queue.put('New')
                # send_queue_d.put('New')
                thread1 = threading.Thread(target=Send, args=(group, send_queue,))
                thread1.start()
                pass
            else:
                thread1 = threading.Thread(target=Send, args=(group, send_queue,))
                thread1.start()

            
            thread2 = threading.Thread(target=Recv, args=(conn, count, send_queue,))
            thread2.daemon = True
            thread2.start()

    except Exception as e:
        print(e)