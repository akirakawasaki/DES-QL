# standard libraries
import decimal
import math
import socket

# third-party libraries
import numpy as np
import pandas as pd

# local libraries
# n/a


class tlm():
    
    W2B = 2

    NUM_OF_FRAMES = 8

    LEN_HEADER  = 4
    LEN_PAYLOAD = 64
    
    BUFSIZE = W2B * (LEN_HEADER + LEN_PAYLOAD) * NUM_OF_FRAMES       # 1088 bytes
    #BUFSIZE = 1088
    #BUFSIZE = 1280
    #BUFSIZE = 2176

    '''
    Convert thermoelectric voltage (in uV) to temperature (in K)
    '''
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

    '''
    Convert temperature (in K) to thermoelectric voltage (in uV)
    '''
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

    '''
    Convert thermistor voltage to resistance
    '''
    def v2ohm(self, val):
        # Ref.: Converting NI 9213 Data (FPGA Interface)
        return (1.0e4 * 32.0 * val) / (2.5 - 32.0 * val)

    '''
    Convert thermistor resistance to temperature (in K)
    '''
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
    
    '''
    Constractor
    '''
    def __init__(self, tlm_type):
        #self.HOST = socket.gethostname()
        self.HOST = ''
        self.TLM_TYPE = tlm_type

        #print(self.TLM_TYPE)
        #print(self.BUFSIZE)

        #self.PORT = 70
        if self.TLM_TYPE == 'smt':
            self.PORT = 49157
            self.DATA_PATH = './data_smt.xlsx'
        elif self.TLM_TYPE == 'pcm':
            self.PORT = 49158
            self.DATA_PATH = './data_pcm.xlsx'
        else:
            print('Error: Type of the telemeter is wrong!')

        #print(self.PORT)

        # create a scoket for UPD/IP communication
        self.udpSoc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # bind a port
        self.udpSoc.bind((self.HOST, self.PORT))

        # load configuration
        if self.TLM_TYPE == 'smt':
            self.df_cfg = pd.read_excel('./config_tlm.xlsx', sheet_name='smt')
        elif self.TLM_TYPE == 'pcm':
            self.df_cfg = pd.read_excel('./config_tlm.xlsx', sheet_name='pcm')

        self.NUM_OF_ITEMS = len(self.df_cfg.index)
        self.SUP_COM      = self.df_cfg['sup com'].max()
        
        # configure output file
        self.df = pd.DataFrame(index=[], columns=self.df_cfg['item']) 
        
        # initialize data index
        self.iData = 0

    '''
    Destractor
    '''
    def __del__(self):
        self.udpSoc.close()

    def save(self):
        self.df.to_excel(self.DATA_PATH)

    def receive(self):
        #print('tlm.receive called')
        self.data, self.addr = self.udpSoc.recvfrom(self.BUFSIZE)

    def reshape(self):
        # sweep frames in a major frame
        for iFrame in range(self.NUM_OF_FRAMES):
            #print(f"iData: {self.iData}")

            adrs_tmp = iFrame * self.W2B * (self.LEN_HEADER + self.LEN_PAYLOAD)
            #print(f"adrs_tmp: {adrs_tmp}") 

            # initialize the row by filling wit NaN
            self.df.loc[self.iData] = np.nan
            
            # pick up data from the datagram
            '''
            When w assgn < 0
            '''
            # Days from January 1st on GSE
            adrs = adrs_tmp + self.W2B * 0
            self.df.iat[self.iData,0] =  (self.data[adrs]   >> 4  ) * 100 \
                                       + (self.data[adrs]   & 0x0F) * 10  \
                                       + (self.data[adrs+1] >> 4  ) * 1
        
            # GSE timestamp in [sec]
            adrs = adrs_tmp + self.W2B * 0
            self.df.iat[self.iData,1] =  (self.data[adrs+1] & 0x0F) * 10  * 3600 \
                                       + (self.data[adrs+2] >> 4  ) * 1   * 3600 \
                                       + (self.data[adrs+2] & 0x0F) * 10  * 60   \
                                       + (self.data[adrs+3] >> 4  ) * 1   * 60   \
                                       + (self.data[adrs+3] & 0x0F) * 10         \
                                       + (self.data[adrs+4] >> 4  ) * 1          \
                                       + (self.data[adrs+4] & 0x0F) * 100 / 1000 \
                                       + (self.data[adrs+5] >> 4  ) * 10  / 1000 \
                                       + (self.data[adrs+5] & 0x0F) * 1   / 1000 

            '''
            When w assgn >= 0
            '''   
            for iItem in range(2, self.NUM_OF_ITEMS):
                # designate byte addres with the datagram
                adrs = adrs_tmp + self.W2B * (self.LEN_HEADER + self.df_cfg.at[iItem,'w assgn'])

                # frame/loop counter
                if self.df_cfg.at[iItem,'type'] == 'counter':
                    self.df.iat[self.iData,iItem] = \
                        int.from_bytes((self.data[adrs], self.data[adrs+1]), byteorder='big', signed=False)
                    #self.df.iat[self.iData,iItem] =  self.data[adrs]   * 2**8 \
                    #                               + self.data[adrs+1]
                
                # DES timestamp in [sec]
                elif self.df_cfg.at[iItem,'type'] == 'des time':
                    self.df.iat[self.iData,iItem] = \
                        int.from_bytes((self.data[adrs], self.data[adrs+1], self.data[adrs+2], self.data[adrs+3]), 
                                        byteorder='big', signed=False) \
                            / 1000.0
                    #self.df.iat[self.iData,iItem] = (  self.data[adrs]   * 2**(24) \
                    #                                 + self.data[adrs+1] * 2**(16) \
                    #                                 + self.data[adrs+2] * 2**(8)  \
                    #                                 + self.data[adrs+3] * 2**(0)  ) / 1000.0

                # pressure in [MPa]
                elif self.df_cfg.at[iItem,'type'] == 'p':
                    self.df.iat[self.iData,iItem] = \
                          self.df_cfg.at[iItem,'coeff a'] / 2**11 \
                            * int.from_bytes((self.data[adrs], self.data[adrs+1]), byteorder='big', signed=True) \
                        + self.df_cfg.at[iItem,'coeff b']
                                    
                # temperature in [K]
                elif self.df_cfg.at[iItem,'type'] == 'T':
                    # TC thermoelectric voltage in [uV]
                    Vtc =  self.df_cfg.at[iItem,'coeff a'] / 2**18 * 1e6 \
                            * int.from_bytes((self.data[adrs], self.data[adrs+1]), byteorder='big', signed=True) \
                         + self.df_cfg.at[iItem,'coeff b']
                    Ttc = self.uv2k(Vtc + Vcjc - Vaz, 'K')

                    self.df.iat[self.iData,iItem] = Ttc

                    #print(f"Vtc : {Vtc}")
                    #print(f"Vcjc: {Vcjc}")
                    #print(f"Vaz : {Vaz}")

                # auto-zero coefficient in [uV]
                elif self.df_cfg.at[iItem,'type'] == 'az':
                    Vaz =  self.df_cfg.at[iItem,'coeff a'] / 2**18 * 1e6 \
                            * int.from_bytes((self.data[adrs], self.data[adrs+1]), byteorder='big', signed=True) \
                         + self.df_cfg.at[iItem,'coeff b']
                    
                    self.df.iat[self.iData,iItem] = Vaz

                # cold-junction compensation coefficient in [uV]
                elif self.df_cfg.at[iItem,'type'] == 'cjc':
                    cjc =  self.df_cfg.at[iItem,'coeff a'] / 2**18 \
                            * int.from_bytes((self.data[adrs], self.data[adrs+1]), byteorder='big', signed=True) \
                         + self.df_cfg.at[iItem,'coeff b']
                    Rcjc = self.v2ohm(cjc)
                    Tcjc = self.ohm2k(Rcjc)
                    Vcjc = self.k2uv(Tcjc, 'K')

                    #print(f"CJC : {cjc}")
                    #print(f"Rcjc: {Rcjc}")
                    #print(f"Tcjc: {Tcjc}")
                    #print(f"Vcjc: {Vcjc}")

                    self.df.iat[self.iData,iItem] = Vcjc

                # analog pressure in [MPa]
                elif self.df_cfg.at[iItem,'type'] == 'p ana':
                    if iFrame % self.df_cfg.at[iItem,'sub com mod'] != self.df_cfg.at[iItem,'sub com res']: continue
                    
                    self.df.iat[self.iData,iItem] = \
                          self.df_cfg.at[iItem,'coeff a'] / 2**16 * 5.0 \
                            * int.from_bytes((self.data[adrs],self.data[adrs+1]), byteorder='big', signed=True) \
                        + self.df_cfg.at[iItem,'coeff b']

                # voltage in [V]
                elif self.df_cfg.at[iItem,'type'] == 'V':
                    self.df.iat[self.iData,iItem] = \
                          self.df_cfg.at[iItem,'coeff a'] \
                            * int.from_bytes((self.data[adrs],self.data[adrs+1]), byteorder='big', signed=True) \
                        + self.df_cfg.at[iItem,'coeff b']

                # relay status (boolean)
                elif self.df_cfg.at[iItem,'type'] == 'rel':
                    self.df.iat[self.iData,iItem] = \
                        (self.data[adrs + self.df_cfg.at[iItem,'coeff b']] & int(self.df_cfg.at[iItem,'coeff a'])) \
                            / self.df_cfg.at[iItem,'coeff a']
                    #self.df.iat[self.iData,iItem] = \
                    #   int.from_bytes((self.data[adrs],self.data[adrs+1]), byteorder='big', signed=False)

                # others
                else:
                    self.df.iat[self.iData,iItem] = \
                          self.df_cfg.at[iItem,'coeff a'] \
                            * int.from_bytes((self.data[adrs], self.data[adrs+1]), byteorder='big', signed=False) \
                        + self.df_cfg.at[iItem,'coeff b']

            self.iData += 1


