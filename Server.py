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
    CRED = '\033[91m'  # error color start
    CEND = '\033[0m'  # error color end
    SMCS = '\x1b[6;30;42m'
    SMCE = '\x1b[0m'

    # game attributes
    name1 = None
    name2 = None
    answer1 = None
    answer2 = None
    bank = [("dogs legs + humen eyes? ", "6"), ("6+2?", "8"), ("100-99?", "1"),
            ("the sum of all digit in the year we found about CoronaVirus?", "4")]
    grand_answer = ""
    question = ""
    winner = None
    brod = ""

    # concurconcy objects
    begin_game = threading.Lock()
    check = threading.Lock()
    ber = threading.Barrier(2)

    # statistics
    total_played = 0

    def __init__(self, ip):
        '''
        Function thet sets the IP address and calls for start function to initate the connections.
        '''
        self.Ip = ip
        lst = self.Ip.split(".")
        self.brod = lst[0] + '.' + lst[1] + '.' + '255.255'
        self.total_played = 0
        self.start()
        # start the server

    def start(self):
        '''
        Function that will initaite 2 new threads one for UDP conn and TCP conn
        '''
        print('\x1b[6;30;42m' + 'Server started, listening on IP address ' + self.Ip + '\x1b[0m')

        udp_thread = threading.Thread(target=self.start_server_udp)
        # start upd

        tcp_thread = threading.Thread(target=self.start_server_tcp)
        # start tcp

        udp_thread.start()
        tcp_thread.start()

    def start_server_udp(self):
        '''
        Function that starts the UDP socket and sends offers in >IbH format
        '''
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Enable broadcasting mode
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            # UDP
            bytes_to_send = struct.pack(">IbH", 0xabcddcba, 0x2, self.Port)
            # sending packege with magi cookie, offer request and tcp port6

            while True:
                self.begin_game.acquire()
                # while the tcp thread did not said that the game started
                sock.sendto(bytes_to_send, (self.brod, self.udp_dest))
                print("Just sent Brodcast over UDP ")
                self.begin_game.release()
                # send offer
                time.sleep(2)
                # sleep
            sock.close()

        except Exception as e:
            print(self.CRED + 'unable to connect with UDP socket' + self.CEND)
            print(self.CRED + "Error description : " + str(e) + self.CEND)

    def start_server_tcp(self):
        '''
        Function that initaite the tcp socket and listen for clients
        Creates 2 new threads - one for each client
        '''
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((self.Ip, self.Port))
            s.listen(5)
            print("TCP socket connection runing, listening to requests...")

        except Exception as e:
            print(self.CRED + 'Unable to create TCP socket' + self.CEND)
            print(self.CRED + "Error description : " + str(e) + self.CEND)

        while True:
            # self.winner = None
            self.ber = threading.Barrier(2)
            is_empty = True  # no even one player
            is_full = False  # all the players arrived the game can begin

            while not is_full:
                r = random.randint(0, len(self.bank) - 1)
                self.question, self.grand_answer = self.bank[r]

                if is_empty:
                    try:
                        conn, addr = s.accept()
                        player1 = threading.Thread(target=self.handle_client, args=(conn, True))
                        is_empty = False
                        player1.start()

                    except:
                        print(self.CRED + 'Unable to accept client via TCP socket' + self.CEND)
                        continue


                else:
                    try:
                        conn, addr = s.accept()
                        player2 = threading.Thread(target=self.handle_client, args=(conn, False))
                        is_full = True
                        player2.start()


                    except:
                        print(self.CRED + 'Unable to accept client via TCP socket' + self.CEND)
                        continue

            self.begin_game.acquire()  # change the lock to locked the udp loop will stop
            self.total_played += 1
            player1.join()
            player2.join()
            self.begin_game.release()
            print('\x1b[6;30;42m' + 'Server started, listening on IP address ' + self.Ip + '\x1b[0m')

    def handle_client(self, conn, first):
        '''
        Functiov that starts the game.
        The function send and revice messeges with the client on the other side of the connection
        '''
        try:
            self.winner = None
            name = conn.recv(1024).decode()
            if first:
                self.name1 = name
                # check if ends with '\n'?
                print("Client 1 has accepted: " + self.name1)
            else:
                self.name2 = name
                print("Client 2 has accepted: " + self.name2)
            self.ber.wait()  # wait for the other thread to arrive to this point
            msg = 'Welcome to Quick Maths\nPlayer 1: ' + self.name1 + 'Player 2: ' + self.name2 + '==\nPlease answer the following question as fast as you can:\n' + self.SMCS + 'How much is ' + self.question + self.SMCE + '\n'
            conn.send(msg.encode())  # sends the message
        except Exception as e:
            print(self.CRED + 'Lost connection to the client' + self.CEND)
            print(self.CRED + "Error description : " + str(e) + self.CEND)
            if first:
                self.winner = self.name2
            else:
                self.winner = self.name1

            conn.close()
        # start counting 10 seconds if no data reviced then send draw message
        timer = time.time()
        end_timer = time.time()
        try:
            if first:
                ans = threading.Thread(target=self.receive_char, args=(conn, True))
                ans.start()
            else:
                ans = threading.Thread(target=self.receive_char, args=(conn, False))
                ans.start()
        except Exception as e:
            if first:
                print(self.CRED + "Error with the receive thread on client 1" + self.CEND)
                self.winner = self.name2

            else:
                print(self.CRED + "Error with the receive thread on client 2" + self.CEND)
                print(self.CRED + "Error description : " + str(e) + self.CEND)
                self.winner = self.name1

            conn.close()

        while self.winner is None:
            end_timer = time.time()
            time.sleep(1)
            if end_timer - timer > 10.0:
                break

        try:
            if end_timer - timer >= 10.0:
                conn.send((
                                      'Game over!\nThe correct answer was ' + self.grand_answer + '\n\nits a ' + self.SMCS + 'DREW' + self.SMCE + '\n' + 'Total games played on our server: ' + str(
                                  self.total_played) + '\n').encode())
                conn.close()
            else:
                conn.send((
                                      'Game over!\nThe correct answer was ' + self.grand_answer + '\n\nCongratulations to the winner: ' + self.SMCS + self.winner[
                                                                                                                                                      :-1] + self.SMCE + '\n' + 'Total games played on our server: ' + str(
                                  self.total_played) + '\n').encode())
                conn.close()
            # send summery and close the socket

        except Exception as e:
            print(self.CRED + "Lost connection to the client" + self.CEND)
            print(self.CRED + "Error description : " + str(e) + self.CEND)
            if first:
                self.winner = self.name2
            else:
                self.winner = self.name1
            conn.close()

    def receive_char(self, conn, first):
        '''
        Function that recieve the connection and waits for client answer via the connection
        The function will ditermine who is the winned
        '''
        try:
            attempt = conn.recv(1024).decode()
        except Exception as e:
            if first:
                self.winner = self.name2
            else:
                self.winner = self.name1

        self.check.acquire()

        if self.winner is None:
            if first:
                if self.grand_answer == attempt:
                    self.winner = self.name1
                else:
                    self.winner = self.name2
            else:
                if self.grand_answer == attempt:
                    self.winner = self.name2
                else:
                    self.winner = self.name1

        self.check.release()


if __name__ == '__main__':
    # start server with ip
    s = Server(scapy.all.get_if_addr('eth1'))