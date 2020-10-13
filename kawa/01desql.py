# standard libraries
import socket 

# third-party libraries
import pandas as pd

# local libraries
# non


class data_recv():
    def __init__(self):
       
        # host name of this machine        
        self.HOST = socket.gethostname()

        #self.PORT = 70
        self.PORT = 49157    # to hear from SMT
        #self.PORT = 49158    # to hear from PCM

        self.BUFSIZE = (4 + 64) * 8 * 2     # 1088 bytes
        #self.BUFSIZE = 2176
        #self.BUFSIZE = 3000
        
        # create a scoket for UPD/IP communication
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # bind a port
        self.s.bind(self.HOST, self.PORT)


        # load configuration
        self.df_cfg = pd.read_excel('./config_tlm.xlsx', sheet_name='smt')
        self.df_cfg[['item']].head()

        #
        self.df = pd.DataFrame(index=[], columns=self.df_cfg[['item']]) 
    
    def recv(self):

        self.data, self.addr = self.s.recvfrom(self.BUFSIZE)
        
        #print(f"From: {self.addr}")
        #print(f"To  : {socket.gethostbyname(self.HOST)}")

        #for i in range(8):
        #    print(f"message {i+1}-0: {data[i*136:i*136+8]}")
        #    for j in range(8):
        #        print(f"message {i+1}-{j+1}: {data[i*136+j*16+8:i*136+j*16+8+16]}")

    def reshape(self):
        
        


    def scaling(self):
        

    def save(self):
        df.to_excel('./data.xlsx')

    def __del__(self):
        self.s.close()


# STEP 1: data revieve
tlm = data_recv()
tlm.recv()

print(f"From: {tlm.addr}")
print(f"To  : {socket.gethostbyname(tlm.HOST)}")

#print(type(tlm.data))

for i in range(8):
    print(f"message {i+1}-0: {tlm.data[i*136:i*136+8]}")
    for j in range(8):
        print(f"message {i+1}-{j+1}: {tlm.data[i*136+j*16+8:i*136+j*16+8+16]}")

for k in range(tlm.BUFSIZE)
    print(hex(tlm.data[k])


# STEP 2: data reshape


# STEP 3: data scaling


# STEP 4: data display


# STEP 5: data save




# post process 
del tlm























