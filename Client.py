import socket
import struct


class Client:
    udp_port = 13117
    name = "AmitAndJuval\n"
    tcp_port = None

    def __init__(self):
        self.getting_offers()

    def getting_offers(self):
        # getting udp offers
        print('Client started, listening for offer requests...')
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        s.bind(('', 13117))

        # getting offers until messege with right ormat arrives
        while True:
            data, server = s.recvfrom(1024)
            # checking that they are in the right format
            tup = struct.unpack(">IbH", data)
            if tup[0] == 0xabcddcba and tup[1] == 0x2:  # check the condition
                # exctarting the port
                self.tcp_port = tup[2]
                s.close()
                break
        # got tcp port attempting to connect
        self.connect_to_server(server[0])

    def connect_to_server(self, host_ip):
        # connectiong by tcp to the server
        print('Received offer from ' + host_ip + ' ,attempting to connect...')
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host_ip, self.tcp_port))
            print("client connection with server established")

            # sending the name of the team
            sock.send(self.name.encode())

            data = sock.recv(1024)
            print(data.decode())
            # getting messege from the server (game begin) and prints

            answer = input()
            sock.send(answer.encode())
            # sending char to the server while keep on listiong for messeges

            data = sock.recv(1024)
            print(data.decode())
            # gettng winner messege from server and prints
        except Exception as e:
            print('Server disconnected, listening for offer requests...')
            print(e)
            # maybe need to close the socket ?
            # looking for the tcp connection to close by the sever and prints that the connection closed
            # returning to getting_offers function
        finally:
            self.getting_offers()


if __name__ == '__main__':
    c=Client()
