import select
import socket
import struct
import getch


class Client:
    udp_port = 13117
    name = "AmitAndJuval\n"
    tcp_port = None
    CRED = '\033[91m'  # error color start
    CEND = '\033[0m'  # error color end
    SMCS = '\x1b[6;30;42m'
    SMCE = '\x1b[0m'
    GREEN = '\033[32m'

    def __init__(self):
        self.getting_offers()

    def getting_offers(self):
        complete = True
        # getting udp offers
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            s.bind(('', 13117))
            print(self.SMCS + 'Client started, listening for offer requests...' + self.SMCE)
        except Exception as e:
            print(self.CRED + "unable to connect with UDP socket" + self.CEND)
            complete = False;

        # getting offers until messege with right ormat arrives
        while True:
            try:
                data, server = s.recvfrom(1024)
            except Exception as e:
                print(self.CRED + "unable to receive data from socket, connection problem" + self.CEND)
                complete = False
                break
            # checking that they are in the right format
            try:
                tup = struct.unpack(">IbH", data)
            except Exception as e:
                print(self.CRED + "unable to unapck the data from " + server[0] + " , not in >IbH format" + self.CEND)
                continue
            if len(tup) == 3:
                if tup[0] == 0xabcddcba and tup[1] == 0x2:  # check the condition
                    # exctarting the port
                    if type(tup[2]) is int:
                        self.tcp_port = tup[2]
                        s.close()
                        break
        # got tcp port attempting to connect
        if complete:
            self.connect_to_server(server[0])
            return
        # else:
        # self.getting_offers();

    def connect_to_server(self, host_ip):
        # connectiong by tcp to the server
        print(self.SMCS + 'Received offer from ' + host_ip + ' ,attempting to connect...' + self.SMCE)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host_ip, self.tcp_port))
            print(self.GREEN + "client connection with server established")

            # sending the name of the team
            sock.send(self.name.encode())

            data = sock.recv(1024)
            print(data.decode())
            # getting messege from the server (game begin) and prints
            while True:
                r, _, _ = select.select([sock], [], [], 1)
                if r:
                    data = sock.recv(1024)
                    print(data.decode())
                    break
                read = getch()
                sock.send(read.decode())
                data = sock.recv(1024)
                if data:
                    print(data.decode())
                    break


        except Exception as e:
            print(self.CRED + 'Server disconnected, listening for offer requests...' + self.CEND)
            # maybe need to close the socket ?
            # looking for the tcp connection to close by the sever and prints that the connection closed
            # returning to getting_offers function
        finally:
            self.getting_offers()


if __name__ == '__main__':
    c = Client()
