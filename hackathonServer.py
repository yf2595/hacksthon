import socket
import threading
import time
import scapy # used to get the ip address like in the instroctions
import struct

class Server:
    Port=2006
    udp_dest=13117
    eth1='172.0.0/24'
    eth0='172.99.0/24'
    name1=None
    name2=None
    winner=None
    begin_game=threading.Lock()
    ber=threading.Barrier(2)
    check = threading.Lock()
    finish = False
    
    
    def __init__(self,ip):
        self.Ip=ip
        self.start()
    
    def start(self):
        print('Server started, listening on IP address '+self.Ip) 
        udp_thread=threading.Thread(target=self.start_server_udp) #start upd
        tcp_thread=threading.Thread(target=self.start_server_tcp) #start tcp
        udp_thread.start()
        tcp_thread.start()

        
    
    def start_server_udp(self):
        sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) #UDP 
        sock.bind((self.Ip, self.Port))
        bytes_to_send=struct.pack(">IbH",0xabcddcba,0x2,self.Port) #need to see how you can send byte or string?!
        
        while not self.begin_game.locked(): #while the tcp thread did not said that the game started
            sock.sendto(bytes_to_send,("<broadcast>",self.udp_dest)) # send offer
            time.sleep(1) # sleep
        sock.close()    
            
            
            
    def start_server_tcp(self):
        self.winner = None
        self.finish = False
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.Ip, self.Port))
        
        while True:
            s.listen()
            
            is_empty=True #no even one player
            is_full=False #all the players arrived the game can begin
            
            while not is_full:
                if is_empty:
                    conn, addr = s.accept()
                    player1=threading.Thread(target=self.handle_client1, args=(conn,))
                    is_empty=False
                    player1.start()
                    
                else:
                    conn, addr = s.accept()
                    player2=threading.Thread(target=self.handle_client2, args=(conn,))
                    is_full=True
                    player2.start()
                    
            self.begin_game.acquire() # change the lock to locked the udp loop will stop 
            
          
    def handle_client1(self,conn):
        self.name1 = conn.recv(1024)
        self.ber.wait() # wait for the other thread to arrive to this point
        msg='Welcome to Quick Maths\nPlayer 1: '+self.name1+'Player 2: '+self.name2+'==\nPlease answer the following question as fast as you can:\nHow much is 7+1?\n'
        conn.send(msg.encode()) #sends the message
        #start counting 10 seconds if no data reviced then send draw message   
        timer = threading.Timer(10.0)
        timer.start()
        while(self.winner == None and not timer.finished()):
            try:
                conn.settimeout(1)
                data=conn.recv(1024)
                data=data.decode()
                break;
            except:
                continue
                

        if(timer.finished()):
            self.finish = True
        #check the answer and decide if winneer
        if(not self.finish):
            self.check.acquire()
            if(self.winner == None):
                if data=='8':
                    self.winner=self.name1
                else:
                    self.winner=self.name2
                self.check.release()
        else:
            self.winner = "draw"
        #send summery and close the socket
        conn.send(('Game over!\nThe correct answer was 8\n\nCongratulations to the winner: '+self.winner+'\n').encode())
        conn.close()




    def handle_client2(self,conn):
        self.name2 = conn.recv(1024)
        self.ber.wait() #the game can start if both threads are here
        msg='Welcome to Quick Maths\nPlayer 1: '+self.name1+'Player 2: '+self.name2+'==\nPlease answer the following question as fast as you can:\nHow much is 7+1?\n'
        conn.send(msg.encode())
        
        #start counting 10 seconds if no data reviced then send draw message   
        timer = threading.Timer(10.0)
        timer.start()
        while(self.winner == None and not timer.finished()):
            try:
                conn.settimeout(1)
                data=conn.recv(1024)
                data=data.decode()
                break;
            except:
                continue

        if(timer.finished()):
            self.finish = True
        #check the answer and decide if winneer
        if(not self.finish):
            self.check.acquire()
            if(self.winner == None):
                if data=='8':
                    self.winner=self.name2
                else:
                    self.winner=self.name1
                self.check.release()
        else:
            self.winner = "draw"
        #send summery and close the socket
        conn.send(('Game over!\nThe correct answer was 8\n\nCongratulations to the winner: '+self.winner+'\n').encode())
        conn.close()
        self.begin_game.release()
        

serv=Server("127.0.0.1")
        
#maybe make a winner function with lock and some boolean variable to know if someone was there?    
#need to make sure after closing both sockets that the udp function will start again on different thread.
