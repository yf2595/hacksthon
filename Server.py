import socket
import threading
import time
# import scapy # used to get the ip address like in the instroctions
import struct


class Server:
    Port = 2006
    udp_dest = 13117
    eth1 = '172.0.0/24'
    eth0 = '172.99.0/24'
    name1 = None
    name2 = None
    winner = None
    begin_game = threading.Lock()
    ber = threading.Barrier(2)
    check = threading.Lock()
    finish = False

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
            self.finish = False
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
            print(self.begin_game.locked())
            player1.join()
            print("first player finished")
            player2.join()
            print("second client finished")

            print('Server started, listening on IP address ' + self.Ip)
            self.begin_game.release()
            udp_thread = threading.Thread(target=self.start_server_udp)
            udp_thread.start()


    def handle_client1(self, conn):
        self.name1 = conn.recv(1024).decode()
        print(self.name1)
        self.ber.wait()  # wait for the other thread to arrive to this point
        msg = 'Welcome to Quick Maths\nPlayer 1: ' + self.name1 + 'Player 2: ' + self.name2 + '==\nPlease answer the following question as fast as you can:\nHow much is 7+1?\n'
        conn.send(msg.encode())  # sends the message
        # start counting 10 seconds if no data reviced then send draw message
        timer = time.time();
        end_timer=time.time();
        while self.winner is None and (end_timer-timer<10.0):
            try:
                # conn.settimeout(1)
                data = conn.recv(1024)
                data = data.decode()
                break;
            except Exception as e:
                print("this is the time out exception")
                print(e)
            finally:
                end_timer=time.time();

        if end_timer-timer>=10.0:
            self.finish = True
        # check the answer and decide if winneer
        if not self.finish:
            self.check.acquire()
            if self.winner is None:
                if data == '8':
                    self.winner = self.name1
                else:
                    self.winner = self.name2
            self.check.release()
        else:
            if self.winner is None:
                self.winner = "draw"
        # send summery and close the socket
        conn.send(
            ('Game over!\nThe correct answer was 8\n\nCongratulations to the winner: ' + self.winner + '\n').encode())
        conn.close()

    def handle_client2(self, conn):
        self.name2 = conn.recv(1024).decode()
        self.ber.wait()  # the game can start if both threads are here
        msg = 'Welcome to Quick Maths\nPlayer 1: ' + self.name1 + 'Player 2: ' + self.name2 + '==\nPlease answer the following question as fast as you can:\nHow much is 7+1?\n'
        conn.send(msg.encode())

        # start counting 10 seconds if no data reviced then send draw message
        timer = time.time();
        end_timer = time.time();
        while self.winner is None and (end_timer - timer < 10.0):
            try:
                # conn.settimeout(1)
                data = conn.recv(1024)
                data = data.decode()
                break;
            except Exception as e:
                print("this is the time out exception")
                print(e)
                continue
            finally:
                end_timer = time.time();

        if end_timer - timer >= 10.0:
            self.finish = True
        # check the answer and decide if winneer
        if not self.finish:
            self.check.acquire()
            if self.winner is None:
                if data == '8':
                    self.winner = self.name2
                else:
                    self.winner = self.name1
            self.check.release()
        else:
            if self.winner is None:
                self.winner = "draw"
        # send summery and close the socket
        conn.send(
            ('Game over!\nThe correct answer was 8\n\nCongratulations to the winner: ' + self.winner + '\n').encode())
        conn.close()


if __name__ == '__main__':
    s=Server("10.100.102.6")

# maybe make a winner function with lock and some boolean variable to know if someone was there?
# need to make sure after closing both sockets that the udp function will start again on different thread.
