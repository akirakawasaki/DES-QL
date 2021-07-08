### Standard libraries
import asyncio
import copy
import csv
import datetime
import math
import pathlib
import queue
import sys

# import cProfile
from os import spawnve
import pprint as pp
# import pstats

### Third-party libraries
import numpy as np
import pandas as pd

### Local libraries
# n/a


#
#   Data handler
#
class DataHandler :
    ''' Class constants '''
    
    # telemeter properties
    BPW = 2                     # bytes per word
    NUM_OF_FRAMES = 8           # number of frames in a major frame
    LEN_HEADER  = 4             # header length in bytes in a frame
    LEN_PAYLOAD = 64            # payload length in bytes in a frame
    BUFSIZE = BPW * (LEN_HEADER + LEN_PAYLOAD) * NUM_OF_FRAMES       # 1088 bytes

    # input file pathes
    FPATH_CONFIG = './config_tlm.xlsx'

    # output file pathes
    __FPATH_LS_DATA = './data_***.csv'                  # low-speed data
    __FNAME_LS_DATA = 'data_***.csv'
    __FPATH_HS_DATA = './high_speed_data_****.csv'      # high-speed data
    FPATH_ERR = './error_history.csv'                   # error history


    def __init__(self, tlm_type, g_state, g_lval, q_dgram) -> None:
        # shere arguments within the class
        self.tlm_type = tlm_type
        self.g_state = g_state
        self.g_lval = g_lval

        ### general settings
        # queues for inter-process message passing
        self.q_dgram = q_dgram      # receiving ONLY

        ### Initialize 
        # - decoder
        # load configuration for word assignment
        try: 
            df_cfg = pd.read_excel(self.FPATH_CONFIG, 
                            sheet_name=self.tlm_type, header=0, index_col=0).dropna(how='all')
        except:
            print(f'Error TLM {self.tlm_type}: Configuration file NOT exist!')
            sys.exit()
        
        self.dictTlmItemAttr = df_cfg.to_dict(orient='index')
        self.listTlmItem = list(self.dictTlmItemAttr)
        self.NUM_OF_ITEMS = len(df_cfg.index)
        self.MAX_SUP_COM = df_cfg['sup com'].max()

        self.iLine = 0

        # for high-speed data functionality
        self.high_speed_data_is_avtive = False
        self.idx_high_speed_data = 0

        # for latching of last MCU error in GUI
        self.last_error = 0

        # - file writer
        dt_now = datetime.datetime.now()
        str_dt = dt_now.strftime('%Y%m%d%H%S')
        fdir = './dat/' + str_dt
        print(fdir)
        pathlib.Path(fdir).mkdir(parents=True,exist_ok=True)
        self.fpath_ls_data = fdir + '/' + self.__FNAME_LS_DATA.replace('***', self.tlm_type)
        # self.fpath_ls_data = self.__FPATH_LS_DATA.replace('***', self.tlm_type)

        df_mf = pd.DataFrame(index=[], columns=self.dictTlmItemAttr.keys())
        df_mf.to_csv(self.fpath_ls_data, mode='w')


    #
    #   Telemetry data handler
    #
    async def data_handler(self) -> None:
        print(f'DAT {self.tlm_type}: Starting data handlar...')

        # create FIFO queues to communicate among async coroutines
        # self.q_dgram = asyncio.Queue()          # transferring datagram     from listner to decorder
        self.q_write_data = asyncio.Queue()     # transferring decoded data from decoder to file writer

        # invoke async tasks in the running event loop (ORDER OF INVOCATION IS IMPORTAN)
        # - file writer
        task_file_writer = asyncio.create_task( self.file_writer() ) 
        
        # - data decoder
        task_decoder = asyncio.create_task( self.decoder() )

        # block until GUI task done
        while True:            
            await asyncio.sleep(1)
            if self.g_state[self.tlm_type]['F_Quit_Data_Handler'] == True:  break
            # if self.g_state[self.tlm_type]['Tlm_Server_Is_Active'] == False:    break

        print(f'DAT {self.tlm_type}: Data handler will be closed soon...')

        # wait for queue to be fully processed
        await self.q_dgram.join()           

        # wait for queue to be fully processed
        await self.q_write_data.join()      

        # quit async tasks after GUI task done
        # - deta decoder
        # print(f'TLM {self.tlm_type}: queue size = {self.q_dgram.qsize()}')
        task_decoder.cancel()
        await task_decoder                  # wait for task to be cancelled

        # - file writer
        task_file_writer.cancel()
        await task_file_writer              # wait for task to be cancelled

        print(f'DAT {self.tlm_type}: Closing data handler...')


    # General file writer
    async def file_writer(self) -> None:
        print(f'DAT {self.tlm_type}: Starting file writer...')

        while True:
            try:
                (file_path, write_data) = await self.q_write_data.get()
            except asyncio.CancelledError:
                break

            with open(file_path, 'a') as f:
                writer = csv.writer(f)
                writer.writerows(write_data)
            
            self.q_write_data.task_done()

            # for debug 
            # print(f'DAT {self.tlm_type}: Data saved!')

        print(f'DAT {self.tlm_type}: Closing file writer...')


    # Datagram decoder
    async def decoder(self) -> None:
        print(f'DAT {self.tlm_type}: Starting data decoder...')

        Decoder_Task_Is_Canceled = False

        while True:
            # poll task cacellation
            try:
                pass
            except asyncio.CancelledError:
                Decoder_Task_Is_Canceled = True
            
            # poll datagram reception
            try:
                data = self.q_dgram.get_nowait()
            except queue.Empty:
                if Decoder_Task_Is_Canceled == True:    break

                await asyncio.sleep(0.0005)
                continue

            ### decode datagram
            dict_mf, hs_data, err_history = self.decode(data)

            ### output decoded data
            # - To Files
            if self.g_state[self.tlm_type]['Data_Save_Is_Active'] == True:
                # low-speed data 
                if self.iLine % 1 == 0:
                # if self.iLine % 10 == 0:
                    write_data = [  list(dict_mf[0].values()),
                                    list(dict_mf[1].values()),
                                    list(dict_mf[2].values()),
                                    list(dict_mf[3].values()),
                                    list(dict_mf[4].values()),
                                    list(dict_mf[5].values()),
                                    list(dict_mf[6].values()),
                                    list(dict_mf[7].values()) ]
                    self.q_write_data.put_nowait( (self.fpath_ls_data, write_data) )

                # high-speed data
                if hs_data != []:
                    self.q_write_data.put_nowait( (self.fpath_hs_data, hs_data) )

                # error history
                if err_history != []:
                    self.q_write_data.put_nowait( (self.FPATH_ERR, err_history) )

                # print(f'TLM {self.tlm_type}:  Data Save Is Active!')    # for debug

            # - To CUI
            # if iLine % 1 == 0:
            if self.iLine % 20000 == 0:
            # if self.iLine % 50000 == 0:
                print('')
                print(f'{self.tlm_type} iLine: {self.iLine}')
                # print(dict_mf)
                print(dict_mf[0])
                print(dict_mf[1])
                print(dict_mf[2])
                print(dict_mf[3])
                print(dict_mf[4])
                print(dict_mf[5])
                print(dict_mf[6])
                print(dict_mf[7])
                print('')

            # - To GUI
            self.notify_gui(dict_mf)

            self.q_dgram.task_done()

        print(f'DAT {self.tlm_type}: Closing data decoder...')


    # Notify GUI of latest values
    def notify_gui(self, dict_mf) -> None:
        # dict_tmp = dict_mf[0].copy()
        dict_tmp = copy.deepcopy(dict_mf[0])

        # fill NaN backward
        for key in dict_tmp.keys():
            try:
                if math.isnan(dict_tmp[key]) == False:  continue
            except TypeError:
                continue

            for iFrame in range(self.NUM_OF_FRAMES):
                try:
                    if math.isnan(dict_mf[iFrame][key]) == True:    continue
                except TypeError:
                    continue

                dict_tmp[key] = dict_mf[iFrame][key]

                break

        #
        #   Specialized Feature: Last Error Latch
        #
        if self.tlm_type == 'smt':
            # serch for last MCU error
            for iFrame in range(self.NUM_OF_FRAMES):
                if dict_mf[iFrame]['Error code'] == 0:  continue

                dict_tmp['Error code'] = dict_mf[iFrame]['Error code']

            # save last MCU error as a global status
            if dict_tmp['Error code'] != 0:
                self.g_state['last_error'] = dict_tmp['Error code']
        ###

        # 
        self.g_lval[self.tlm_type].update(dict_tmp) 


    # Decode raw telemetry data into physical values
    def decode(self, data):
        # initialize   
        gse_time = 0.0
        Vcjc = 0.0
        Vaz = 0.0

        hs_data = []
        err_history = []
        
        dict_data_matrix = {}

        # sweep frames in a major frame
        for iFrame in range(self.NUM_OF_FRAMES):
            # initialize row by filling with NaN
            dict_data_row = dict.fromkeys(['Line#'] + self.listTlmItem, math.nan)

            dict_data_row.update({'Line#':self.iLine})

            # byte index of the head of the frame (without header)
            byte_idx_head =   self.BPW * (self.LEN_HEADER + self.LEN_PAYLOAD) * iFrame \
                            + self.BPW *  self.LEN_HEADER
            # print(f"byte_idx_head: {byte_idx_head}") 

            # pick up data from the datagram (Get physical values from raw words)
            for strItem in self.dictTlmItemAttr.keys():
                iItem = self.listTlmItem.index(strItem)

                # calc byte index of datum within the datagram
                byte_idx =  byte_idx_head + self.BPW * int(self.dictTlmItemAttr[strItem]['w idx'])

                byte_length = self.BPW * int(self.dictTlmItemAttr[strItem]['word len'])
                byte_string = data[byte_idx:byte_idx+byte_length]

                ''' Decoding rules '''      ### To Be Refactored ###
                
                ### Peculiar items
                # - Number of days from January 1st on GSE
                if self.dictTlmItemAttr[strItem]['type'] == 'gse day':
                    # byte_length = self.BPW * int(self.dictTlmItemAttr[strItem]['word len'])
                    # byte_string = data[byte_idx:byte_idx+byte_length]

                    ###
                    decoded_value =  (byte_string[0] >> 4  ) * 100 \
                                   + (byte_string[0] & 0x0F) * 10  \
                                   + (byte_string[1] >> 4  ) * 1
                    ###
                    
                    dict_data_row.update({strItem:decoded_value})

                    continue

                # - GSE timestamp in [sec]
                elif self.dictTlmItemAttr[strItem]['type'] == 'gse time':
                    # byte_length = self.BPW * int(self.dictTlmItemAttr[strItem]['word len'])
                    # byte_string = data[byte_idx:byte_idx+byte_length]

                    ###
                    decoded_value =  (byte_string[1] & 0x0F) * 10  * 3600  \
                                   + (byte_string[2] >> 4  ) * 1   * 3600  \
                                   + (byte_string[2] & 0x0F) * 10  * 60    \
                                   + (byte_string[3] >> 4  ) * 1   * 60    \
                                   + (byte_string[3] & 0x0F) * 10          \
                                   + (byte_string[4] >> 4  ) * 1           \
                                   + (byte_string[4] & 0x0F) * 100 * 0.001 \
                                   + (byte_string[5] >> 4  ) * 10  * 0.001 \
                                   + (byte_string[5] & 0x0F) * 1   * 0.001

                    gse_time = decoded_value
                    ###
                    
                    dict_data_row.update({strItem:decoded_value})
                    
                    continue

                # - Relay status (boolean)
                elif self.dictTlmItemAttr[strItem]['type'] == 'bool':
                    # byte_length = self.BPW * int(self.dictTlmItemAttr[strItem]['word len'])
                    # byte_string = data[byte_idx:byte_idx+byte_length]

                    ###
                    byte_idx_offset = int(self.dictTlmItemAttr[strItem]['b coeff'])
                    bit_filter = int(self.dictTlmItemAttr[strItem]['a coeff'])
                    decoded_value = 1.0 if ((byte_string[byte_idx_offset] & bit_filter) > 0) \
                                    else 0.0
                    ###

                    dict_data_row.update({strItem:decoded_value})

                    continue

                ### High-speed data    ### T.B.REFAC. ###
                # - header
                if self.dictTlmItemAttr[strItem]['type'] == 'data hd':
                    ###
                    # - W009 + W010: start of data (SOD)
                    byte_idx_offset = 0
                    byte_length = 4
                    byte_string = data[byte_idx+byte_idx_offset:byte_idx+byte_idx_offset+byte_length]
                    
                    decoded_value = byte_string
                    dict_data_row.update({strItem:decoded_value})
                    ###

                    # - W009 + W010: start of data (SOD)
                    byte_idx_offset = 0
                    byte_length = 4
                    byte_string = data[byte_idx+byte_idx_offset:byte_idx+byte_idx_offset+byte_length]
                    
                    w009 = byte_string

                    # - W013 : sensor number
                    byte_idx_offset = 8 
                    byte_length = 2
                    byte_string = data[byte_idx+byte_idx_offset:byte_idx+byte_idx_offset+byte_length]

                    w013 = byte_string

                    # switch high_speed_data_is_active
                    if self.high_speed_data_is_avtive == False:
                        
                        # detect start of high-speed data when NOT ACTIVE
                        if      (w009 == b'\xff\x53\x4f\x44') \
                            and (w013 == b'\x00\x01' or w013 == b'\x00\x02' or w013 == b'\x00\x03'):

                            self.high_speed_data_is_avtive = True
                            self.fpath_hs_data = self.__FPATH_HS_DATA.replace('****', '{:0=4}'.format(self.idx_high_speed_data))
                            print('TLM DCD: Start of high-speed data is detected!')

                            ### file header
                            # - W011: data length
                            byte_idx_offset = 4
                            byte_length = 4
                            byte_string = data[byte_idx+byte_idx_offset:byte_idx+byte_idx_offset+byte_length]

                            signed = False
                            integer_bit_length = 32     # includes a sign bit if any
                            a_coeff = 1.0
                            b_coeff = 0.0

                            total_bit_length = 8 * byte_length
                            fractional_bit_length = total_bit_length - integer_bit_length
        
                            decoded_value =  b_coeff \
                                           + a_coeff * (int.from_bytes(byte_string, byteorder='big', signed=signed)) \
                                                        * 2**(-fractional_bit_length)

                            data_length = int(decoded_value)

                            # - W013: sensor number
                            byte_idx_offset = 8
                            byte_length = 2
                            byte_string = data[byte_idx+byte_idx_offset:byte_idx+byte_idx_offset+byte_length]

                            signed = False
                            integer_bit_length = 16     # includes a sign bit if any
                            a_coeff = 1.0
                            b_coeff = 0.0

                            total_bit_length = 8 * byte_length
                            fractional_bit_length = total_bit_length - integer_bit_length
        
                            decoded_value =  b_coeff \
                                           + a_coeff * (int.from_bytes(byte_string, byteorder='big', signed=signed)) \
                                                        * 2**(-fractional_bit_length)

                            sensor_number = int(decoded_value)

                            # - W017: sampling rate
                            byte_idx_offset = 16
                            byte_length = 2
                            byte_string = data[byte_idx+byte_idx_offset:byte_idx+byte_idx_offset+byte_length]

                            signed = False
                            integer_bit_length = 16     # includes a sign bit if any
                            a_coeff = 1.0
                            b_coeff = 0.0

                            total_bit_length = 8 * byte_length
                            fractional_bit_length = total_bit_length - integer_bit_length
        
                            decoded_value =  b_coeff \
                                           + a_coeff * (int.from_bytes(byte_string, byteorder='big', signed=signed)) \
                                                        * 2**(-fractional_bit_length)

                            sampling_rate = int(decoded_value)


                            hs_data.append(['data length=', data_length])
                            hs_data.append(['sensor number=', sensor_number])
                            hs_data.append(['sampling rate=', sampling_rate])
                            hs_data.append([])      # blank line

                    else:
                        # - W018: 
                        byte_idx_offset = 18
                        byte_length = 2
                        byte_string = data[byte_idx+byte_idx_offset:byte_idx+byte_idx_offset+byte_length]

                        w018 = byte_string

                        # detect end of high-speed data when ACTIVE
                        if      (w009 == b'\xff\x53\x4f\x44') \
                            and (w013 == b'\x00\x00') \
                            and (w018 == b'\xff\xff'):

                            self.high_speed_data_is_avtive = False
                            self.idx_high_speed_data += 1
                            print('TLM DCD: End of high-speed data detected!')

                    continue

                # - payload (first half)
                elif self.dictTlmItemAttr[strItem]['type'] == 'data pl1':
                    ###
                    # - W018
                    byte_idx_offset = 18
                    byte_length = 2
                    byte_string = data[byte_idx+byte_idx_offset:byte_idx+byte_idx_offset+byte_length]
                    
                    decoded_value = byte_string
                    dict_data_row.update({strItem:decoded_value})
                    ###

                    # skip below when high speed data is NOT active
                    if self.high_speed_data_is_avtive == False:     continue

                    # output history to an external file
                    for j in range(int(self.dictTlmItemAttr[strItem]['word len'])):
                        # decode 1 word
                        byte_idx_offset = self.BPW * j
                        byte_length = 2
                        byte_string = data[byte_idx+byte_idx_offset:byte_idx+byte_idx_offset+byte_length]                            
                        
                        #####
                        signed = self.dictTlmItemAttr[strItem]['signed']
                        integer_bit_length = int(self.dictTlmItemAttr[strItem]['integer bit len'])    # includes a sign bit if any
                        a_coeff = self.dictTlmItemAttr[strItem]['a coeff']
                        b_coeff = self.dictTlmItemAttr[strItem]['b coeff']

                        total_bit_length = 8 * byte_length
                        fractional_bit_length = total_bit_length - integer_bit_length

                        decoded_value =  b_coeff \
                                       + a_coeff * (int.from_bytes(byte_string, byteorder='big', signed=signed)) \
                                                    * 2**(-fractional_bit_length)
                        #####
                        
                        hs_data.append([format(gse_time,'.3f'), decoded_value])

                    continue

                # - payload (latter half)
                elif self.dictTlmItemAttr[strItem]['type'] == 'data pl2':
                    ###
                    # - W036
                    byte_idx_offset = 0
                    byte_length = 2
                    byte_string = data[byte_idx+byte_idx_offset:byte_idx+byte_idx_offset+byte_length]
                    
                    decoded_value = byte_string
                    dict_data_row.update({strItem:decoded_value})
                    ###

                    # skip below when high speed data is NOT active
                    if self.high_speed_data_is_avtive == False:     continue
                    
                    # output history to an external file
                    for j in range(int(self.dictTlmItemAttr[strItem]['word len'])):                        
                        byte_idx_offset = self.BPW * j
                        byte_length = 2
                        byte_string = data[byte_idx+byte_idx_offset:byte_idx+byte_idx_offset+byte_length]

                        #####
                        signed = self.dictTlmItemAttr[strItem]['signed']
                        integer_bit_length = int(self.dictTlmItemAttr[strItem]['integer bit len'])    # includes a sign bit if any
                        a_coeff = self.dictTlmItemAttr[strItem]['a coeff']
                        b_coeff = self.dictTlmItemAttr[strItem]['b coeff']

                        total_bit_length = 8 * byte_length
                        fractional_bit_length = total_bit_length - integer_bit_length

                        decoded_value =  b_coeff \
                                       + a_coeff * (int.from_bytes(byte_string, byteorder='big', signed=signed)) \
                                                    * 2**(-fractional_bit_length)
                        #####
                        
                        hs_data.append([format(gse_time,'.3f'), decoded_value])

                    continue

                ### Ordinary items
                # decoded_value = self.get_physical_value(self.dictTlmItemAttr[strItem], data, byte_idx)

                # - Ordinary items
                if self.dictTlmItemAttr[strItem]['ordinary item'] == True :
                    # handle sub-commutation
                    if iFrame % self.dictTlmItemAttr[strItem]['sub com mod'] != self.dictTlmItemAttr[strItem]['sub com res']: 
                        continue

                    decoded_value = self.get_physical_value(self.dictTlmItemAttr[strItem], byte_string)
                    # dict_data_row.update({strItem:decoded_value})

                # - Temperature in [K] <S,16,-2>
                elif self.dictTlmItemAttr[strItem]['type'] == 'T':
                    decoded_value = self.get_physical_value(self.dictTlmItemAttr[strItem], byte_string)
                    
                    # get TC thermoelectric voltage in [uV]
                    Vtc = decoded_value

                    # get temperature by converting thermoelectric voltage
                    Ttc = self.uv2k(Vtc + Vcjc - Vaz, 'K')

                    # decoded_value = Ttc             # in Kelvin
                    decoded_value = Ttc - 273.15    # in deg-C

                    # dict_data_row.update({strItem:Ttc})             # in Kelvin
                    # dict_data_row.update({strItem:(Ttc - 273.15)})  # in deg-C

                # - Cold-junction compensation coefficient in [uV]
                elif self.dictTlmItemAttr[strItem]['type'] == 'cjc':
                    decoded_value = self.get_physical_value(self.dictTlmItemAttr[strItem], byte_string)

                    cjc = decoded_value

                    Rcjc = self.v2ohm(cjc)
                    Tcjc = self.ohm2k(Rcjc)
                    Vcjc = self.k2uv(Tcjc, 'K')

                    decoded_value = Vcjc

                    # dict_data_row.update({strItem:Vcjc})

                # - Auto-zero coefficient in [uV]
                elif self.dictTlmItemAttr[strItem]['type'] == 'az':
                    decoded_value = self.get_physical_value(self.dictTlmItemAttr[strItem], byte_string)

                    Vaz = decoded_value
                    
                    # dict_data_row.update({strItem:decoded_value})

                # - error code
                elif self.dictTlmItemAttr[strItem]['type'] == 'ec':
                    decoded_value = self.get_physical_value(self.dictTlmItemAttr[strItem], byte_string)

                    ecode = decoded_value                
                    # memory when error occcures
                    if ecode != 0:  err_history.append([format(gse_time,'.3f'), int(ecode)])
                    
                    # dict_data_row.update({strItem:decoded_value})

                # - others
                else:
                    print(f'TLM RCV: ITEM={iItem} has no decoding rule!')

                # update dict_data_row
                dict_data_row.update({strItem:decoded_value})

            dict_data_matrix[iFrame] = dict_data_row

            self.iLine += 1

        return dict_data_matrix, hs_data, err_history

        # df_mf = pd.DataFrame.from_dict(dict_data_matrix, orient='index')

        # return df_mf, hs_data, err_history


    ''' Implimentations of decoding rules '''
    def dr_ordinary_item(self):
        pass

    def dr_gse_time(self):
        pass

    def dr_gse_time(self):
        pass


    ''' Utilities ''' 
    # Get a physical value from raw telemeter words
    def get_physical_value(self, itemAttr, byte_string):        

        ###
        byte_length = self.BPW * int(itemAttr['word len']) 
        signed = itemAttr['signed']
        integer_bit_length = int(itemAttr['integer bit len'])    # include sign bit if any
        a_coeff = itemAttr['a coeff']
        b_coeff = itemAttr['b coeff']

        total_bit_length = 8 * byte_length
        fractional_bit_length = total_bit_length - integer_bit_length
        decoded_value =  b_coeff \
                       + a_coeff * (int.from_bytes(byte_string, byteorder='big', signed=signed)) \
                                    * 2**(-fractional_bit_length)
        ###

        return decoded_value


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


    # Print a major flame
    def print_mf(self, data):
        # header
        for k in range(self.BPW * self.LEN_HEADER):   
            print(hex(data[k]).zfill(4), end=' ')
        print('')   # linefeed
        
        # payload
        for j in range(4):                  
            print(f"message {0}-{j}: ",end='')
            for k in range(self.BPW * int(self.LEN_PAYLOAD / 4)): 
                print(hex(data[k + self.BPW * (self.LEN_HEADER + j * int(self.LEN_PAYLOAD / 4))]).zfill(4), end=' ')
            print('')   # linefeed
        
        # empty line
        print('')


#
#   Main
#
if __name__ == "__main__":
    pass

    # print('MAIN: Invoking Telemetry Data Handler...')

    # tlm_type = sys.argv[1]

    # # error trap
    # if tlm_type == '':
    #     print("ERROR: TLM_TYPE is NOT designated!")
    #     sys.exit()
    # elif tlm_type != 'smt' and tlm_type != 'pcm':
    #     print("ERROR: TLM_TYPE is wrong!")
    #     sys.exit()

    # # set GIL switching time to a vlaue other than the default [s]
    # # sys.setswitchinterval(0.001)

    # # create instances
    # # q_message = asyncio.Queue
    # q_message = queue.Queue
    # q_latest_values = queue.Queue if (tlm_type == 'smt') else queue.Queue
    # tlm = TelemeterHandler(tlm_type, q_message, q_latest_values)

    # # invoke event loop to enter async coroutine
    # asyncio.run(tlm.tlm_handler(), debug=True)

    # print('Program terminated normally')