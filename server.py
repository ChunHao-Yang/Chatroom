import json
import socket
import threading
import re
import pymongo
import datetime
from time import sleep

from utils import *

HOST_IP = "localhost" 
PORT = 8088

clients = dict()
lock = threading.Lock()
db = None

class ClientThread(threading.Thread):
    def __init__(self, client_socket, addr):
        threading.Thread.__init__(self)
        self.cli_socket = client_socket
        self.addr = addr
    def run(self):
        while True:
            try:
                try:
                    recv_msg = self.cli_socket.recv(1024)
                except:
                    print(f"user: {self.addr} stop the connection.")
                    break
                recv_msg = recv_msg.decode()
                request_handler(db, self.cli_socket, recv_msg)
            except ConnectionResetError:
                print(f"user: {self.addr} stop the connection.")
                break
            
class SocketThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.flag = True
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    def run(self):
        self.s.bind((HOST_IP, PORT))
        self.s.listen()
        while True:
            c, addr = self.s.accept()
            
            if self.flag:
                print(f"user: {addr} start connecting.")
                lock.acquire()
                clients[addr] = c
                lock.release()
                ct = ClientThread(c, addr)
                ct.start()
            else:
                break
    def cancel(self):
        try:
            self.flag = False
            st = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            st.connect((HOST_IP, PORT))
            sleep(1)
            st.close()
            lock.acquire()
            for client in clients.values():
                client.shutdown(socket.SHUT_RDWR)
                client.close()
            lock.release()
            self.s.close()
            os._exit(0)
        except:
            pass

def main():
    global db
    # Init Database
    db = init_database()
    # Start Socket
    server_thread = SocketThread()
    
    server_thread.start()
    # Get command from server
    print(f"start server ...")
    print(f"type 'quit' to stop server.")
    while True:
        command =  input()
        if command == "quit":
            server_thread.cancel()
            print("server closed.")
            break
    close_database(db)
            
if __name__=="__main__":
    main()