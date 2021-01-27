# from socket import *
import socket

class udprecv():
    def __init__(self):

        # DistIP = "192.168.1.4" 
        DistIP = "192.168.1.255" 
        # DistIP = "192.168.108.189" 
        # DistIP = "" 
        # DistIP = socket.gethostbyname(socket.gethostname())
        # SrcPort = 70
        DistPort = 49157
        self.DistAddr = (DistIP, DistPort)

        print(f'HOST = {DistIP}')

        self.BUFSIZE = 1088
        #self.BUFSIZE = 2176
        #self.BUFSIZE = 3000
        self.udpServSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udpServSock.bind(self.DistAddr)

    def recv(self):
        #while True:

        data, addr = self.udpServSock.recvfrom(self.BUFSIZE)
        
        print(f"from: {addr}")
        print(type(data))

        for i in range(8):
        #for i in range(16):
            print(f"message {i+1}-0: {data[i*136:i*136+8]}")
            for j in range(8):
                print(f"message {i+1}-{j+1}: {data[i*136+j*16+8:i*136+j*16+8+16]}")
               
        #for k in range(1088):
        #for k in range(1100):
        #    print(hex(data[k]))


            

udp = udprecv()
udp.recv()


