### Standard libraries
#import asyncio
import csv
#import decimal
import math
# import socket
import sys

### Third-party libraries
import numpy as np
import pandas as pd

### Local libraries
#n/a


'''
Constant Definition
'''
W2B = 2
# NUM_OF_FRAMES = 8
# LEN_HEADER  = 4
# LEN_PAYLOAD = 64
# BUFSIZE = W2B * (LEN_HEADER + LEN_PAYLOAD) * NUM_OF_FRAMES       # 1088 bytes


#
# UDP Communication Handler
#
class DatagramServerProtocol:
    # Constant Definition
    __W2B = 2

    __NUM_OF_FRAMES = 8

    __LEN_HEADER  = 4
    __LEN_PAYLOAD = 64
    
    __BUFSIZE = __W2B * (__LEN_HEADER + __LEN_PAYLOAD) * __NUM_OF_FRAMES       # 1088 bytes
    
    # Initialize instance
    def __init__(self, tlm_type, tlm_latest_data):
        print(f'Starting {tlm_type} handlar...')
        
        self.TLM_TYPE = tlm_type
        self.tlm_latest_data = tlm_latest_data

        # choose a destination file for data ouput
        self.DATA_PATH = f'./data_{self.TLM_TYPE}.csv'
        # if self.TLM_TYPE == 'smt':
        #     self.DATA_PATH = './data_smt.csv'
        # elif self.TLM_TYPE == 'pcm':
        #     self.DATA_PATH = './data_pcm.csv'
        # else:
        #     print('Error: Type of the telemeter is wrong!')
        #     sys.exit()

        # print('Im here!')

        # load configuration for word assignment
        # self.df_cfg = pd.read_excel('./config_tlm.xlsx', sheet_name=self.TLM_TYPE).dropna(how='all')
        try: 
            df_cfg = pd.read_excel('./config_tlm_2.xlsx', 
                                sheet_name=self.TLM_TYPE, header=0, index_col=None).dropna(how='all')
            # self.df_cfg = pd.read_excel('./config_tlm.xlsx', 
            #                     sheet_name=self.TLM_TYPE, header=0, index_col=None).dropna(how='all')
        except:
            print('Error TLM: "config_tlm.xlsx"!')
            print(self.TLM_TYPE)
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
        # self.df_mf = pd.DataFrame(index=[], columns=self.df_cfg['item']) 
        self.df_mf.to_csv(self.DATA_PATH, mode='w')

        # initialize data index
        self.iLine = 0

    # Event handler
    def connection_made(self,transport):
        print("Connected to %s" % self.TLM_TYPE)
        #self.transport = transport

    # Event handler
    def connection_lost(self,exec):
        print(f'Disconnected from {self.TLM_TYPE}')

    # Event handler
    def datagram_received(self, data, addr):
        print(f'Received a datagram from {self.TLM_TYPE}')
        #print_mf(data)      # for debug

        # check size of the datagram
        if len(data) != self.__BUFSIZE:
            print(f'ERROR TLM RCV: Size of received data = {len(data)}')

        self.__translate(data)
        
        # append translated data to file
        self.df_mf.to_csv(self.DATA_PATH, mode='a', header=False)
        
        #if self.iLine % 1 == 0:
        if self.iLine % 500 == 0:
            print('')
            print(f'iLine: {self.iLine}')
            print(f'From : {addr}')
            # print(f'To   : {socket.gethostbyname(self.HOST)}')
            print(self.df_mf)
            print('')

        # notify GUI of the latest values
        if self.TLM_TYPE == 'smt':
            self.tlm_latest_data.df_smt = self.df_mf.fillna(method='ffill').tail(1)
        else:
            self.tlm_latest_data.df_pcm = self.df_mf.fillna(method='ffill').tail(1)
        
        # if self.TLM_TYPE == 'smt':
        #     self.tlm_latest_data.df_smt = self.df_mf.tail(1)
        # else:
        #     self.tlm_latest_data.df_pcm = self.df_mf.tail(1)

        # for debug
        # print("TLM notifies GUI of df:")
        # print(self.tlm_latest_values.df_smt)
        # print(self.tlm_latest_values.df_smt.index)
    
    # Internal method: 
    # Translate raw telemetry data into physical values
    def __translate(self, data):
        # initialize   ### T.B.REFAC ###
        Vcjc = 0.0
        Vaz = 0.0
        
        # self.df_mf = pd.DataFrame(index=[], columns=self.TlmItemList) 

        # sweep frames in a major frame
        for iFrame in range(self.__NUM_OF_FRAMES):
            #print(f"iLine: {self.iLine}")

            ### initialize the row by filling wit NaN
            self.df_mf.loc[iFrame] = np.nan
            # self.df_mf.loc[iFrame] = np.nan
            # print(self.df_mf)

            ### byte index of the head of the frame (without header)
            byte_idx_head =  self.__W2B * (self.__LEN_HEADER + self.__LEN_PAYLOAD) * iFrame \
                           + self.__W2B *  self.__LEN_HEADER
            #print(f"byte_idx_head: {byte_idx_head}") 
            
            ### pick up data from the datagram
            '''
            When w assgn < 0
            '''
            # # Days from January 1st on GSE
            # byte_idx = byte_idx_head + self.__W2B * 0
            # self.df_mf.iat[iFrame,0] =  (data[byte_idx]   >> 4  ) * 100 \
            #                           + (data[byte_idx]   & 0x0F) * 10  \
            #                           + (data[byte_idx+1] >> 4  ) * 1
        
            # # GSE timestamp in [sec]
            # byte_idx = byte_idx_head + self.__W2B * 0
            # self.df_mf.iat[iFrame,1] =  (data[byte_idx+1] & 0x0F) * 10  * 3600 \
            #                           + (data[byte_idx+2] >> 4  ) * 1   * 3600 \
            #                           + (data[byte_idx+2] & 0x0F) * 10  * 60   \
            #                           + (data[byte_idx+3] >> 4  ) * 1   * 60   \
            #                           + (data[byte_idx+3] & 0x0F) * 10         \
            #                           + (data[byte_idx+4] >> 4  ) * 1          \
            #                           + (data[byte_idx+4] & 0x0F) * 100 / 1000 \
            #                           + (data[byte_idx+5] >> 4  ) * 10  / 1000 \
            #                           + (data[byte_idx+5] & 0x0F) * 1   / 1000 

            '''
            When w assgn >= 0
            '''
            # Get a physical value from telemeter words
            # for iItem in range(0, self.NUM_OF_ITEMS):
            # for iItem in range(2, self.NUM_OF_ITEMS):
            for strItem in self.TlmItemList:
                iItem = self.TlmItemList.index(strItem)
                # iItem = int(self.TlmItemAttr[strItem]['No.']) - 1       ### T.B.REFAC ###

                # byte index of the datum with the datagram
                byte_idx =  byte_idx_head + self.__W2B * int(self.TlmItemAttr[iItem]['w idx'])
                # byte_idx = byte_idx_head + self.__W2B * (self.__LEN_HEADER + int(self.df_cfg.at[iItem,'w idx']))

                # ordinary Items
                if self.TlmItemAttr[iItem]['ordinary item'] == True :
                    self.df_mf.iat[iFrame,iItem] = self.get_physical_value_from_tlm_words(iItem, data, byte_idx)

                # days from January 1st on GSE
                elif self.TlmItemAttr[iItem]['type'] == 'gse day':
                    # byte_idx = byte_idx_head + self.__W2B * 0
                    self.df_mf.iat[iFrame,iItem] =  (data[byte_idx]   >> 4  ) * 100 \
                                                  + (data[byte_idx]   & 0x0F) * 10  \
                                                  + (data[byte_idx+1] >> 4  ) * 1
        
                # GSE timestamp in [sec]
                elif self.TlmItemAttr[iItem]['type'] == 'gse time':
                    # byte_idx = byte_idx_head + self.__W2B * 0
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

                # temperature in [K] <S,16,-2>
                elif self.TlmItemAttr[iItem]['type'] == 'T':
                # elif self.df_cfg.at[iItem,'type'] == 'T':
                    # TC thermoelectric voltage in [uV]
                    Vtc = self.get_physical_value_from_tlm_words(iItem, data, byte_idx)
                    # Vtc =  self.df_cfg.at[iItem,'a coeff'] / 2**18 * 1e6 \
                    #         * int.from_bytes((data[byte_idx], data[byte_idx+1]), 
                    #                         byteorder='big', signed=True) \
                    #      + self.df_cfg.at[iItem,'b coeff']

                    Ttc = self.uv2k(Vtc + Vcjc - Vaz, 'K')

                    # self.df_mf.iat[iFrame,iItem] = Ttc                 # Kelvin
                    self.df_mf.iat[iFrame,iItem] = Ttc - 273.15         # deg-C
                    # self.df_mf.iat[iFrame,iItem] = Ttc
                
                # cold-junction compensation coefficient in [uV]
                elif self.TlmItemAttr[iItem]['type'] == 'cjc':
                # elif self.df_cfg.at[iItem,'type'] == 'cjc':
                    cjc = self.get_physical_value_from_tlm_words(iItem, data, byte_idx)
                    # cjc =  self.df_cfg.at[iItem,'a coeff'] / 2**18 \
                    #         * int.from_bytes((data[byte_idx], data[byte_idx+1]), 
                    #                         byteorder='big', signed=True) \
                    #      + self.df_cfg.at[iItem,'b coeff']
                    Rcjc = self.v2ohm(cjc)
                    Tcjc = self.ohm2k(Rcjc)
                    Vcjc = self.k2uv(Tcjc, 'K')

                    self.df_mf.iat[iFrame,iItem] = Vcjc
                    # self.df_mf.iat[iFrame,iItem] = Vcjc

                # auto-zero coefficient in [uV]
                elif self.TlmItemAttr[iItem]['type'] == 'az':
                # elif self.df_cfg.at[iItem,'type'] == 'az':
                    Vaz = self.get_physical_value_from_tlm_words(iItem, data, byte_idx)
                    # Vaz =  self.df_cfg.at[iItem,'a coeff'] / 2**18 * 1e6 \
                    #         * int.from_bytes((data[byte_idx], data[byte_idx+1]), 
                    #                         byteorder='big', signed=True) \
                    #      + self.df_cfg.at[iItem,'b coeff']
                    
                    self.df_mf.iat[iFrame,iItem] = Vaz
                    # self.df_mf.iat[iFrame,iItem] = Vaz

                # relay status (boolean)
                elif self.TlmItemAttr[iItem]['type'] == 'bool':
                # elif self.TlmItemAttr[iItem]['type'] == 'bit':
                # elif self.TlmItemAttr[iItem]['type'] == 'rel':
                # elif self.df_cfg.at[iItem,'type'] == 'rel':
                    self.df_mf.iat[iFrame,iItem] = \
                        (  data[byte_idx + int(self.TlmItemAttr[iItem]['b coeff'])] 
                         & int(self.TlmItemAttr[iItem]['a coeff'])) \
                            / int(self.TlmItemAttr[iItem]['a coeff'])

                    # self.df_mf.iat[iFrame,iItem] = \
                        # (data[byte_idx + int(self.df_cfg.at[iItem,'b coeff'])] & int(self.df_cfg.at[iItem,'a coeff'])) \
                        #     / self.df_cfg.at[iItem,'a coeff']

                # analog pressure in [MPa]
                elif self.TlmItemAttr[iItem]['type'] == 'p ana':
                # elif self.df_cfg.at[iItem,'type'] == 'p ana':
                    if iFrame % self.TlmItemAttr[iItem]['sub com mod'] != self.TlmItemAttr[iItem]['sub com res']: 
                        continue
                    # if iFrame % self.df_cfg.at[iItem,'sub com mod'] != self.df_cfg.at[iItem,'sub com res']: continue
                    
                    self.df_mf.iat[iFrame,iItem] = self.get_physical_value_from_tlm_words(iItem, data, byte_idx)
                    # self.df_mf.iat[iFrame,iItem] = \
                    #       self.df_cfg.at[iItem,'a coeff'] / 2**16 * 5.0 \
                    #         * int.from_bytes((data[byte_idx],data[byte_idx+1]), 
                    #                         byteorder='big', signed=True) \
                    #     + self.df_cfg.at[iItem,'b coeff']

                # error code
                elif self.TlmItemAttr[iItem]['type'] == 'ec':
                    ecode = self.get_physical_value_from_tlm_words(iItem, data, byte_idx)
                    self.df_mf.iat[iFrame,iItem] = ecode
                    
                    # write history to an external file when an error occurs
                    if ecode != 0:
                        DATA_PATH_EC = './error_history.csv'
                        with open(DATA_PATH_EC, 'a') as f:
                            writer = csv.writer(f)
                            writer.writerow([format(gse_time,'.3f'), int(ecode)])

                # high speed data header
                elif self.TlmItemAttr[iItem]['type'] == 'data hd':
                    ### T.B.REFAC ###
                    
                    byte_length = 2
                    signed = self.TlmItemAttr[iItem]['signed']
                    integer_bit_length = int(self.TlmItemAttr[iItem]['integer bit len'])    # include sign bit if any
                    a_coeff = self.TlmItemAttr[iItem]['a coeff']
                    b_coeff = self.TlmItemAttr[iItem]['b coeff']

                    total_bit_length = 8 * byte_length
                    fractional_bit_length = total_bit_length - integer_bit_length
                    
                    # - start of data 1
                    byte_idx_shift = 0
                    #####
                    byte_string = []
                    for i in range(byte_length): byte_string.append(data[byte_idx+i+byte_idx_shift])

                    physical_value =  b_coeff \
                                    + a_coeff \
                                        * (int.from_bytes(byte_string, byteorder='big', signed=signed)) \
                                        / 2**(fractional_bit_length)
                    #####
                    SOD_H = physical_value

                    # - start of data 2
                    byte_idx_shift = 2
                    #####
                    byte_string = []
                    for i in range(byte_length): byte_string.append(data[byte_idx+i+byte_idx_shift])

                    physical_value =  b_coeff \
                                    + a_coeff \
                                        * (int.from_bytes(byte_string, byteorder='big', signed=signed)) \
                                        / 2**(fractional_bit_length)
                    #####
                    SOD_L = physical_value

                    # - sensor number
                    byte_idx_shift = 8
                    #####
                    byte_string = []
                    for i in range(byte_length): byte_string.append(data[byte_idx+i+byte_idx_shift])

                    physical_value =  b_coeff \
                                    + a_coeff \
                                        * (int.from_bytes(byte_string, byteorder='big', signed=signed)) \
                                        / 2**(fractional_bit_length)
                    #####
                    SENS_NUM = physical_value

                    self.df_mf.iat[iFrame,iItem] = SENS_NUM

                # high speed data payload
                elif self.TlmItemAttr[iItem]['type'] == 'data pl1':
                    ### T.B.REFAC ###
                    
                    byte_length = 2
                    signed = self.TlmItemAttr[iItem]['signed']
                    integer_bit_length = int(self.TlmItemAttr[iItem]['integer bit len'])    # include sign bit if any
                    a_coeff = self.TlmItemAttr[iItem]['a coeff']
                    b_coeff = self.TlmItemAttr[iItem]['b coeff']

                    total_bit_length = 8 * byte_length
                    fractional_bit_length = total_bit_length - integer_bit_length
                    
                    # - W018
                    byte_idx_shift = 0
                    #####
                    byte_string = []
                    for i in range(byte_length): byte_string.append(data[byte_idx+i+byte_idx_shift])

                    physical_value =  b_coeff \
                                    + a_coeff \
                                        * (int.from_bytes(byte_string, byteorder='big', signed=signed)) \
                                        / 2**(fractional_bit_length)
                    #####
                    W018 = byte_string

                    self.df_mf.iat[iFrame,iItem] = W018

                    # if (SENS_NUM != 0) and (W018 != 0xFFFF):
                    if ((SENS_NUM == 1) or (SENS_NUM == 2) or (SENS_NUM == 3)) and (W018 != 0xFFFF):
                        # write history to an external file
                        DATA_PATH_HSD = f'./high_speed_data{int(SENS_NUM)}.csv'
                        with open(DATA_PATH_HSD, 'a') as f:
                            writer = csv.writer(f)
                            for j in range(int(self.TlmItemAttr[iItem]['word len'])):
                                byte_idx_shift = self.__W2B * j
                                #####
                                byte_string = []
                                for i in range(byte_length): byte_string.append(data[byte_idx+i+byte_idx_shift])

                                physical_value =  b_coeff \
                                                + a_coeff \
                                                    * (int.from_bytes(byte_string, byteorder='big', signed=signed)) \
                                                    / 2**(fractional_bit_length)
                                
                                writer.writerow([format(gse_time,'.3f'), physical_value])

                elif self.TlmItemAttr[iItem]['type'] == 'data pl2':
                    ### T.B.REFAC ###
                    
                    byte_length = 2
                    signed = self.TlmItemAttr[iItem]['signed']
                    integer_bit_length = int(self.TlmItemAttr[iItem]['integer bit len'])    # include sign bit if any
                    a_coeff = self.TlmItemAttr[iItem]['a coeff']
                    b_coeff = self.TlmItemAttr[iItem]['b coeff']

                    total_bit_length = 8 * byte_length
                    fractional_bit_length = total_bit_length - integer_bit_length
                    
                    # - W036
                    byte_idx_shift = 0
                    #####
                    byte_string = []
                    for i in range(byte_length): byte_string.append(data[byte_idx+i+byte_idx_shift])

                    physical_value =  b_coeff \
                                    + a_coeff \
                                        * (int.from_bytes(byte_string, byteorder='big', signed=signed)) \
                                        / 2**(fractional_bit_length)
                    #####
                    W036 = byte_string

                    self.df_mf.iat[iFrame,iItem] = W036

                    # if (SENS_NUM != 0) and (W018 != 0xFFFF):
                    if ((SENS_NUM == 1) or (SENS_NUM == 2) or (SENS_NUM == 3)) and (W018 != 0xFFFF):
                        # write history to an external file
                        DATA_PATH_HSD = f'./high_speed_data{int(SENS_NUM)}.csv'
                        with open(DATA_PATH_HSD, 'a') as f:
                            writer = csv.writer(f)
                            for j in range(int(self.TlmItemAttr[iItem]['word len'])):
                                byte_idx_shift = self.__W2B * j
                                #####
                                byte_string = []
                                for i in range(byte_length): byte_string.append(data[byte_idx+i+byte_idx_shift])

                                physical_value =  b_coeff \
                                                + a_coeff \
                                                    * (int.from_bytes(byte_string, byteorder='big', signed=signed)) \
                                                    / 2**(fractional_bit_length)
                                
                                writer.writerow([format(gse_time,'.3f'), physical_value])

                # DES timestamp in [sec]
                # if self.df_cfg.at[iItem,'type'] == 'des time':
                #     self.df_mf.iat[iFrame,iItem] = \
                #         int.from_bytes((data[byte_idx], data[byte_idx+1], data[byte_idx+2], data[byte_idx+3]), 
                #                         byteorder='big', signed=False) \
                #         / 1000.0

                # pressure in [MPa] <S,16,5>
                # elif self.df_cfg.at[iItem,'type'] == 'p':
                #     self.df_mf.iat[iFrame,iItem] = \
                #         self.df_cfg.at[iItem,'a coeff'] / 2**11 \
                #             * int.from_bytes((data[byte_idx], data[byte_idx+1]), 
                #                             byteorder='big', signed=True) \
                #         + self.df_cfg.at[iItem,'b coeff']


                # acceleration in [m/s2] <S,32,12>
                # elif self.df_cfg.at[iItem,'type'] == 'a':
                #     self.df_mf.iat[iFrame,iItem] = \
                #         self.df_cfg.at[iItem,'a coeff'] / 2**20 \
                #             * int.from_bytes((data[byte_idx], data[byte_idx+1], data[byte_idx+2], data[byte_idx+3] ), 
                #                             byteorder='big', signed=True) \
                #         + self.df_cfg.at[iItem,'b coeff']

                # angular velocity in [rad/s] <S,32,12>
                # elif self.df_cfg.at[iItem,'type'] == 'omg':
                #     self.df_mf.iat[iFrame,iItem] = \
                #         self.df_cfg.at[iItem,'a coeff'] / 2**20 \
                #             * int.from_bytes((data[byte_idx], data[byte_idx+1], data[byte_idx+2], data[byte_idx+3] ), 
                #                             byteorder='big', signed=True) \
                #         + self.df_cfg.at[iItem,'b coeff']

                # magnetic flux density in arbitrary unit
                # elif self.df_cfg.at[iItem,'type'] == 'B':
                #     self.df_mf.iat[iFrame,iItem] = \
                #         self.df_cfg.at[iItem,'a coeff'] \
                #             * int.from_bytes((data[byte_idx], data[byte_idx+1], data[byte_idx+2], data[byte_idx+3] ), 
                #                             byteorder='big', signed=True) \
                #         + self.df_cfg.at[iItem,'b coeff']

                # Eular angle in [rad] <S,32,12>
                # elif self.df_cfg.at[iItem,'type'] == 'EA':
                #     self.df_mf.iat[iFrame,iItem] = \
                #         self.df_cfg.at[iItem,'a coeff'] / 2**20 \
                #             * int.from_bytes((data[byte_idx], data[byte_idx+1], data[byte_idx+2], data[byte_idx+3] ), 
                #                             byteorder='big', signed=True) \
                #         + self.df_cfg.at[iItem,'b coeff']

                # voltage in [V] <S,16,5>
                # elif self.df_cfg.at[iItem,'type'] == 'V':
                #     self.df_mf.iat[iFrame,iItem] = \
                #         self.df_cfg.at[iItem,'a coeff'] / 2**11 \
                #             * int.from_bytes((data[byte_idx], data[byte_idx+1]), 
                #                             byteorder='big', signed=True) \
                #         + self.df_cfg.at[iItem,'b coeff']

                # SSD free space in [GB]
                # elif self.df_cfg.at[iItem,'type'] == 'disk space':
                #     self.df_mf.iat[iFrame,iItem] = \
                #             int.from_bytes((data[byte_idx], data[byte_idx+1]), 
                #                             byteorder='big', signed=True) / 2**7

                # error code
                # elif self.df_cfg.at[iItem,'type'] == 'ec':
                #     self.df_mf.iat[iFrame,iItem] = \
                #         int.from_bytes((data[byte_idx], data[byte_idx+1], data[byte_idx+2], data[byte_idx+3]), 
                #                         byteorder='big', signed=False)

                # PCB data
                #elif self.df_cfg.at[iItem,'type'] == 'data':                    
                #    for iii in (9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25):
                #    self.df_mf.iat[iFrame,iItem] = \
                #          self.df_cfg.at[iItem,'a coeff'] / 2**16 * 5.0 \
                #            * int.from_bytes((data[byte_idx],data[byte_idx+1]), 
                #                            byteorder='big', signed=True) \
                #        + self.df_cfg.at[iItem,'b coeff']
                
                # frame/loop counter
                # elif self.df_cfg.at[iItem,'type'] == 'counter':
                #     self.df_mf.iat[iFrame,iItem] = \
                #         int.from_bytes((data[byte_idx], data[byte_idx+1]), 
                #                         byteorder='big', signed=False)

                # others
                else:
                    # print(f'Error TLM RCV: ITEM={iItem} has no translation rule!')
                    self.df_mf.iat[iFrame,iItem] = np.nan
                    # self.df_mf.iat[iFrame,iItem] = \
                    #       self.df_cfg.at[iItem,'a coeff'] \
                    #         * int.from_bytes((data[byte_idx], data[byte_idx+1]), 
                    #                         byteorder='big', signed=False) \
                    #     + self.df_cfg.at[iItem,'b coeff']

            self.iLine += 1

        # clean up
        # self.df_mf.drop(self.df_mf.index[[0, -1]])

    #
    # Utilities
    #

    # Print major flame
    def print_mf(self, data):
        # header
        for k in range(self.__W2B * self.__LEN_HEADER):   
            print(hex(data[k]).zfill(4), end=' ')
        print('')   # linefeed
        
        # payload
        for j in range(4):                  
            print(f"message {0}-{j}: ",end='')
            for k in range(self.__W2B * int(self.__LEN_PAYLOAD / 4)): 
                print(hex(data[k + self.__W2B * (self.__LEN_HEADER + j * int(self.__LEN_PAYLOAD / 4))]).zfill(4), end=' ')
            print('')   # linefeed
        
        # empty line
        print('')  

    # Get a physical value from telemeter words
    def get_physical_value_from_tlm_words(self, iItem, data, idx_byte):
        byte_length = self.__W2B * int(self.TlmItemAttr[iItem]['word len'])
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


 

