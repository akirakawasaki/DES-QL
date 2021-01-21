### standard libraries
import asyncio
import socket
import sys

### third-party libraries
#n/a

### local libraries
#n/a


'''
Constant Definition
'''
W2B = 2
NUM_OF_FRAMES = 8
LEN_HEADER  = 4
LEN_PAYLOAD = 64
BUFSIZE = W2B * (LEN_HEADER + LEN_PAYLOAD) * NUM_OF_FRAMES       # 1088 bytes

class DatagramServerProtocol:
    def __init__(self,type):
        self.type = type
    
    def connection_made(self,transport):
        self.transport = transport
        print("connected")

    def connection_lost(self,exec):
        print("disconnected")

    def datagram_received(self,data,addr):
        print("Received a datagram from %s" % self.type)
        
        #port = self.transport.get_extra_info('sockname')[1]     # destination port
        #print(addr)
        #print(port)

        #DATA_PATH = ''
        #if self.type == 'smt':
        #    DATA_PATH = './data_smt.csv'
        #elif self.type == 'pcm':
        #    DATA_PATH = './data_pcm.csv'
        #else :
        #    print('Error: Type of the telemeter is wrong!')

        #print(data)

        for k in range(W2B * LEN_HEADER):   # header
            print(hex(data[k]).zfill(4), end=' ')
        print('')   # linefeed
        for j in range(4):                  # payload
            print(f"message {0}-{j}: ",end='')
            for k in range(W2B * int(LEN_PAYLOAD / 4)): 
                print(hex(data[k + W2B * (LEN_HEADER + j * int(LEN_PAYLOAD / 4))]).zfill(4), end=' ')
            print('')   # linefeed
        print('')   # linefeed


async def tlm(type):
    print("Starting UDP server for %s" % type)

    # initialize
    HOST = socket.gethostbyname(socket.gethostname())
    PORT = 0

    if type == 'smt':
        PORT = 49157
    elif type == 'pcm':
        PORT = 49158
    else :
        print('Error: Type of the telemeter is wrong!')
        sys.exit()

    # Get a reference to the event loop as we plan to use low-level APIs.
    loop = asyncio.get_running_loop()

    # One protocol instance will be created to serve all client requests.
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: DatagramServerProtocol(type),
        local_addr=(HOST,PORT))

    try:
        await asyncio.sleep(3600)  # Serve for 1 hour.
    finally:
        transport.close()


if __name__ == "__main__":
    #asyncio uses event loops to manage its operation
    loop = asyncio.get_event_loop()

    #Create coroutines for three tables
    gathered_coroutines = asyncio.gather(
        tlm("smt"),
        tlm("pcm"))

    #This is the entry from synchronous to asynchronous code. It will block ntil the coroutine passed in has completed
    loop.run_until_complete(gathered_coroutines)
    
    #We're done with the event loop
    loop.close()


