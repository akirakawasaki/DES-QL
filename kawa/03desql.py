# standard libraries
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
    
    BUFSIZE = (LEN_HEADER + LEN_PAYLOAD) * NUM_OF_FRAMES * W2B      # 1088 bytes
    #BUFSIZE = 1280
    #BUFSIZE = 2176
    
    def __init__(self):
        self.HOST = socket.gethostname()

        #PORT = 70
        PORT = 49157    # for SMT
        #PORT = 49158    # for PCM
      
        # create a scoket for UPD/IP communication
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # bind a port
        self.s.bind((self.HOST, PORT))

        # load configuration
        self.df_cfg = pd.read_excel('./config_tlm.xlsx', sheet_name='smt')

        self.NUM_OF_ITEMS = len(self.df_cfg)
        self.SUP_COM      = self.df_cfg['sup com'].max()
        
        #
        self.df = pd.DataFrame(index=[], columns=self.df_cfg[['item']]) 
        self.data_idx = 0

    def __del__(self):
        self.s.close()

    def receive(self):
        self.data, self.addr = self.s.recvfrom(self.BUFSIZE)
        
    def reshape(self):
        # sweep frames in a major frame
        for ii in range(self.NUM_OF_FRAMES):
            adrs_tmp = self.W2B * (self.LEN_HEADER + self.LEN_PAYLOAD) * ii
            
            for iii in range(self.SUP_COM):
                i = self.data_idx + self.SUP_COM * ii + iii

                self.df.loc[i] = np.nan
                
                if iii == 0:
                    # days since January 1st 
                    self.df.iat[i,0] =  int(self.data[adrs_tmp+8+1] >> 4)   * 10**2 \
                                      + int(self.data[adrs_tmp+8+1] & 0x0F) * 10**1 \
                                      + int(self.data[adrs_tmp+8+2] >> 4)   * 10**0
            
                    # time in [sec]
                    self.df.iat[i,1] =  int(self.data[adrs_tmp+8+2] & 0x0F) * 10**1 * 3600 \
                                      + int(self.data[adrs_tmp+8+3] >> 4)   * 10**0 * 3600 \
                                      + int(self.data[adrs_tmp+8+3] & 0x0F) * 10**1 * 60 \
                                      + int(self.data[adrs_tmp+8+4] >> 4)   * 10**0 * 60 \
                                      + int(self.data[adrs_tmp+8+4] & 0x0F) * 10**1 \
                                      + int(self.data[adrs_tmp+8+5] >> 4)   * 10**0 \
                                      + int(self.data[adrs_tmp+8+5] & 0x0F) * 10**(-1) \
                                      + int(self.data[adrs_tmp+8+6] >> 4)   * 10**(-2) \
                                      + int(self.data[adrs_tmp+8+6] & 0x0F) * 10**(-3) \
                                      + int(self.data[adrs_tmp+8+7] >> 4)   * 10**(-4) \
                                      + int(self.data[adrs_tmp+8+7] & 0x0F) * 10**(-5)
            
                    # frame counter
                    self.df.iat[i,2] =  int(self.data[adrs_tmp+8+ 2*2+1]) * 2**16 \
                                      + int(self.data[adrs_tmp+8+32*2+1]) * 2**8 \
                                      + int(self.data[adrs_tmp+8+32*2+0])
                
                else:
                    self.df.iat[i,0] = self.df.iat[i-1,0]       # day
                    self.df.iat[i,1] = self.df.iat[i-1,1]       # time !TBFixed
                    self.df.iat[i,2] = self.df.iat[i-1,2]       # frame counter

                # pick up datum 
                for j in range(3, self.NUM_OF_ITEMS):
                    # handle sub-commutation
                    if self.df_cfg.at[j,'sub com mod'] > 1:
                        if (ii > 0 or iii > 0):
                            continue
                        
                        adrs = self.W2B * ( (self.LEN_HEADER + self.LEN_PAYLOAD) * self.df_cfg.at[j,'sub com res'] \
                                           + self.LEN_HEADER \
                                           + self.df_cfg.at[j,'w assgn'] )
                    
                    # handle normal commutation
                    elif self.df_cfg.at[j,'sup com'] == 1:
                        if self.df_cfg.at[j,'w assgn'] < 0:
                            continue
                        
                        if iii > 0:
                            continue

                        adrs =  adrs_tmp \
                              + self.W2B * (self.LEN_HEADER + self.df_cfg.at[j,'w assgn'])
                   
                    # handle super-commutation x2 !TBFixed
                    elif self.df_cfg.at[j,'sup com'] == 2:
                        if iii == 1:
                            adrs =  adrs_tmp \
                                  + self.W2B * (self.LEN_HEADER + self.df_cfg.at[j,'w assgn 2'])
                        else:
                            continue

                    # handle super-commutation x4 !TBFixed
                    elif self.df_cfg.at[j,'sup com'] == 4:
                        if iii == 1:
                            adrs =  adrs_tmp \
                                  + self.W2B * (self.LEN_HEADER + self.df_cfg.at[j,'w assgn 2'])
                        elif iii == 2:
                            adrs =  adrs_tmp \
                                  + self.W2B * (self.LEN_HEADER + self.df_cfg.at[j,'w assgn 3'])
                        elif iii == 3:
                            adrs =  adrs_tmp \
                                  + self.W2B * (self.LEN_HEADER + self.df_cfg.at[j,'w assgn 4'])
                        else:
                            print('Error: Super-comutation handling exception!') 

                    else:
                        print('Error: Commutation handling exception!')
                        
                    self.df.iat[i,j] =  self.df_cfg.at[j,'coeff a'] * (int(self.data[adrs]) * 2**16 + int(self.data[adrs+1])) \
                                      + self.df_cfg.at[j,'coeff b']
        
        self.data_idx += self.NUM_OF_FRAMES * self.SUP_COM 

    def save(self):
        print(self.df)
        self.df.to_excel('./data.xlsx')

# STEP 0: pre-process
smt = tlm()

# STEP 1: data revieve
smt.recv()

print(f"From: {smt.addr}")
print(f"To  : {socket.gethostbyname(smt.HOST)}")

#print(type(smt.data))

for i in range(8):
    print(f"message {i+1}-0: {smt.data[i*136:i*136+8]}")
    for j in range(8):
        print(f"message {i+1}-{j+1}: {smt.data[i*136+j*16+8:i*136+j*16+8+16]}")

for k in range(smt.BUFSIZE):
    print(hex(smt.data[k]))


# STEP 2: data reshape
smt.reshape()

print(smt.df)


# STEP 4: data display


# STEP 5: data save
smt.save()

# STEP F: post-process 
del smt























