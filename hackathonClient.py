import socket
import struct


class Client:
    IP=""
    udp_port=13117
    name="AmitAndJuval\n"
    tcp_port=None
    
    def __init__(self,ip):
        self.IP=ip
        #self.getting_offers()
    


    def getting_offers(self):
        #getting udp offers
        print('Client started, listening for offer requests...')
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        s.bind(('',13117)) # maybe self.IP  --> is it no eth0/1?
        data, server = s.recvfrom(1024)
        #checking that they are in the right format
        tup = struct.unpack("", data)
        if tup[0]=="0xabcddcba" and tup[1]=="0x2":
            #exctarting the port
            self.tcp_port=tup[2]
        s.close()
        #activate the connect_to_server function
        self.connect_to_server()

        
        
        

    def connect_to_server(self):
        #connectiong by tcp to the server
        print('Received offer from 172.1.0.4,attempting to connect...')
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host_ip, port)) #dont know the host_ip
        
            #sending the name of the team
            s.send(self.name.encode())
        
            data=s.recv(1024)
            #getting messege from the server (game begin) and prints

            answer=input(data.decode())
            #sending char to the server while keep on listiong for messeges

            s.send(answer.encode())
            
            data=s.recv(1024)
            print(data.decode())
        except:
            print('Server disconnected, listening for offer requests...')
            self.getting_offers()
        #looking for the tcp connection to close by the sever and prints that the connection closed
        #returning to getting_offers function
    

    
    
    