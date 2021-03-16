### Standard libraries
import asyncio
import csv
import math
from os import spawnve
import socket
import sys

### Third-party libraries
import numpy as np
import pandas as pd

### Local libraries
#n/a

'''
Constant Definition
'''
# n/a

#
#   Telemetry Data Hundler
#
async def tlm_hundler(tlm_type, internal_flags, tlm_latest_data):
    print('Starting socket communication for {}...'.format(tlm_type))
    
    # initialize
    # HOST = ''
    # HOST = '192.168.1.255'                                  # mac
    HOST = socket.gethostbyname(socket.gethostname())       # windows / mac(debug)
    PORT = 0

    ### T.B.REFAC. ###
    if tlm_type == 'smt':
        PORT = 49157
    elif tlm_type == 'pcm':
        PORT = 49158
    else :
        print('Error: Type of a telemeter is wrong!')
        return
    
    # tasks = []

    queue = asyncio.Queue()
    task = asyncio.create_task(tlm_data_decoder(tlm_type, queue, tlm_latest_data))
    # tasks.append(task)

    # file_path = f'./data_{tlm_type}.csv'        ### T.B.REFAC. ###
    # queue = asyncio.Queue()
    # task = asyncio.create_task(save_tlm_data(file_path, queue))
    # tasks.append(task)

    # file_path = None                            ### T.B.REFAC. ###
    # q_hsd = asyncio.Queue()
    # task = asyncio.create_task(save_tlm_data_hsd(file_path, q_hsd))
    # tasks.append(task)

    # file_path = './error_history.csv'           ### T.B.REFAC. ###
    # q_err = asyncio.Queue()
    # task = asyncio.create_task(save_tlm_data_err(file_path, q_err))
    # tasks.append(task)

    # # Wait until all worker tasks are cancelled.
    # await asyncio.gather(*tasks, return_exceptions=True)

    # print("I'm here!")

    # create datagram listner in the running event loop
    loop = asyncio.get_running_loop()
    (transport, protocol) = await loop.create_datagram_endpoint(
                                    lambda: DatagramServerProtocol(tlm_type, queue),
                                    local_addr=(HOST,PORT))
    # transport, protocol = await loop.create_datagram_endpoint(
    #                                 lambda: DatagramServerProtocol(tlm_type, tlm_latest_data, queue, q_hsd, q_err),
    #                                 local_addr=(HOST,PORT))

    ### T.B.REFAC. ###
    # wait until the GUI task is done
    while internal_flags.GUI_TASK_IS_DONE == False:
        await asyncio.sleep(1)

    transport.close()

    print(f'TLM {tlm_type}: queue size = {queue.qsize()}')

    # Wait until the queue is fully processed.
    await queue.join()
    # await q_hsd.join()
    # await q_err.join()

    # print("I'm here!")

    # Cancel our worker tasks.
    task.cancel()
    # for task in tasks:
    #     task.cancel()

    print('Closing {}...'.format(tlm_type))

    # quit
    # return (transport, protocol)

#
#   for low-speed data
#
# async def save_tlm_data(file_path, queue):
#     # await asyncio.sleep(1)
    
#     # DATA_PATH = f'./data_{tlm_type}.csv'
#     # df = pd.DataFrame()
#     # df.to_csv(DATA_PATH, mode='w')

#     while True:
#         # print(f'len = {queue.qsize()}')
        
#         # try:
#         #     pass    
#         # except asyncio.CancelledError:
#         #     if queue.empty() == True: break
#         #     raise

#         df = await queue.get()

#         df.to_csv(file_path, mode='a', header=False)
#         # df.to_csv(DATA_PATH, mode='a', header=False)
#         # print()
#         # print(f'item = {item}')

#         queue.task_done()

#
#   for high-speed data
#
# async def save_tlm_data_hsd(file_path, queue):
#     idx_high_speed_data = 0

#     while True:
#         # print(f'len = {queue.qsize()}')
        
#         item = await queue.get()

#         file_path = './high_speed_data_{:0=4}.csv'.format(idx_high_speed_data)
#         with open(file_path, 'a') as f:
#             writer = csv.writer(f)
#             writer.writerows(item)

