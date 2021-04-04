### Standard libraries
import asyncio
import csv
import math
from os import spawnve
import queue
import socket
import sys
import time

import cProfile
import pstats

### Third-party libraries
import numpy as np
import pandas as pd

### Local libraries
#n/a


#
#   Telemeter handler
#
class TelemeterHandler :
    # Class constants
    
    # telemeter properties
    W2B = 2
    NUM_OF_FRAMES = 8
    LEN_HEADER  = 4
    LEN_PAYLOAD = 64
    BUFSIZE = W2B * (LEN_HEADER + LEN_PAYLOAD) * NUM_OF_FRAMES       # 1088 bytes

    # input file pathes
    FPATH_CONFIG = './config_tlm_2.xlsx'

    # output file pathes
    __FPATH_LS_DATA = './data_***.csv'                # low-speed data    
    FPATH_HS_DATA = './high_speed_data_***.csv'     # high-speed data
    FPATH_ERR = './error_history.csv'               # error history


    def __init__(self, tlm_type, q_message, q_latest_values) -> None:
        ### general settings

        self.tlm_type = tlm_type

        # queues for inter-process message passing
        self.q_message = q_message                  # only for receiving
        self.q_latest_values = q_latest_values      # only for sending 

        ### Initialize datagram listner
        # self.HOST = ''
        # self.HOST = '192.168.1.255'                                  # mac
        self.HOST = socket.gethostbyname(socket.gethostname())       # windows / mac(debug)
        self.PORT = 49157 if (self.tlm_type == 'smt') else 49158


        ### Initialize decoder
        # load configuration for word assignment
        try: 
            df_cfg = pd.read_excel(self.FPATH_CONFIG, 
                            sheet_name=self.tlm_type, header=0, index_col=None).dropna(how='all')
        except:
            print(f'Error TLM {self.tlm_type}: Configuration file NOT exist!')
            sys.exit()
        
        # print(f'df_cfg = {df_cfg}')     # for debug

        self.TlmItemList = df_cfg['item'].values.tolist()
        self.TlmItemAttr = df_cfg.to_dict(orient='index')
        self.NUM_OF_ITEMS = len(df_cfg.index)
        self.MAX_SUP_COM = df_cfg['sup com'].max()

        # for debug
        # print(f'Item List = {self.TlmItemList}')
        # print(f'Item Attributions = {self.TlmItemAttr}')

        # initialize a DataFrame to store data of one major frame
        self.df_mf = pd.DataFrame(index=[], columns=self.TlmItemList)

        # initialize data index
        self.iLine = 0

        # initialize high-speed data functionality
        # self.w009_old = 0x00
        # self.w018_old = 0x00
        self.high_speed_data_is_avtive = False
        # self.idx_high_speed_data = 0


        ### Initialize file writer
        self.fpath_ls_data = self.__FPATH_LS_DATA.replace('***', self.tlm_type)
        self.df_mf.to_csv(self.fpath_ls_data, mode='w')        


    # Telemetry data hundler
    async def tlm_handler(self) -> None:
        print(f'TLM {self.tlm_type}: Starting tlm handlar...')

        # create FIFO queues to communicate among async coroutines
        self.q_dgram = asyncio.Queue()          # transferring datagram                from listner to decorder
        self.q_write_data = asyncio.Queue()     # transferring decoded low-speed data  from decoder to general file writer
        # self.q_ls_data = asyncio.Queue()        # transferring decoded low-speed data  from decoder to dedicated file writer
        # self.q_hs_data = asyncio.Queue()        # transferring decoded high-speed data from decoder to dedicated file writer
        # self.q_errors = asyncio.Queue()         # transferring decoded errors          from decoder to dedicated file writer

        ### invoke async tasks in the running event loop (ORDER OF INVOCATION IS IMPORTAN?)
        # task_fwriter_ls_data = asyncio.create_task( tlm.fwriter_ls_data() )
        # task_fweiter_hs_data = asyncio.create_task( tlm.fwriter_hs_data() )
        # task_fweiter_errors  = asyncio.create_task( tlm.fwriter_errors() )
        task_file_writer     = asyncio.create_task( tlm.file_writer() ) 
        task_decoder         = asyncio.create_task( tlm.decoder() )

        # invoke datagram endpoint
        loop = asyncio.get_running_loop()
        (transport, protocol) = await loop.create_datagram_endpoint(
                                        protocol_factory=(lambda: DatagramServerProtocol(tlm_type, self.q_dgram)),
                                        local_addr=(self.HOST,self.PORT))

        # wait until the GUI task done
        # while True:
        #     message = await self.q_message.get()
        #     if message == "quit tlm":   break

        # wait until the GUI task done
        # while q_message != True:
        #     await asyncio.sleep(1)

        # for debug
        await asyncio.sleep(10)

        # quit detagram listner after GUI task done
        transport.close()

        # quit decoder after datagram queue fully processed
        # print(f'TLM {self.tlm_type}: queue size = {self.q_dgram.qsize()}')
        await self.q_dgram.join()
        task_decoder.cancel()

        # quit file writer after write data queue fully processed
        await self.q_write_data.join()
        task_file_writer.cancel()

        # task_fwriter_ls_data.cancel()
        # task_fweiter_hs_data.cancel()
        # task_fweiter_errors.cancel()

        print(f'Closing {self.tlm_type} handler...')


    # General file writer
    async def file_writer(self) -> None:    
        print(f'TLM {self.tlm_type}: Starting file writer...')

        # 
        while True:
            (file_path, write_data) = await self.q_write_data.get()
            
            with open(file_path, 'a') as f:
                writer = csv.writer(f)
                writer.writerows(write_data)
            
            self.q_write_data.task_done()


    # # File writer for low-speed data
    # async def fwriter_ls_data(self) -> None:
    #     file_path = f'./data_{self.tlm_type}.csv'
        
    #     while True:
    #         df_mf = await self.q_ls_data.get()
    #         df_mf.to_csv(file_path, mode='w')
            
    #         self.q_ls_data.task_done()


    # # File writer for high-speed data
    # async def fwriter_hs_data(self) -> None:
    #     file_path = f'./data_{self.tlm_type}.csv'
        
    #     while True:
    #         df_mf = await self.q_ls_data.get()
    #         df_mf.to_csv(file_path, mode='w')
            
    #         self.q_ls_data.task_done()

    
    # # File writer for error history
    # async def fwriter_errors(self) -> None:
    #     file_path = './error.csv'
        
    #     while True:
    #         df_mf = await self.q_ls_data.get()
    #         df_mf.to_csv(file_path, mode='w')
            
    #         self.q_ls_data.task_done()


    # Datagram decoder
    async def decoder(self) -> None:
        print(f'TLM {self.tlm_type}: Starting data decoder...')

        while True:
            data = await self.q_dgram.get()
            
            # print('Im here!')

            df_mf = self.decode(data)

            # # append translated data to file
            # self.df_mf.to_csv(self.data_path, mode='a', header=False)

            # enqueue to save decode data in a file
            write_data = df_mf.values.tolist()
            self.q_write_data.put_nowait( (self.fpath_ls_data, write_data) )

            # notify GUI of latest values
            self.notify(df_mf)

            self.q_dgram.task_done()


    # Notify GUI of latest values
    def notify(self, df_mf) -> None:
        pass
        # if self.tlm_type == 'smt':
        #     tlm_latest_data.df_smt = df_mf.fillna(method='bfill').head(1)
        #     # tlm_latest_data.df_smt = df_mf.fillna(method='ffill').tail(1)
        # else:
        #     tlm_latest_data.df_pcm = df_mf.fillna(method='bfill').head(1)
        #     # tlm_latest_data.df_pcm = df_mf.fillna(method='ffill').tail(1)


    # Decode raw telemetry data into physical values
    def decode(self, data):
        # initialize a DataFrame to store data of one major frame
        self.df_mf = pd.DataFrame(index=[], columns=self.TlmItemList)
        
        # initialize   
        gse_time = 0.0
        Vcjc = 0.0
        Vaz = 0.0
        
        # sweep frames in a major frame
        for iFrame in range(self.NUM_OF_FRAMES):
            # print(f"iLine: {self.iLine}")

            # initialize the row by filling wit NaN
            self.df_mf.loc[iFrame] = np.nan
            # print(self.df_mf)

            # byte index of the head of the frame (without header)
            byte_idx_head =   self.W2B * (self.LEN_HEADER + self.LEN_PAYLOAD) * iFrame \
                            + self.W2B *  self.LEN_HEADER
            # print(f"byte_idx_head: {byte_idx_head}") 
            
            # pick up data from the datagram (Get physical values from raw words)
            for strItem in self.TlmItemList:
                iItem = self.TlmItemList.index(strItem)

                # calc byte index of datum within the datagram
                byte_idx =  byte_idx_head + self.W2B * int(self.TlmItemAttr[iItem]['w idx'])

                #
                #   Decoding rules
                #

                ### Peculiar items ()
                # - Number of days from January 1st on GSE
                if self.TlmItemAttr[iItem]['type'] == 'gse day':
                    self.df_mf.iat[iFrame,iItem] =  (data[byte_idx]   >> 4  ) * 100 \
                                                  + (data[byte_idx]   & 0x0F) * 10  \
                                                  + (data[byte_idx+1] >> 4  ) * 1
                    continue

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
                    continue

                # - Relay status (boolean)
                elif self.TlmItemAttr[iItem]['type'] == 'bool':
                    self.df_mf.iat[iFrame,iItem] = \
                        (  data[byte_idx + int(self.TlmItemAttr[iItem]['b coeff'])] 
                            & int(self.TlmItemAttr[iItem]['a coeff'])) \
                            / int(self.TlmItemAttr[iItem]['a coeff'])
                    continue

                ### High-speed data    ### T.B.REFAC. ###
                # - header
                if self.TlmItemAttr[iItem]['type'] == 'data hd':
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

                    # detect head of high-speed data
                    if self.high_speed_data_is_avtive == False:    
                        if      (w009 == [0xFF, 0x53, 0x4F, 0x44]) \
                            and (w013 == [0x00, 0x01] or w013 == [0x00, 0x02] or w013 == [0x00, 0x03]):
                            
                            self.high_speed_data_is_avtive = True
                            # idx_high_speed_data += 1
                            high_speed_data = []
                            print('TLM TRN: Start of high-speed data is detected!')

                    continue

                # - payload (first half)
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

                    continue

                # - payload (latter half)
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

                    continue

                ### Ordinary items
                float_value = self.get_physical_value(iItem, data, byte_idx)

                # - ordinary items
                if self.TlmItemAttr[iItem]['ordinary item'] == True :
                    self.df_mf.iat[iFrame,iItem] = float_value

                # - analog pressure in [MPa]
                elif self.TlmItemAttr[iItem]['type'] == 'p ana':
                    # handle sub-commutation
                    if iFrame % self.TlmItemAttr[iItem]['sub com mod'] != self.TlmItemAttr[iItem]['sub com res']: 
                        continue
                    
                    self.df_mf.iat[iFrame,iItem] = float_value

                # - Temperature in [K] <S,16,-2>
                elif self.TlmItemAttr[iItem]['type'] == 'T':
                    # get TC thermoelectric voltage in [uV]
                    Vtc = float_value

                    # get temperature by converting thermoelectric voltage
                    Ttc = self.uv2k(Vtc + Vcjc - Vaz, 'K')

                    self.df_mf.iat[iFrame,iItem] = Ttc - 273.15         # in deg-C
                    # self.df_mf.iat[iFrame,iItem] = Ttc                 # in Kelvin
                
                # - Cold-junction compensation coefficient in [uV]
                elif self.TlmItemAttr[iItem]['type'] == 'cjc':
                    cjc = float_value

                    Rcjc = self.v2ohm(cjc)
                    Tcjc = self.ohm2k(Rcjc)
                    Vcjc = self.k2uv(Tcjc, 'K')

                    self.df_mf.iat[iFrame,iItem] = Vcjc

                # - Auto-zero coefficient in [uV]
                elif self.TlmItemAttr[iItem]['type'] == 'az':
                    Vaz = float_value
                    
                    self.df_mf.iat[iFrame,iItem] = Vaz

                # - error code
                elif self.TlmItemAttr[iItem]['type'] == 'ec':
                    ecode = float_value
                    self.df_mf.iat[iFrame,iItem] = ecode
                    
                    ### T.B.REFAC. ###
                    # write history to an external file when error occurs
                    if ecode != 0:
                        datum = [format(gse_time,'.3f'), int(ecode)]
                        
                        # DATA_PATH_EC = './error_history.csv'
                        # with open(DATA_PATH_EC, 'a') as f:
                        #     writer = csv.writer(f)
                        #     writer.writerow([format(gse_time,'.3f'), int(ecode)])
                        
                        self.q_write_data.put_nowait( (self.FPATH_ERR, datum) )

                # - others
                else:
                    self.df_mf.iat[iFrame,iItem] = np.nan
                    print(f'TLM RCV: ITEM={iItem} has no decoding rule!')

            self.iLine += 1
        
        #if iLine % 1 == 0:
        if self.iLine % 500 == 0:
            print('')
            print(f'iLine: {self.iLine}')
            # print(f'From : {addr}')
            # print(f'To   : {socket.gethostbyname(self.HOST)}')
            print(self.df_mf)
            print('')

        return self.df_mf


    ''' Utilities ''' 
    # Print a major flame
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


    # Get a physical value from raw telemeter words
    def get_physical_value(self, iItem, data, idx_byte):
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


    # Convert thermoelectric voltage (in uV) to temperature (in K)
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


    # Convert temperature (in K) to thermoelectric voltage (in uV)
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


    # Convert thermistor voltage to resistance
    def v2ohm(self, val):
        # Ref.: Converting NI 9213 Data (FPGA Interface)
        return (1.0e4 * 32.0 * val) / (2.5 - 32.0 * val)


    # Convert thermistor resistance to temperature (in K)
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
#   Datagram Listner
#
class DatagramServerProtocol:    
    # Initialize instance
    def __init__(self, tlm_type, data_queue) -> None:
        self.TLM_TYPE = tlm_type
        self.data_queue = data_queue

        print(f'TLM {self.TLM_TYPE}: Starting datagram listner...')

    # Event handler
    def connection_made(self,transport):
        print(f'Connected to {self.TLM_TYPE}')
        #self.transport = transport

    # Event handler
    def datagram_received(self, data, addr):
        print(f'TLM {self.TLM_TYPE}: Received a datagram')
        
        # for debug
        # print_mf(data)      
        # print(f'TLM RCV: queue size = {self.data_queue.qsize()}')

        self.data_queue.put_nowait(data)

    # Event handler
    def connection_lost(self,exec):
        print(f'Disconnected from {self.TLM_TYPE}')


#
#   Main
#
if __name__ == "__main__":
    # cProfile.run('main()', filename='main.prof')
    
    print('MAIN: Invoking Telemetry Data Handler...')

    tlm_type = sys.argv[1]

    # error trap
    if tlm_type == '':
        print("ERROR: TLM_TYPE is NOT designated!")
        sys.exit()
    elif tlm_type != 'smt' and tlm_type != 'pcm':
        print("ERROR: TLM_TYPE is wrong!")
        sys.exit()

    # set GIL switching time to a vlaue other than the default [s]
    # sys.setswitchinterval(0.001)

    # create instances
    # q_message = False
    # q_message = asyncio.Queue
    q_message = queue.Queue
    q_latest_values = queue.Queue if (tlm_type == 'smt') else queue.Queue
    tlm = TelemeterHandler(tlm_type, q_message, q_latest_values)

    # invoke event loop to enter async coroutine
    asyncio.run(tlm.tlm_handler(), debug=True)

    # print('Im here!')

    # time.sleep(5)

    # q_message.put_nowait('quit tlm')
    # q_message = True

    print('Program terminated normally')