#--- MAIN PROCEDURE STARTS HERE ------------------------------
print('DES-QL Launched!')
print('')

### STEP 0: initialize 
smt = tlm('smt')
#smt = tlm('pcm')
#pcm = tlm('pcm')

NNN = 0
#while NNN < 1:
#while NNN <= 500:
while NNN <= 10000:
    ### STEP 1: data receive
    smt.receive()

    # for debug
    '''
    print(f"From: {smt.addr}")
    print(f"To  : {socket.gethostbyname(smt.HOST)}")
    print('')
    '''
    
    '''
    for i in range(smt.NUM_OF_FRAMES):
        adrs_tmp = i * smt.W2B * (smt.LEN_HEADER + smt.LEN_PAYLOAD)

        # header
        print(f"message {i}-H: ",end='') 
        for k in range(smt.W2B * smt.LEN_HEADER): 
            print(hex(smt.data[k + adrs_tmp]).zfill(4), end=' ')
        print('')

        # payload
        for j in range(4):
            print(f"message {i}-{j}: ",end='')
            for k in range(smt.W2B * int(smt.LEN_PAYLOAD / 4)): 
                print(hex(smt.data[k + adrs_tmp + smt.W2B * (smt.LEN_HEADER + j * int(smt.LEN_PAYLOAD / 4))]).zfill(4), end=' ')
            print('')
    print('')
    '''

    #for k in range(smt.BUFSIZE):
    #    print(hex(smt.data[k]))

    #print(f"SUP_COM: {smt.SUP_COM}")
    #print('')


    ### STEP 2: data reshape
    smt.reshape()

    # for debug
    #print(smt.df)


    ### STEP 3: data save
    #if NNN % 1 == 0:
    #if NNN % 100 == 0:
    if NNN % 500 == 0:
        print(f"NNN : {NNN}")
        print(f"From: {smt.addr}")
        #print(f"To  : {socket.gethostbyname(smt.HOST)}")
        print('')
        print(smt.df)
        smt.save()


    ### STEP 4: data display
    # N/A

    NNN += 1

# for debug
'''
print(smt.uv2k(-1.0,'K')+273.15)
print(smt.uv2k(1.0,'K')+273.15)
print(smt.uv2k(20643.0,'K')+273.15)
print(smt.uv2k(20645.0,'K')+273.15)
print('')
print(smt.k2uv(-1.0-273.15,'K'))
print(smt.k2uv(1.0-273.15,'K'))
print(smt.k2uv(500.0-273.15,'K'))
'''

### STEP F: finalize
del smt
#del pcm























