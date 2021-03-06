import select
import socket
import struct
import getch
import time
import threading
import scapy.all
import multiprocessing as mp


class Client:
    # connection properties
    udp_port = 13117
    ip = ""
    name = "Eyal Golan is single\n"
    tcp_port = None

    # style
    CRED = '\033[91m'  # error color start
    CEND = '\033[0m'  # error color end
    SMCS = '\x1b[6;30;42m'
    SMCE = '\x1b[0m'
    GREEN = '\033[32m'

    # trheading tools
    Mutex = threading.Lock()

    def __init__(self, IP):
        '''
        param: ip - the ip address of the client

        initialize ip address and start the UDP function
        '''
        self.ip = IP
        print(self.SMCS + 'Client started, listening for offer requests...' + self.SMCE)
        self.getting_offers()

    def getting_offers(self):
        '''
        Function that will set the udp socket and listen for offers.
        The function will check the packtes arriving and try to unpack them with >IbH format
        If the packet is in the right format its will call the tcp function with the extracted port from the udp packet
        '''

        # getting udp offers
        while True:
            self.Mutex.acquire()
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                s.bind(('172.99.255.255', 13117))
            except Exception as e:
                print(self.CRED + "unable to connect with UDP socket" + self.CEND)
                self.Mutex.release()
                continue

            # getting offers until messege with right ormat arrives
            try:
                data, server = s.recvfrom(1024)
            except Exception as e:
                print(self.CRED + "unable to receive data from socket, connection problem" + self.CEND)
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
                        self.Mutex.release()
                        continue
                else:
                    self.Mutex.release()
                    continue
            else:
                self.Mutex.release()
                continue
                # got tcp port attempting to connect
            s.close()
            self.Mutex.release()
            self.connect_to_server(server[0])

    def get_char(self, return_list):
        '''
        This function will add a char if pressed to the mp Manager list .
        '''

        word = getch.getch()
        return_list.append(word)

    def connect_to_server(self, host_ip):
        '''
        Function which will initiate the TCP connection and will send and receive with the server.
        '''

        self.Mutex.acquire()
        # connecting by tcp to the server
        print(self.SMCS + 'Received offer from ' + host_ip + ' ,attempting to connect...' + self.SMCE)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            addr=(host_ip,self.tcp_port)
            sock.connect(addr)
            print(self.GREEN + "client connection with server established")
        except:
            print(self.CRED + "Unable to create TCP socket with server" + self.CEND)
            self.Mutex.release()
            return
        try:
            # sending the name of the team
            sock.send(self.name.encode())

            data = sock.recv(1024)
            print(data.decode())
            # getting messege from the server (game begin) and prints

            # mp tools
            # Start new process to take char from the console
            manager = mp.Manager()
            return_list = manager.list()
            t = mp.Process(target=self.get_char, args=(return_list,))
            t.start()
            while True:
                # check if any messeges from the server
                r, _, _ = select.select([sock], [], [], 1)
                if r:
                    data = sock.recv(1024)
                    print(data.decode())
                    sock.close()
                    # end game message arrived the socket is closing
                    break
                if return_list:
                    to_send = return_list[0]
                    sock.send(to_send.encode())
                    # sending the answer
                    data = sock.recv(1024)
                    print(data.decode())
                    # reciving the result
                    sock.close()
                    break
            # terminat the input procces
            t.terminate()

        except Exception as e:
            print(self.CRED + 'Server disconnected, listening for offer requests...' + self.CEND)
            print(self.CRED + 'Error - ' + str(e) + self.CEND)

        finally:
            print(self.CRED + 'Server disconnected, listening for offer requests...' + self.CEND)
            self.Mutex.release()


if __name__ == '__main__':
    c = Client(scapy.all.get_if_addr('eth1'))