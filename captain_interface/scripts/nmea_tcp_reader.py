#!/usr/bin/env python

import rospy
import socket

from nmea_msgs.msg import Sentence

def main():
    t = 0


    HOST = rospy.get_param("host", "192.168.1.91")  # The server's hostname or IP address
    PORT = rospy.get_param("port", 9002)  # The port used by the server
    OUTPUT_TOPIC = rospy.get_param("topic", "nmea_sentence")

    BUFFER_SIZE = 128
    buffer = ['']*BUFFER_SIZE
    buffer_index = 0

    sentence_pub = rospy.Publisher(OUTPUT_TOPIC, Sentence, queue_size=1)

    rospy.init_node('nmea_tcp_reader', anonymous=True)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        while(not rospy.is_shutdown()):
            data = s.recv(1024)
            data_chr = [chr(n) for n in data]
            if(len(data) < 1):
                continue
            
            for i in range(len(data_chr)):
                buffer[buffer_index] = data_chr[i]
                buffer_index += 1

                if(buffer[buffer_index-1] == '\n'):
                    #create ros message and send
                    line = ''.join(buffer[0:buffer_index]) 
                    msg = Sentence()
                    msg.sentence = line
                    sentence_pub.publish(msg)
                    print(line)
                    buffer_index = 0
                
                if(buffer_index > BUFFER_SIZE-1):
                    buffer_index = 0
            #print(buffer)
        print("Closing socket")
        s.close()

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass
