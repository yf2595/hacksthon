import select
import socket
import struct
import getch
import time
import threading
import scapy.all


class Client:
    udp_port = 13117
    ip = ""
    name = "AmitAndJuval\n"
    tcp_port = None
    CRED = '\033[91m'  # error color start
    CEND = '\033[0m'  # error color end
    SMCS = '\x1b[6;30;42m'
    SMCE = '\x1b[0m'
    GREEN = '\033[32m'
    Mutex = threading.Lock()
    w = []

    def __init__(self, IP):
        self.ip = IP
        print(self.SMCS + 'Client started, listening for offer requests...' + self.SMCE)
        self.getting_offers()

    def getting_offers(self):
        # getting udp offers
        while True:
            complete = True
            self.Mutex.acquire()
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                s.bind(('', 13117))
            except Exception as e:
                print(self.CRED + "unable to connect with UDP socket" + self.CEND)
                complete = False;
                self.Mutex.release()
                continue

            # getting offers until messege with right ormat arrives
            try:
                data, server = s.recvfrom(1024)
            except Exception as e:
                print(self.CRED + "unable to receive data from socket, connection problem" + self.CEND)
                complete = False
                self.Mutex.release()
                continue
            # checking that they are in the right format
            try:
                tup = struct.unpack(">IbH", data)
            except Exception as e:
                print(self.CRED + "unable to unapck the data from " + server[0] + " , not in >IbH format" + self.CEND)
                self.Mutex.release()
                continue
            if len(tup) == 3:
                if tup[0] == 0xabcddcba and tup[1] == 0x2:  # check the condition
                    # exctarting the port
                    if type(tup[2]) is int:
                        self.tcp_port = tup[2]
                        s.close()
                    else:
                        complete = False
                        self.Mutex.release()
                        continue
                else:
                    complete = False
                    self.Mutex.release()
                    continue
            else:
                complete = False
                self.Mutex.release()
                continue
                # got tcp port attempting to connect
            if complete:
                s.close()
                self.Mutex.release()
                self.connect_to_server(server[0])

    def get_char():
        word = input()
        self.w.append(word)

    def connect_to_server(self, host_ip):
        self.Mutex.acquire()
        # connectiong by tcp to the server
        print(self.SMCS + 'Received offer from ' + host_ip + ' ,attempting to connect...' + self.SMCE)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            addr = ('172.1.0.6', self.tcp_port)
            # addr=(host_ip,self.tcp_port)
            print(addr)
            sock.connect(addr)
            print(self.GREEN + "client connection with server established")
        except:
            print(self.CRED + "Unable to create TCP socket with server" + self.CEND)
            self.Mutex.release()
            return
            # sending the name of the team
        try:
            sock.send(self.name.encode())

            data = sock.recv(1024)
            print(data.decode())
            # getting messege from the server (game begin) and prints
            self.w = []
            t = threading.Thread(target=self.get_char)
            t.start()
            while True:
                r, _, _ = select.select([sock], [], [])
                if r:
                    data = sock.recv(1024)
                    print(data.decode())
                    sock.close()
                    break
                if len(self.w) > 0:
                    sock.send(self.w[0])
                    data = sock.recv(1024)
                    print(data.decode())
                    sock.close()

            # while read==b'':
            #     r, _, _ = select.select([sock], [], [])
            #     if r:
            #         data = sock.recv(1024)
            #         print(data.decode())
            #         recived=True
            #         break
            #     read=getch()
            # if not recived:
            #     sock.send(read)
            #     data = sock.recv(1024)
            #     print(data.decode())


        except Exception as e:
            print(self.CRED + 'Server disconnected, listening for offer requests...' + self.CEND)
            print(e)
            # maybe need to close the socket ?
            # looking for the tcp connection to close by the sever and prints that the connection closed
            # returning to getting_offers function
        finally:
            self.Mutex.release()


if __name__ == '__main__':
    c = Client(scapy.all.get_if_addr('eth1'))
