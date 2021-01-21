# standard libraries
import asyncio
#import decimal
#import math
#import socket
#import concurrent.futures

# third-party libraries
#import numpy as np
#import pandas as pd

# local libraries
#n/a


'''
Constant Definition
'''
W2B = 2

NUM_OF_FRAMES = 8

LEN_HEADER  = 4
LEN_PAYLOAD = 64

BUFSIZE = W2B * (LEN_HEADER + LEN_PAYLOAD) * NUM_OF_FRAMES       # 1088 bytes
#BUFSIZE = 1088
#BUFSIZE = 1280
#BUFSIZE = 2176


class DatagramServerProtocol:
    def __init__(self,type):
        self.type = type
    
    def connection_made(self,transport):
        self.transport = transport

    def datagram_received(self,data,addr):
        #port = self.transport.get_extra_info('sockname')[1]     # destination port
        #print(port)
        #print(addr)
        #print(self.type)

        if type == 'smt':
        #if port == 49157:
            # SMT
            DATA_PATH = './data_smt.csv'
        elif type == 'pcm':
        #elif port == 49158:
            # PCM
            DATA_PATH = './data_pcm.csv'
        else :
            DATA_PATH = ''
            print('Error: Type of the telemeter is wrong!')

        print(data)

        '''
        # header
        for k in range(W2B * LEN_HEADER): 
            print(hex(data[k]).zfill(4), end=' ')

        # payload
        for j in range(4):
            print(f"message {0}-{j}: ",end='')
            for k in range(W2B * int(LEN_PAYLOAD / 4)): 
                print(hex(data[k + W2B * (LEN_HEADER + j * int(LEN_PAYLOAD / 4))]).zfill(4), end=' ')
        
        # linefeed
        print('')
        '''


async def tlm(type):
    print("Starting UDP server for %s" % type)

    #HOST = socket.gethostname()
    HOST = 'localhost'

    if type == 'smt':
        PORT = 49157
    elif type == 'pcm':
        PORT = 49158
    else :
        PORT = 0
        print('Error: Type of the telemeter is wrong!')

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


