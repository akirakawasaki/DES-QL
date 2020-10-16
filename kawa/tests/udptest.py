from socket import *

class udprecv():
    def __init__(self):
        
        #SrcIP = "192.168.108.189" 
        SrcIP = "" 
        #SrcPort = 70
        SrcPort = 49157
        self.SrcAddr = (SrcIP, SrcPort)

        self.BUFSIZE = 1088
        #self.BUFSIZE = 2176
        #self.BUFSIZE = 3000
        self.udpServSock = socket(AF_INET, SOCK_DGRAM)
        self.udpServSock.bind(self.SrcAddr)

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


