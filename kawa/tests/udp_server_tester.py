import socket
import sys
import time

# initialize
HOST = socket.gethostbyname(socket.gethostname())
PORT = 0

TYPE = sys.argv[1]
if TYPE == 'smt':
    PORT = 49157        # smt
elif TYPE == 'pcm':
    PORT = 49158        # pcm
else :
    print("ERROR: TYPE is wrong!")
    sys.exit()
    
print(TYPE, HOST, PORT)

for NNN in range(10):
#for NNN in range(1000):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udpSoc:
        retval = udpSoc.sendto((NNN).to_bytes(4, byteorder='big'),(HOST,PORT))
        print(NNN, retval)

    #time.sleep(1e-3)
    time.sleep(1)