#         queue.task_done()

#         idx_high_speed_data =+ 1

#
#   for error history
#
# async def save_tlm_data_err(file_path, queue):
#     while True:
#         # print(f'len = {queue.qsize()}')
        
#         item = await queue.get()

#         with open(file_path, 'a') as f:
#             writer = csv.writer(f)
#             writer.writerow(item)

#         queue.task_done()

#
#   Datagram Listner
#
class DatagramServerProtocol:
    # Constant Definition
    __W2B = 2
    __NUM_OF_FRAMES = 8
    __LEN_HEADER  = 4
    __LEN_PAYLOAD = 64

    __BUFSIZE = __W2B * (__LEN_HEADER + __LEN_PAYLOAD) * __NUM_OF_FRAMES       # 1088 bytes
    
    # Initialize instance
    # def __init__(self, tlm_type, tlm_latest_data, queue, q_hsd, q_err):
    def __init__(self, tlm_type, data_queue):
        print(f'Starting {tlm_type} handlar...')
        
        self.TLM_TYPE = tlm_type
        # self.tlm_latest_data = tlm_latest_data

        # choose a destination file for data ouput
        # self.DATA_PATH = f'./data_{self.TLM_TYPE}.csv'

        # load configuration for word assignment
        # try: 
        #     df_cfg = pd.read_excel('./config_tlm_2.xlsx', 
        #                         sheet_name=self.TLM_TYPE, header=0, index_col=None).dropna(how='all')
        # except:
        #     print('Error TLM: "config_tlm.xlsx"!')
        #     print(self.TLM_TYPE)
        #     sys.exit()
        # print('df_cfg = {}'.format(df_cfg))

        # self.TlmItemList = df_cfg['item'].values.tolist()
        # self.TlmItemAttr = df_cfg.to_dict(orient='index')
        # self.NUM_OF_ITEMS = len(df_cfg.index)
        # self.MAX_SUP_COM = df_cfg['sup com'].max()

        # for debug
        # print('Item List = {}'.format(self.TlmItemList))
        # print('Item Attributions = {}'.format(self.TlmItemAttr))

        # initialize a DataFrame to store data of one major frame
        # self.df_mf = pd.DataFrame(index=[], columns=self.TlmItemList) 
        # self.df_mf.to_csv(self.DATA_PATH, mode='w')
        
        self.data_queue = data_queue
        # self.queue = queue
        # self.q_hsd = q_hsd
        # self.q_err = q_err

        # initialize data index
        # self.iLine = 0

        # initialize high-speed data functionality
        # self.w009_old = 0x00
        # self.w018_old = 0x00
        # self.high_speed_data_is_avtive = False
        # self.idx_high_speed_data = 0

    # Event handler
    def connection_made(self,transport):
        print("Connected to %s" % self.TLM_TYPE)
        #self.transport = transport

    # Event handler
    def datagram_received(self, data, addr):
        print(f'Received a datagram from {self.TLM_TYPE}')
        #print_mf(data)      # for debug

        # check size of the datagram
        if len(data) != self.__BUFSIZE:
            print(f'ERROR TLM RCV: Size of received data = {len(data)}')

        self.data_queue.put_nowait(data)
        # print(f'TLM RCV: queue size = {self.data_queue.qsize()}')

        # self.__translate(data)
        
        # append translated data to file
        # self.queue.put_nowait(self.df_mf)
        # self.df_mf.to_csv(self.DATA_PATH, mode='a', header=False)
        
        #if self.iLine % 1 == 0:
        # if self.iLine % 500 == 0:
        #     print('')
        #     print(f'iLine: {self.iLine}')
        #     print(f'From : {addr}')
        #     # print(f'To   : {socket.gethostbyname(self.HOST)}')
        #     print(self.df_mf)
        #     print('')

        ### T.B.REFAC.? ###
        # notify GUI of the latest values
        # if self.TLM_TYPE == 'smt':
        #     self.tlm_latest_data.df_smt = self.df_mf.fillna(method='bfill').head(1)
        #     # self.tlm_latest_data.df_smt = self.df_mf.fillna(method='ffill').tail(1)
        # else:
        #     self.tlm_latest_data.df_pcm = self.df_mf.fillna(method='bfill').head(1)
        #     # self.tlm_latest_data.df_pcm = self.df_mf.fillna(method='ffill').tail(1)
        
        # for debug
        # print("TLM notifies GUI of df:")
        # print(self.tlm_latest_values.df_smt)
        # print(self.tlm_latest_values.df_smt.index)
    
    # Event handler
    def connection_lost(self,exec):
        print(f'Disconnected from {self.TLM_TYPE}')


