### Standard libraries
import asyncio
import queue
import socket

### Third-party libraries
# n/a

### Local libraries
# n/a


#
#   Telemeter handler
#
class TelemeterHandler :
    ### Class constants

    # n/a    

    def __init__(self, tlm_type, q_message, q_dgram) -> None:
        self.tlm_type = tlm_type

        # queues for inter-process message passing
        self.q_message = q_message      # receiving ONLY
        self.q_dgram = q_dgram          # sending ONLY

        # datagram server
        self.HOST = '172.20.140.255'                                # mac
        # self.HOST = socket.gethostbyname(socket.gethostname())      # windows / mac(debug)
        self.PORT =      60142 if (self.tlm_type == 'smt') \
                    else 60140

    async def telemeter_handler(self) -> None:
        # invoke async datagram listner
        loop = asyncio.get_running_loop()
        transport, _ = await loop.create_datagram_endpoint(
                                    protocol_factory=(lambda: DatagramServerProtocol(self.tlm_type, self.q_dgram)),
                                    local_addr=(self.HOST,self.PORT))

        # block until GUI task done
        while True:
            await asyncio.sleep(1)

            try:
                msg = self.q_message.get_nowait()
            except queue.Empty:            
                continue

            if msg == 'stop': 
                break
            else:
                self.q_message.task_done()
    
        print(f'TLM {self.tlm_type}: STOP message received!')

        # quit async detagram server
        transport.close()

        # 
        self.q_message.task_done()

        print(f'TLM {self.tlm_type}: Closing tlm handler...')


#
#   Datagram Server
#
class DatagramServerProtocol:    
    # Initialize instance
    def __init__(self, tlm_type, q_dgram) -> None:
        self.tlm_type = tlm_type
        self.q_dgram = q_dgram

        print(f'TLM {self.tlm_type}: Starting datagram listner...')

    # Event handler
    def connection_made(self,transport):
        print(f'Connected to {self.tlm_type}')
        
        self.transport = transport

    # Event handler
    def datagram_received(self, data, addr):
        # print(f'TLM {self.tlm_type}: Received a datagram')
        
        self.q_dgram.put_nowait(data)

        # for debug
        # print_mf(data)      
        # print(f'TLM RCV: queue size = {self.data_queue.qsize()}')

    # Event handler
    def connection_lost(self,exec):
        print(f'Disconnected from {self.tlm_type}') 
