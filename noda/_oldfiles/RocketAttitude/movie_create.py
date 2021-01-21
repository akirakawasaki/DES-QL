# edit by kazama tomoya 3/2/2020

import cv2
import glob

###################################################################################################################################################################################################

header = "TIME-"                                                                    # image file header
frame_rate = 10                                                                     # set frame rate
out_put_file = './movie/Movie.mp4'                                                  # output file name

###################################################################################################################################################################################################

a=sorted(glob.glob("./gif/*.png"))                                                  # sort image file
fourcc = cv2.VideoWriter_fourcc('m','p','4','v')                                    # movie format
video = cv2.VideoWriter(out_put_file, fourcc, frame_rate, (2400,2400))              # video details

for i in range(1, len(a)):
    print(a[i])
    img = cv2.imread(a[i])                                                          # change image format to opencv format
    img = cv2.resize(img, (2400,2400))                                              # resize image
    video.write(img)                                                                # add movie on las frame

video.release()                                                                     # delete video config

###################################################################################################################################################################################################
