import socket
import threading
import time
import scapy.all
import struct
import random



class Server:
    # connection attributes
    Port = 2006
    udp_dest = 13117


    # style attributes
    CRED = '\033[91m' # error color start
    CEND = '\033[0m' # error color end
    SMCS='\x1b[6;30;42m'
    SMCE='\x1b[0m'

    # game attributes
    name1 = None
    name2 = None
    answer1=None
    answer2=None
    bank=[("dogs legs + humen eyes? ","6"),("6+2?","8"),("100-99?","1"),("the sum of all digit in the year we found about CoronaVirus?","4")]
    grand_answer=""
    question=""
    winner = None

    # concurconcy objects
    begin_game = threading.Lock()
    check = threading.Lock()
    ber = threading.Barrier(2)


    def __init__(self, ip):
        self.Ip = ip
        self.start()

    def start(self):
        print('\x1b[6;30;42m' + 'Server started, listening on IP address ' + self.Ip+ '\x1b[0m')
        udp_thread = threading.Thread(target=self.start_server_udp)
        # start upd
        tcp_thread = threading.Thread(target=self.start_server_tcp)
        # start tcp
        udp_thread.start()
        tcp_thread.start()




    def start_server_udp(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Enable broadcasting mode
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            # UDP
            bytes_to_send = struct.pack(">IbH", 0xabcddcba, 0x2, self.Port)
            # need to see how you can send byte or string?!

            while True:
                self.begin_game.acquire()
                # while the tcp thread did not said that the game started
                sock.sendto(bytes_to_send, ("<broadcast>", self.udp_dest))
                print("Just sent Brodcast over UDP ")
                self.begin_game.release()
                # send offer
                time.sleep(2)
                # sleep
            sock.close()
        except Exception as e:
            print(self.CRED+'unable to connect with UDP socket'+self.CEND)




    def start_server_tcp(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print((self.Ip, self.Port))
            s.bind((self.Ip, self.Port))
            s.listen(5)
            print("TCP socket connection runing, listening to requests...")
        except:
            print(self.CRED+'Unable to create TCP socket'+self.CEND)
        while True:
            self.winner = None
            self.ber=threading.Barrier(2)
            is_empty = True  # no even one player
            is_full = False  # all the players arrived the game can begin
            while not is_full:
                r=random.randint(0,len(self.bank)-1)
                self.question, self.grand_answer=self.bank[r]
                if is_empty:
                    print("waiting for client 1")
                    conn, addr = s.accept()
                    print("client 1 accepted")
                    player1 = threading.Thread(target=self.handle_client1, args=(conn,))
                    is_empty = False
                    player1.start()
                    print("thread started - client1")

                else:
                    print("waiting for client 2")
                    conn, addr = s.accept()
                    print("client 2 accepted")
                    player2 = threading.Thread(target=self.handle_client2, args=(conn,))
                    is_full = True
                    player2.start()
                    print("thread started - client2")



            self.begin_game.acquire()  # change the lock to locked the udp loop will stop
            player1.join()
            print('client 1 thread finished')
            player2.join()
            print('client 2 thread finished')
            self.begin_game.release()
            print('\x1b[6;30;42m' + 'Server started, listening on IP address ' + self.Ip+ '\x1b[0m')









    def receive_char1(self,conn):
        try:
            self.answer1 = conn.recv(1024).decode()
        except Exception as e:
            pass
        self.check.acquire()
        if self.winner is None:
            if self.grand_answer==self.answer1:
                self.winner=self.name1
            else:
                self.winner=self.name2
        self.check.release()



    def receive_char2(self, conn):
        try:
            self.answer2 = conn.recv(1024).decode()
        except Exception as e:
            pass
        self.check.acquire()
        if self.winner is None:
            if self.grand_answer == self.answer2:
                self.winner = self.name2
            else:
                self.winner=self.name1
        self.check.release()





    def handle_client1(self, conn):
        try:
            self.answer1=None
            self.name1 = conn.recv(1024).decode()
            print("Client 1 has accepted: "+self.name1)
            self.ber.wait()  # wait for the other thread to arrive to this point
            msg = 'Welcome to Quick Maths\nPlayer 1: ' + self.name1 + 'Player 2: ' + self.name2 + '==\nPlease answer the following question as fast as you can:\nHow much is '+self.question
            conn.send(msg.encode())  # sends the message
        except Exception as e:
            print(self.CRED+'Lost connection to the client'+self.CEND)
        # start counting 10 seconds if no data reviced then send draw message
        timer = time.time()
        end_timer=time.time()
        try:
            ans = threading.Thread(target=self.receive_char1, args=(conn,))
            ans.start()
        except Exception as e :
            print(self.CRED+"error with the receive thread on client 1"+self.CEND)

        while self.winner is None:
            end_timer=time.time()
            time.sleep(1)
            if end_timer - timer > 10.0:
                break

        try:
            if end_timer-timer>=10.0:
                conn.send(('Game over!\nThe correct answer was '+self.grand_answer+ '\n\nits a '+self.SMCS+'DREW' +self.SMCE+'\n').encode())
                conn.close()
            else:
                conn.send(('Game over!\nThe correct answer was '+self.greand_answer+ '\n\nCongratulations to the winner: ' +self.SMCS+self.winner +self.SMCE+ '\n').encode())
                conn.close()
            # send summery and close the socket
        except Exception as e:
            print(self.CRED+"Lost connection to the client"+self.CEND)




    def handle_client2(self, conn):
        try:
            self.answer2=None
            self.name2 = conn.recv(1024).decode()
            print("Client 2 has accepted: "+self.name2)
            self.ber.wait()  # the game can start if both threads are here
            msg = 'Welcome to Quick Maths\nPlayer 1: ' + self.name1 + 'Player 2: ' + self.name2 + '==\nPlease answer the following question as fast as you can:\nHow much is '+self.question
            conn.send(msg.encode())
        except Exception as e:
            print(self.CRED+"Lost connection to the client"+self.CEND)

        # start counting 10 seconds if no data reviced then send draw message
        timer = time.time()
        end_timer = time.time()
        try:
            ans = threading.Thread(target=self.receive_char2, args=(conn,))
            ans.start()

        except Exception as e :
            print(self.CRED+"error with the receive thread on client 2"+self.CEND)
        print("entering clock while:")

        while self.winner is None :
            end_timer = time.time()
            time.sleep(1)
            if end_timer - timer > 10.0:
                break
        try:
            if end_timer - timer >= 10.0:
                conn.send(('Game over!\nThe correct answer was '+self.grand_answer+'\n\nits a '+self.SMCS+'DREW' +self.SMCE+'\n').encode())
                conn.close()
            else:
                # send summery and close the socket
                conn.send(('Game over!\nThe correct answer was '+self.grand_answer+'\n\nCongratulations to the winner: ' +self.SMCS+self.winner +self.SMCE+ '\n').encode())
                conn.close()
        except Exception as e:
            print(self.CRED+"Lost connection to the client"+self.CEND)



if __name__ == '__main__':
    s = Server(scapy.all.get_if_addr('eth1'))