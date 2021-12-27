import socket
import threading
import time
import scapy.all
import struct


class Server:
    Port = 2006
    udp_dest = 13117
    eth1 = '172.0.0/24'
    eth0 = '172.99.0/24'
    name1 = None
    name2 = None
    answer1=None
    answer2=None
    grand_answer="8"
    winner = None
    begin_game = threading.Lock()
    ber = threading.Barrier(2)
    check = threading.Lock()

    def __init__(self, ip):
        self.Ip = ip
        self.start()

    def start(self):
        print('Server started, listening on IP address ' + self.Ip)
        udp_thread = threading.Thread(target=self.start_server_udp)
        # start upd
        tcp_thread = threading.Thread(target=self.start_server_tcp)
        # start tcp
        udp_thread.start()
        tcp_thread.start()




    def start_server_udp(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        # Enable broadcasting mode
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # UDP
        # sock.bind((self.Ip, self.Port))
        bytes_to_send = struct.pack(">IbH", 0xabcddcba, 0x2, self.Port)
        # need to see how you can send byte or string?!

        while not self.begin_game.locked():
            # while the tcp thread did not said that the game started
            sock.sendto(bytes_to_send, ("<broadcast>", self.udp_dest))
            # send offer
            time.sleep(1)
            # sleep
        sock.close()




    def start_server_tcp(self):

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.Ip, self.Port))
        s.listen(2)
        while True:
            self.winner = None
            self.ber=threading.Barrier(2)
            is_empty = True  # no even one player
            is_full = False  # all the players arrived the game can begin
            while not is_full:
                if is_empty:
                    conn, addr = s.accept()
                    player1 = threading.Thread(target=self.handle_client1, args=(conn,))
                    is_empty = False
                    player1.start()

                else:
                    conn, addr = s.accept()
                    player2 = threading.Thread(target=self.handle_client2, args=(conn,))
                    is_full = True
                    player2.start()


            self.begin_game.acquire()  # change the lock to locked the udp loop will stop
            player1.join()
            player2.join()

            print('Server started, listening on IP address ' + self.Ip)
            self.begin_game.release()
            udp_thread = threading.Thread(target=self.start_server_udp)
            udp_thread.start()








    def receive_char1(self,conn):
        try:
            self.answer1 = conn.recv(1024).decode()
            print("client1: answer is "+self.answer1)
        except Exception as e:
            print("")
        self.check.acquire()
        if self.winner is None:
            print("Client1: changing the winner")
            if self.grand_answer==self.answer1:
                self.winner=self.name1
            else:
                self.winner=self.name2
        self.check.release()



    def receive_char2(self, conn):
        try:
            self.answer2 = conn.recv(1024).decode()
            print("client2: answer is "+self.answer2)
        except Exception as e:
            print("")
        self.check.acquire()
        if self.winner is None:
            print("Client1: changing the winner")
            if self.grand_answer == self.answer2:
                self.winner = self.name2
            else:
                self.winner=self.name1
        self.check.release()





    def handle_client1(self, conn):
        try:
            self.answer1=None
            self.name1 = conn.recv(1024).decode()
            self.ber.wait()  # wait for the other thread to arrive to this point
            msg = 'Welcome to Quick Maths\nPlayer 1: ' + self.name1 + 'Player 2: ' + self.name2 + '==\nPlease answer the following question as fast as you can:\nHow much is 7+1?\n'
            conn.send(msg.encode())  # sends the message
        except Exception as e:
            print("Lost connection to the client")
        # start counting 10 seconds if no data reviced then send draw message
        timer = time.time();
        end_timer=time.time();
        try:
            ans = threading.Thread(target=self.receive_char1, args=(conn,))
            ans.start()
            print("Client 1: thread activated")
        except Exception as e :
            print("error with the receive thread on client 1")

        while self.winner is None and (end_timer-timer<10.0):
            end_timer=time.time();
        try:
            if end_timer-timer>=10.0:
                conn.send(('Game over!\nThe correct answer was 8\n\nits a DREW \n').encode())
                conn.close()
            else:
                conn.send(('Game over!\nThe correct answer was 8\n\nCongratulations to the winner: ' + self.winner + '\n').encode())
                conn.close()
            # send summery and close the socket
        except Exception as e:
            print("Lost connection to the client")




    def handle_client2(self, conn):
        try:
            self.answer2=None
            self.name2 = conn.recv(1024).decode()
            self.ber.wait()  # the game can start if both threads are here
            msg = 'Welcome to Quick Maths\nPlayer 1: ' + self.name1 + 'Player 2: ' + self.name2 + '==\nPlease answer the following question as fast as you can:\nHow much is 7+1?\n'
            conn.send(msg.encode())
        except Exception as e:
            print("Lost connection to the client")

        # start counting 10 seconds if no data reviced then send draw message
        timer = time.time();
        end_timer = time.time();
        try:
            ans = threading.Thread(target=self.receive_char2, args=(conn,))
            ans.start()
            print("Client 2: thread activated")

        except Exception as e :
            print("error with the receive thread on client 2")

        while self.winner is None and (end_timer - timer < 10.0):
            end_timer = time.time();
        try:
            if end_timer - timer >= 10.0:
                conn.send(('Game over!\nThe correct answer was 8\n\nits a DREW \n').encode())
                conn.close()
            else:
                # send summery and close the socket
                conn.send(('Game over!\nThe correct answer was 8\n\nCongratulations to the winner: ' + self.winner + '\n').encode())
                conn.close()
        except Exception as e:
            print("Lost connection to the client")

if __name__ == '__main__':
    #s=Server("10.100.102.6")
    s = Server(scapy.all.get_if_addr('172.0.0/24'))