### Standard libraries
#import asyncio
#import decimal
import math
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
# W2B = 2
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

        # load configuration for word assignment
        # self.df_cfg = pd.read_excel('./config_tlm.xlsx', sheet_name=self.TLM_TYPE).dropna(how='all')
        try: 
            self.df_cfg = pd.read_excel('./config_tlm_2.xlsx', 
                                sheet_name=self.TLM_TYPE, header=0, index_col=None).dropna(how='all')
            # self.df_cfg = pd.read_excel('./config_tlm.xlsx', 
            #                     sheet_name=self.TLM_TYPE, header=0, index_col=None).dropna(how='all')
        except:
            print('Error TLM: "config_tlm.xlsx"!')
            print(self.TLM_TYPE)
            sys.exit()

        # print(self.df_cfg)
        self.NUM_OF_ITEMS = len(self.df_cfg.index)
        self.MAX_SUP_COM = self.df_cfg['sup com'].max()
        
        # initialize a DataFrame to store data of one major frame 
        self.df_mf = pd.DataFrame(index=[], columns=self.df_cfg['item']) 
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
    def datagram_received(self,data,addr):
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
            self.tlm_latest_data.df_smt = self.df_mf.tail(1)
        else:
            self.tlm_latest_data.df_pcm = self.df_mf.tail(1)

        # for debug
        # print("TLM notifies GUI of df:")
        # print(self.tlm_latest_values.df_smt)
        # print(self.tlm_latest_values.df_smt.index)
    

    # Internal method: 
    # Translate raw tlm data 
    def __translate(self, data):
        # sweep frames in a major frame
        for iFrame in range(self.__NUM_OF_FRAMES):
            #print(f"iLine: {self.iLine}")

            # byte index of the head of the frame (including header)
            byte_idx_frame_head = iFrame * self.__W2B * (self.__LEN_HEADER + self.__LEN_PAYLOAD)
            #print(f"byte_idx_frame_head: {byte_idx_frame_head}") 

            # initialize the row by filling wit NaN
            self.df_mf.loc[iFrame] = np.nan
            # print(self.df_mf)
            

            # pick up data from the datagram
            '''
            When w assgn < 0
            '''
            # Days from January 1st on GSE
            byte_idx = byte_idx_frame_head + self.__W2B * 0
            self.df_mf.iat[iFrame,0] =  (data[byte_idx]   >> 4  ) * 100 \
                                      + (data[byte_idx]   & 0x0F) * 10  \
                                      + (data[byte_idx+1] >> 4  ) * 1
        
            # GSE timestamp in [sec]
            byte_idx = byte_idx_frame_head + self.__W2B * 0
            self.df_mf.iat[iFrame,1] =  (data[byte_idx+1] & 0x0F) * 10  * 3600 \
                                      + (data[byte_idx+2] >> 4  ) * 1   * 3600 \
                                      + (data[byte_idx+2] & 0x0F) * 10  * 60   \
                                      + (data[byte_idx+3] >> 4  ) * 1   * 60   \
                                      + (data[byte_idx+3] & 0x0F) * 10         \
                                      + (data[byte_idx+4] >> 4  ) * 1          \
                                      + (data[byte_idx+4] & 0x0F) * 100 / 1000 \
                                      + (data[byte_idx+5] >> 4  ) * 10  / 1000 \
                                      + (data[byte_idx+5] & 0x0F) * 1   / 1000 

            '''
            When w assgn >= 0
            '''
            for iItem in range(2, self.NUM_OF_ITEMS):
                # designate byte addres with the datagram
                byte_idx = byte_idx_frame_head + self.__W2B * (self.__LEN_HEADER + int(self.df_cfg.at[iItem,'w idx']))
                
                #
                #   SMT
                #

                # DES timestamp in [sec]
                if self.df_cfg.at[iItem,'type'] == 'des time':
                    self.df_mf.iat[iFrame,iItem] = \
                        int.from_bytes((data[byte_idx], data[byte_idx+1], data[byte_idx+2], data[byte_idx+3]), 
                                        byteorder='big', signed=False) \
                        / 1000.0

                # pressure in [MPa] <S,16,5>
                elif self.df_cfg.at[iItem,'type'] == 'p':
                    self.df_mf.iat[iFrame,iItem] = \
                        self.df_cfg.at[iItem,'a coeff'] / 2**11 \
                            * int.from_bytes((data[byte_idx], data[byte_idx+1]), 
                                            byteorder='big', signed=True) \
                        + self.df_cfg.at[iItem,'b coeff']
                                    
                # temperature in [K] <S,16,-2>
                elif self.df_cfg.at[iItem,'type'] == 'T':
                    # TC thermoelectric voltage in [uV]
                    Vtc =  self.df_cfg.at[iItem,'a coeff'] / 2**18 * 1e6 \
                            * int.from_bytes((data[byte_idx], data[byte_idx+1]), 
                                            byteorder='big', signed=True) \
                         + self.df_cfg.at[iItem,'b coeff']
                    Ttc = self.uv2k(Vtc + Vcjc - Vaz, 'K')

                    self.df_mf.iat[iFrame,iItem] = Ttc

                # auto-zero coefficient in [uV]
                elif self.df_cfg.at[iItem,'type'] == 'az':
                    Vaz =  self.df_cfg.at[iItem,'a coeff'] / 2**18 * 1e6 \
                            * int.from_bytes((data[byte_idx], data[byte_idx+1]), 
                                            byteorder='big', signed=True) \
                         + self.df_cfg.at[iItem,'b coeff']
                    
                    self.df_mf.iat[iFrame,iItem] = Vaz

                # cold-junction compensation coefficient in [uV]
                elif self.df_cfg.at[iItem,'type'] == 'cjc':
                    cjc =  self.df_cfg.at[iItem,'a coeff'] / 2**18 \
                            * int.from_bytes((data[byte_idx], data[byte_idx+1]), 
                                            byteorder='big', signed=True) \
                         + self.df_cfg.at[iItem,'b coeff']
                    Rcjc = self.v2ohm(cjc)
                    Tcjc = self.ohm2k(Rcjc)
                    Vcjc = self.k2uv(Tcjc, 'K')

                    self.df_mf.iat[iFrame,iItem] = Vcjc

                # acceleration in [m/s2] <S,32,12>
                elif self.df_cfg.at[iItem,'type'] == 'a':
                    self.df_mf.iat[iFrame,iItem] = \
                        self.df_cfg.at[iItem,'a coeff'] / 2**20 \
                            * int.from_bytes((data[byte_idx], data[byte_idx+1], data[byte_idx+2], data[byte_idx+3] ), 
                                            byteorder='big', signed=True) \
                        + self.df_cfg.at[iItem,'b coeff']

                # angular velocity in [rad/s] <S,32,12>
                elif self.df_cfg.at[iItem,'type'] == 'omg':
                    self.df_mf.iat[iFrame,iItem] = \
                        self.df_cfg.at[iItem,'a coeff'] / 2**20 \
                            * int.from_bytes((data[byte_idx], data[byte_idx+1], data[byte_idx+2], data[byte_idx+3] ), 
                                            byteorder='big', signed=True) \
                        + self.df_cfg.at[iItem,'b coeff']

                # magnetic flux density in arbitrary unit
                elif self.df_cfg.at[iItem,'type'] == 'B':
                    self.df_mf.iat[iFrame,iItem] = \
                        self.df_cfg.at[iItem,'a coeff'] \
                            * int.from_bytes((data[byte_idx], data[byte_idx+1], data[byte_idx+2], data[byte_idx+3] ), 
                                            byteorder='big', signed=True) \
                        + self.df_cfg.at[iItem,'b coeff']

                # Eular angle in [rad] <S,32,12>
                elif self.df_cfg.at[iItem,'type'] == 'EA':
                    self.df_mf.iat[iFrame,iItem] = \
                        self.df_cfg.at[iItem,'a coeff'] / 2**20 \
                            * int.from_bytes((data[byte_idx], data[byte_idx+1], data[byte_idx+2], data[byte_idx+3] ), 
                                            byteorder='big', signed=True) \
                        + self.df_cfg.at[iItem,'b coeff']

                # voltage in [V] <S,16,5>
                elif self.df_cfg.at[iItem,'type'] == 'V':
                    self.df_mf.iat[iFrame,iItem] = \
                        self.df_cfg.at[iItem,'a coeff'] / 2**11 \
                            * int.from_bytes((data[byte_idx], data[byte_idx+1]), 
                                            byteorder='big', signed=True) \
                        + self.df_cfg.at[iItem,'b coeff']

                # relay status (boolean)
                elif self.df_cfg.at[iItem,'type'] == 'rel':
                    self.df_mf.iat[iFrame,iItem] = \
                        (data[byte_idx + int(self.df_cfg.at[iItem,'b coeff'])] & int(self.df_cfg.at[iItem,'a coeff'])) \
                            / self.df_cfg.at[iItem,'a coeff']

                # SSD free space in [GB]
                elif self.df_cfg.at[iItem,'type'] == 'disk space':
                    self.df_mf.iat[iFrame,iItem] = \
                            int.from_bytes((data[byte_idx], data[byte_idx+1]), 
                                            byteorder='big', signed=True) / 2**7

                # error code
                elif self.df_cfg.at[iItem,'type'] == 'ec':
                    self.df_mf.iat[iFrame,iItem] = \
                        int.from_bytes((data[byte_idx], data[byte_idx+1], data[byte_idx+2], data[byte_idx+3]), 
                                        byteorder='big', signed=False)

                #
                #   PCM
                #

                # analog pressure in [MPa]
                elif self.df_cfg.at[iItem,'type'] == 'p ana':
                    if iFrame % self.df_cfg.at[iItem,'sub com mod'] != self.df_cfg.at[iItem,'sub com res']: continue
                    
                    self.df_mf.iat[iFrame,iItem] = \
                          self.df_cfg.at[iItem,'a coeff'] / 2**16 * 5.0 \
                            * int.from_bytes((data[byte_idx],data[byte_idx+1]), 
                                            byteorder='big', signed=True) \
                        + self.df_cfg.at[iItem,'b coeff']

                # PCB data
                #elif self.df_cfg.at[iItem,'type'] == 'data':                    
                #    for iii in (9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25):
                #    self.df_mf.iat[iFrame,iItem] = \
                #          self.df_cfg.at[iItem,'a coeff'] / 2**16 * 5.0 \
                #            * int.from_bytes((data[byte_idx],data[byte_idx+1]), 
                #                            byteorder='big', signed=True) \
                #        + self.df_cfg.at[iItem,'b coeff']

                #
                #   Common
                #
                
                # frame/loop counter
                elif self.df_cfg.at[iItem,'type'] == 'counter':
                    self.df_mf.iat[iFrame,iItem] = \
                        int.from_bytes((data[byte_idx], data[byte_idx+1]), 
                                        byteorder='big', signed=False)

                # others
                else:
                    self.df_mf.iat[iFrame,iItem] = \
                          self.df_cfg.at[iItem,'a coeff'] \
                            * int.from_bytes((data[byte_idx], data[byte_idx+1]), 
                                            byteorder='big', signed=False) \
                        + self.df_cfg.at[iItem,'b coeff']

            self.iLine += 1


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
    def get_physical_value_from_tlm_words(self, data, datum_attr):
        # tlm_type  = 'smt'
        # head = datum_attr.head
        # byte_length = datum_attr.byte_length
        # signed = True
        total_bit_length = 8 * datum_attr.byte_length
        # fracttional_bit_length = total_bit_length - integer_bit_lengtu
        # integer_bit_length = 10
        # a_coeff = 1
        # b_coeff = 0
        
        byte_string = []
        for i in range(datum_attr.byte_length): byte_string.append(data[datum_attr.idx_byte_head+i])

        physical_value =  datum_attr.b_coeff \
                        + datum_attr.a_coeff \
                            * (int.from_bytes(byte_string, byteorder='big', signed=datum_attr.signed)) \
                            / 2**(datum_attr.total_bit_length - datum_attr.integer_bit_length)

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


class TlmDatumAttribution:
    def __init__(self, dfTlmDatumAttr):
        # self.tlm_type  = 'smt'
        self.idx_byte_head = 0
        self.byte_length = 2
        self.signed = True
        self.integer_bit_length = 10        # include sign bit if any
        self.a_coeff = 1
        self.b_coeff = 0

        self.total_bit_length = 8 * self.byte_length
        self.fractional_bit_length = self.total_bit_length - self.integer_bit_length

 