#
#   Telemetry Data Decoder
#
async def tlm_data_decoder(tlm_type, data_queue, tlm_latest_data):
    print(f'Starting {tlm_type} data decoder...')
    
    tlm = Tlm(tlm_type)

    while True:
        data = await data_queue.get()
        
        df_mf = tlm.translate(data)

        if tlm_type == 'smt':
            tlm_latest_data.df_smt = df_mf.fillna(method='bfill').head(1)
            tlm_latest_data.df_smt = df_mf.fillna(method='ffill').tail(1)
        else:
            tlm_latest_data.df_pcm = df_mf.fillna(method='bfill').head(1)
            tlm_latest_data.df_pcm = df_mf.fillna(method='ffill').tail(1)

        data_queue.task_done()

#
#   tlm
#
class Tlm :
    W2B = 2
    NUM_OF_FRAMES = 8
    LEN_HEADER  = 4
    LEN_PAYLOAD = 64
    BUFSIZE = W2B * (LEN_HEADER + LEN_PAYLOAD) * NUM_OF_FRAMES       # 1088 bytes

    def __init__(self, tlm_type) :
        self.tlm_type = tlm_type

        # choose a destination file for data ouput
        self.data_path = f'./data_{self.tlm_type}.csv'

        # load configuration for word assignment
        try: 
            df_cfg = pd.read_excel('./config_tlm_2.xlsx', 
                                sheet_name=tlm_type, header=0, index_col=None).dropna(how='all')
        except:
            print('Error TLM: "config_tlm.xlsx"!')
            print(tlm_type)
            sys.exit()
        # print('df_cfg = {}'.format(df_cfg))

        self.TlmItemList = df_cfg['item'].values.tolist()
        self.TlmItemAttr = df_cfg.to_dict(orient='index')
        self.NUM_OF_ITEMS = len(df_cfg.index)
        self.MAX_SUP_COM = df_cfg['sup com'].max()

        # for debug
        # print('Item List = {}'.format(self.TlmItemList))
        # print('Item Attributions = {}'.format(self.TlmItemAttr))

        # initialize a DataFrame to store data of one major frame
        self.df_mf = pd.DataFrame(index=[], columns=self.TlmItemList)
        self.df_mf.to_csv(self.data_path, mode='w')
        
        # initialize data index
        self.iLine = 0

        # initialize high-speed data functionality
        # self.w009_old = 0x00
        # self.w018_old = 0x00
        self.high_speed_data_is_avtive = False
        # self.idx_high_speed_data = 0

    # Translate raw telemetry data into physical values
    def translate(self, data):
        ### T.B.REFAC. ###
        # initialize a DataFrame to store data of one major frame
        self.df_mf = pd.DataFrame(index=[], columns=self.TlmItemList)
        
        # initialize   
        gse_time = 0.0
        Vcjc = 0.0
        Vaz = 0.0
        
        # sweep frames in a major frame
        for iFrame in range(self.NUM_OF_FRAMES):
            #print(f"iLine: {self.iLine}")

            # initialize the row by filling wit NaN
            self.df_mf.loc[iFrame] = np.nan
            # print(self.df_mf)

            # byte index of the head of the frame (without header)
            byte_idx_head =   self.W2B * (self.LEN_HEADER + self.LEN_PAYLOAD) * iFrame \
                            + self.W2B *  self.LEN_HEADER
            #print(f"byte_idx_head: {byte_idx_head}") 
            
            # pick up data from the datagram (Get a physical value from telemeter words)
            for strItem in self.TlmItemList:
                iItem = self.TlmItemList.index(strItem)

                # byte index of the datum with the datagram
                byte_idx =  byte_idx_head + self.W2B * int(self.TlmItemAttr[iItem]['w idx'])

                ### Ordinary Items
                if self.TlmItemAttr[iItem]['ordinary item'] == True :
                    self.df_mf.iat[iFrame,iItem] = self.get_physical_value_from_tlm_words(iItem, data, byte_idx)

                ### other than ordinary items
                # - days from January 1st on GSE
                elif self.TlmItemAttr[iItem]['type'] == 'gse day':
                    self.df_mf.iat[iFrame,iItem] =  (data[byte_idx]   >> 4  ) * 100 \
                                                  + (data[byte_idx]   & 0x0F) * 10  \
                                                  + (data[byte_idx+1] >> 4  ) * 1
        
                # - GSE timestamp in [sec]
                elif self.TlmItemAttr[iItem]['type'] == 'gse time':
                    gse_time =  (data[byte_idx+1] & 0x0F) * 10  * 3600 \
                              + (data[byte_idx+2] >> 4  ) * 1   * 3600 \
                              + (data[byte_idx+2] & 0x0F) * 10  * 60   \
                              + (data[byte_idx+3] >> 4  ) * 1   * 60   \
                              + (data[byte_idx+3] & 0x0F) * 10         \
                              + (data[byte_idx+4] >> 4  ) * 1          \
                              + (data[byte_idx+4] & 0x0F) * 100 / 1000 \
                              + (data[byte_idx+5] >> 4  ) * 10  / 1000 \
                              + (data[byte_idx+5] & 0x0F) * 1   / 1000
                    self.df_mf.iat[iFrame,iItem] = gse_time

                # - temperature in [K] <S,16,-2>
                elif self.TlmItemAttr[iItem]['type'] == 'T':
                    # get TC thermoelectric voltage in [uV]
                    Vtc = self.get_physical_value_from_tlm_words(iItem, data, byte_idx)

                    # get temperature by converting thermoelectric voltage
                    Ttc = self.uv2k(Vtc + Vcjc - Vaz, 'K')

                    self.df_mf.iat[iFrame,iItem] = Ttc - 273.15         # in deg-C
                    # self.df_mf.iat[iFrame,iItem] = Ttc                 # in Kelvin
                
                # - cold-junction compensation coefficient in [uV]
                elif self.TlmItemAttr[iItem]['type'] == 'cjc':
                    cjc = self.get_physical_value_from_tlm_words(iItem, data, byte_idx)

                    Rcjc = self.v2ohm(cjc)
                    Tcjc = self.ohm2k(Rcjc)
                    Vcjc = self.k2uv(Tcjc, 'K')

                    self.df_mf.iat[iFrame,iItem] = Vcjc

                # - auto-zero coefficient in [uV]
                elif self.TlmItemAttr[iItem]['type'] == 'az':
                    Vaz = self.get_physical_value_from_tlm_words(iItem, data, byte_idx)
                    
                    self.df_mf.iat[iFrame,iItem] = Vaz

                # - relay status (boolean)
                elif self.TlmItemAttr[iItem]['type'] == 'bool':
                    self.df_mf.iat[iFrame,iItem] = \
                        (  data[byte_idx + int(self.TlmItemAttr[iItem]['b coeff'])] 
                            & int(self.TlmItemAttr[iItem]['a coeff'])) \
                            / int(self.TlmItemAttr[iItem]['a coeff'])

                # - analog pressure in [MPa]
                elif self.TlmItemAttr[iItem]['type'] == 'p ana':
                    # handle sub-commutation
                    if iFrame % self.TlmItemAttr[iItem]['sub com mod'] != self.TlmItemAttr[iItem]['sub com res']: 
                        continue
                    
                    self.df_mf.iat[iFrame,iItem] = self.get_physical_value_from_tlm_words(iItem, data, byte_idx)

                # - error code
                elif self.TlmItemAttr[iItem]['type'] == 'ec':
                    ecode = self.get_physical_value_from_tlm_words(iItem, data, byte_idx)
                    self.df_mf.iat[iFrame,iItem] = ecode
                    
                    # write history to an external file when an error occurs
                    if ecode != 0:
                        datum = [format(gse_time,'.3f'), int(ecode)]
                        
                        ### T.B.REFAC. ###
                        DATA_PATH_EC = './error_history.csv'
                        with open(DATA_PATH_EC, 'a') as f:
                            writer = csv.writer(f)
                            writer.writerow([format(gse_time,'.3f'), int(ecode)])
                        
                        # q_err.put_nowait(datum)

                ### T.B.REFAC. ###
                # - high speed data header
                elif self.TlmItemAttr[iItem]['type'] == 'data hd':
                    signed = self.TlmItemAttr[iItem]['signed']
                    integer_bit_length = int(self.TlmItemAttr[iItem]['integer bit len'])    # includes a sign bit if any
                    a_coeff = self.TlmItemAttr[iItem]['a coeff']
                    b_coeff = self.TlmItemAttr[iItem]['b coeff']

                    # - W009 + W010: start of data
                    byte_length = 4
                    total_bit_length = 8 * byte_length
                    fractional_bit_length = total_bit_length - integer_bit_length
                    byte_idx_shift = 0
                    #####
                    byte_string = []
                    for i in range(byte_length): byte_string.append(data[byte_idx+i+byte_idx_shift])

                    # physical_value =  b_coeff \
                    #                 + a_coeff \
                    #                     * (int.from_bytes(byte_string, byteorder='big', signed=signed)) \
                    #                     / 2**(fractional_bit_length)
                    #####
                    w009 = byte_string
                    self.df_mf.iat[iFrame,iItem] = w009

                    # - W013 : senser number
                    byte_length = 2
                    total_bit_length = 8 * byte_length
                    fractional_bit_length = total_bit_length - integer_bit_length
                    byte_idx_shift = 8
                    #####
                    byte_string = []
                    for i in range(byte_length): byte_string.append(data[byte_idx+i+byte_idx_shift])

                    # physical_value =  b_coeff \
                    #                 + a_coeff \
                    #                     * (int.from_bytes(byte_string, byteorder='big', signed=signed)) \
                    #                     / 2**(fractional_bit_length)
                    #####
                    w013 = byte_string

                    # # - W018 : head of payload
                    # byte_length = 2
                    # total_bit_length = 8 * byte_length
                    # fractional_bit_length = total_bit_length - integer_bit_length
                    # byte_idx_shift = 18
                    # #####
                    # byte_string = []
                    # for i in range(byte_length): byte_string.append(data[byte_idx+i+byte_idx_shift])

                    # physical_value =  b_coeff \
                    #                 + a_coeff \
                    #                     * (int.from_bytes(byte_string, byteorder='big', signed=signed)) \
                    #                     / 2**(fractional_bit_length)
                    # #####
                    # w018 = byte_string

                    # detect head of high-speed data
                    if (self.high_speed_data_is_avtive == False \
                            and w009 == [0xFF, 0x53, 0x4F, 0x44] \
                            and (w013 == [0x00, 0x01] or w013 == [0x00, 0x02] or w013 == [0x00, 0x03])):
                        self.high_speed_data_is_avtive = True
                        # idx_high_speed_data += 1
                        high_speed_data = []
                        print('TLM TRN: High-speed data is activated!')

                    # if (self.w009_old == [0xFF, 0x53, 0x4F, 0x44] and self.w018_old == [0xFF, 0xFF]) \
                    #     and (w009     != [0xFF, 0x53, 0x4F, 0x44] and      w018     != [0xFF, 0xFF]):
                    #     self.high_speed_data_is_avtive = True
                    #     self.idx_high_speed_data += 1
                    #     print('TLM TRN: High-speed data is activated!')
                    # elif (self.w009_old != [0xFF, 0x53, 0x4F, 0x44] and self.w018_old != [0xFF, 0xFF]) \
                    #     and (  w009     == [0xFF, 0x53, 0x4F, 0x44] and      w018     == [0xFF, 0xFF]):
                    #     self.high_speed_data_is_avtive = False
                    #     print('TLM TRN: High-speed data is deactivated!')

                    # self.w009_old = w009
                    # self.w018_old = w018

                ### T.B.REFAC. ###
                # - high speed data payload (first half)
                elif self.TlmItemAttr[iItem]['type'] == 'data pl1':
                    byte_length = 2
                    signed = self.TlmItemAttr[iItem]['signed']
                    integer_bit_length = int(self.TlmItemAttr[iItem]['integer bit len'])    # includes a sign bit if any
                    a_coeff = self.TlmItemAttr[iItem]['a coeff']
                    b_coeff = self.TlmItemAttr[iItem]['b coeff']

                    total_bit_length = 8 * byte_length
                    fractional_bit_length = total_bit_length - integer_bit_length
                    
                    # - W018
                    byte_idx_shift = 18
                    #####
                    byte_string = []
                    for i in range(byte_length): byte_string.append(data[byte_idx+i+byte_idx_shift])

                    # physical_value =  b_coeff \
                    #                 + a_coeff \
                    #                     * (int.from_bytes(byte_string, byteorder='big', signed=signed)) \
                    #                     / 2**(fractional_bit_length)
                    #####
                    w018 = byte_string
                    self.df_mf.iat[iFrame,iItem] = w018

                    # write history to an external file
                    if self.high_speed_data_is_avtive == True:
                        for j in range(int(self.TlmItemAttr[iItem]['word len'])):
                            byte_idx_shift = self.W2B * j
                            
                            #####
                            byte_string = []
                            for i in range(byte_length): byte_string.append(data[byte_idx+i+byte_idx_shift])

                            physical_value =  b_coeff \
                                            + a_coeff \
                                                * (int.from_bytes(byte_string, byteorder='big', signed=signed)) \
                                                / 2**(fractional_bit_length)
                            #####
                            
                            high_speed_data.append([format(gse_time,'.3f'), physical_value])

                            # detect EOF
                            if byte_string == [0xFF, 0xFF]:
                                self.high_speed_data_is_avtive = False
                                # q_hsd.put_nowait(high_speed_data)
                                print('TLM TRN: High-speed data is deactivated!')
                                break

                        # DATA_PATH_HSD = './high_speed_data_{:0=4}.csv'.format(self.idx_high_speed_data)
                        # with open(DATA_PATH_HSD, 'a') as f:
                        #     writer = csv.writer(f)
                        #     for j in range(int(TlmItemAttr[iItem]['word len'])):
                        #         byte_idx_shift = self.__W2B * j
                                
                        #         #####
                        #         byte_string = []
                        #         for i in range(byte_length): byte_string.append(data[byte_idx+i+byte_idx_shift])

                        #         physical_value =  b_coeff \
                        #                         + a_coeff \
                        #                             * (int.from_bytes(byte_string, byteorder='big', signed=signed)) \
                        #                             / 2**(fractional_bit_length)
                        #         #####
                                
                        #         writer.writerow([format(gse_time,'.3f'), physical_value])

                ### T.B.REFAC. ###
                # - high speed data payload (latter half)
                elif self.TlmItemAttr[iItem]['type'] == 'data pl2':
                    byte_length = 2
                    signed = self.TlmItemAttr[iItem]['signed']
                    integer_bit_length = int(self.TlmItemAttr[iItem]['integer bit len'])    # includes a sign bit if any
                    a_coeff = self.TlmItemAttr[iItem]['a coeff']
                    b_coeff = self.TlmItemAttr[iItem]['b coeff']

                    total_bit_length = 8 * byte_length
                    fractional_bit_length = total_bit_length - integer_bit_length
                    
                    # - W036
                    byte_idx_shift = 0
                    #####
                    byte_string = []
                    for i in range(byte_length): byte_string.append(data[byte_idx+i+byte_idx_shift])

                    # physical_value =  b_coeff \
                    #                 + a_coeff \
                    #                     * (int.from_bytes(byte_string, byteorder='big', signed=signed)) \
                    #                     / 2**(fractional_bit_length)
                    #####
                    w036 = byte_string
                    self.df_mf.iat[iFrame,iItem] = w036

                    # write history to an external file
                    if self.high_speed_data_is_avtive == True:
                        for j in range(int(self.TlmItemAttr[iItem]['word len'])):
                            byte_idx_shift = self.W2B * j
                            
                            #####
                            byte_string = []
                            for i in range(byte_length): byte_string.append(data[byte_idx+i+byte_idx_shift])

                            physical_value =  b_coeff \
                                            + a_coeff \
                                                * (int.from_bytes(byte_string, byteorder='big', signed=signed)) \
                                                / 2**(fractional_bit_length)
                            #####
                            
                            high_speed_data.append([format(gse_time,'.3f'), physical_value])

                            # detect EOF
                            if byte_string == [0xFF, 0xFF]:
                                self.high_speed_data_is_avtive = False
                                # q_hsd.put_nowait(high_speed_data)
                                print('TLM TRN: High-speed data is deactivated!')
                                break

                        # DATA_PATH_HSD = './high_speed_data_{:0=4}.csv'.format(self.idx_high_speed_data)
                        # with open(DATA_PATH_HSD, 'a') as f:
                        #     writer = csv.writer(f)
                        #     for j in range(int(self.TlmItemAttr[iItem]['word len'])):
                        #         byte_idx_shift = self.__W2B * j
                                
                        #         #####
                        #         byte_string = []
                        #         for i in range(byte_length): byte_string.append(data[byte_idx+i+byte_idx_shift])

                        #         physical_value =  b_coeff \
                        #                         + a_coeff \
                        #                             * (int.from_bytes(byte_string, byteorder='big', signed=signed)) \
                        #                             / 2**(fractional_bit_length)
                        #         #####
                                
                        #         writer.writerow([format(gse_time,'.3f'), physical_value])

                # - others
                else:
                    self.df_mf.iat[iFrame,iItem] = np.nan
                    # print(f'TLM RCV: ITEM={iItem} has no translation rule!')

            self.iLine += 1

        # clean up
        # self.df_mf.drop(self.df_mf.index[[0, -1]])

        # append translated data to file
        self.df_mf.to_csv(self.data_path, mode='a', header=False)
        
        #if iLine % 1 == 0:
        if self.iLine % 500 == 0:
            print('')
            print(f'iLine: {self.iLine}')
            # print(f'From : {addr}')
            # print(f'To   : {socket.gethostbyname(self.HOST)}')
            print(self.df_mf)
            print('')

        return self.df_mf

    ### T.B.REFAC. ###
    # notify GUI of the latest values
    # def notify_gui(self) :
    #     return self.df_mf.fillna(method='bfill').head(1)
    #     # return self.df_mf.fillna(method='ffill').tail(1)

    ''' Utilities ''' 
    #
    #   Get a physical value from telemeter words
    #
    ### T.B.REFAC. ###
    def get_physical_value_from_tlm_words(self, iItem, data, idx_byte):
        byte_length = self.W2B * int(self.TlmItemAttr[iItem]['word len'])
        signed = self.TlmItemAttr[iItem]['signed']
        integer_bit_length = int(self.TlmItemAttr[iItem]['integer bit len'])    # include sign bit if any
        a_coeff = self.TlmItemAttr[iItem]['a coeff']
        b_coeff = self.TlmItemAttr[iItem]['b coeff']

        total_bit_length = 8 * byte_length
        fractional_bit_length = total_bit_length - integer_bit_length
        
        byte_string = []
        for i in range(byte_length): byte_string.append(data[idx_byte+i])

        physical_value =  b_coeff \
                        + a_coeff \
                            * (int.from_bytes(byte_string, byteorder='big', signed=signed)) \
                            / 2**(fractional_bit_length)

        return physical_value

    #
    #   Convert thermoelectric voltage (in uV) to temperature (in K)
    #
    def uv2k(self, val, type):
        if type != 'K': print('ERROR!')

        # Ref.: NIST Monograph 175
        if val < 0.0:
            c0 = 0.0
            c1 = 2.5173462e-2
            c2 = -1.1662878e-6
            c3 = -1.0833638e-9
            c4 = -8.9773540e-13
            c5 = -3.7342377e-16
            c6 = -8.6632643e-20
            c7 = -1.0450598e-23
            c8 = -5.1920577e-28
            c9 = 0.0
        elif val < 20644.0:
            c0 = 0.0
            c1 = 2.508355e-2
            c2 = 7.860106e-8
            c3 = -2.503131e-10
            c4 = 8.315270e-14
            c5 = -1.228034e-17
            c6 = 9.804036e-22
            c7 = -4.413030e-26
            c8 = 1.057734e-30
            c9 = -1.052755e-35
        else:
            c0 = -1.318058e2
            c1 = 4.830222e-2
            c2 = -1.646031e-6
            c3 = 5.464731e-11
            c4 = -9.650715e-16
            c5 = 8.802193e-21
            c6 = -3.110810e-26
            c7 = 0.0
            c8 = 0.0
            c9 = 0.0

        y =  c0 \
            + c1 * val \
            + c2 * val**2 \
            + c3 * val**3 \
            + c4 * val**4 \
            + c5 * val**5 \
            + c6 * val**6 \
            + c7 * val**7 \
            + c8 * val**8 \
            + c9 * val**9 \
            + 273.15         # convert deg-C to Kelvin

        return y

    #        
    #   Convert temperature (in K) to thermoelectric voltage (in uV)
    #
    def k2uv(self, val, type):
        if type != 'K': print('ERROR!')

        val2 = val - 273.15     # convert Kelvin to deg-C

        # Ref.: NIST Monograph 175
        if val2 < 0.0:
            c0 = 0.0
            c1 = 3.9450128025e1
            c2 = 2.3622373598e-2
            c3 = -3.2858906784e-4
            c4 = -4.9904828777e-6
            c5 = -6.7509059173e-8
            c6 = -5.7410327428e-10
            c7 = -3.1088872894e-12
            c8 = -1.0451609365e-14
            c9 = -1.9889266878e-17
            c10 = -1.6322697486e-20
            alp0 = 0.0
            alp1 = 0.0
        else:
            c0 = -1.7600413686e1
            c1 = 3.8921204975e1
            c2 = 1.8558770032e-2
            c3 = -9.9457592874e-5
            c4 = 3.1840945719e-7
            c5 = -5.6072844889e-10
            c6 = 5.6075059059e-13
            c7 = -3.2020720003e-16
            c8 = 9.7151147152e-20
            c9 = -1.2104721275e-23
            c10 = 0.0
            alp0 = 1.185976e2
            alp1 = -1.183432e-4

        y =  c0 \
            + c1 * val2 \
            + c2 * val2**2 \
            + c3 * val2**3 \
            + c4 * val2**4 \
            + c5 * val2**5 \
            + c6 * val2**6 \
            + c7 * val2**7 \
            + c8 * val2**8 \
            + c9 * val2**9 \
            + c10 * val2**10 \
            + alp0 * math.exp(alp1 * (val2 - 126.9686)**2)
        
        return y

    #    
    #   Convert thermistor voltage to resistance
    #
    def v2ohm(self, val):
        # Ref.: Converting NI 9213 Data (FPGA Interface)
        return (1.0e4 * 32.0 * val) / (2.5 - 32.0 * val)

    #
    #   Convert thermistor resistance to temperature (in K)
    #
    def ohm2k(self, val):
        if val > 0:
            # Ref.: Converting NI 9213 Data (FPGA Interface)
            a = 1.2873851e-3
            b = 2.3575235e-4
            c = 9.4978060e-8
            y = 1.0 / (a + b * math.log(val) + c * (math.log(val)**3)) - 1.0
        else:
            y = 273.15
        
        return y

    #
    #   Print a major flame
    #
    def print_mf(self, data):
        # header
        for k in range(self.W2B * self.LEN_HEADER):   
            print(hex(data[k]).zfill(4), end=' ')
        print('')   # linefeed
        
        # payload
        for j in range(4):                  
            print(f"message {0}-{j}: ",end='')
            for k in range(self.W2B * int(self.LEN_PAYLOAD / 4)): 
                print(hex(data[k + self.W2B * (self.LEN_HEADER + j * int(self.LEN_PAYLOAD / 4))]).zfill(4), end=' ')
            print('')   # linefeed
        
        # empty line
        print('') 

 

