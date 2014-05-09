import socket
import base64
import sys
from select import select
from threading import Thread, Event, Timer
import time
import select

UDP_PORT_SENDER = 4500
UDP_PORT_RECEIVER = 4501
UDP_IP = "127.0.0.1"

PROTO = "prot"
NODATA = ""
DATA = 2
SRC = 1
SIZEOFBYTE = 8
NUMFRAGS = 32
RETRYATTEMPTS = 0


globalIsOver = False

def fragment_factory(MessageId, DataLength, NumFrags, PacketType, FragMask, Data):
	binProto = ''.join(format(ord(x), 'b') for x in PROTO) + "0000"
	binMessageId = '{0:032b}'.format(MessageId)
	binDataLength = '{0:032b}'.format(DataLength)
	binNumFrags = '{0:016b}'.format(NumFrags)
	binPacketType = '{0:016b}'.format(PacketType)
	binFragMask = FragMask
	binData = ''.join('{:08b}'.format(ord(c)) for c in Data)
	return binProto + binMessageId + binDataLength + binNumFrags + binPacketType + binFragMask + binData

def decode_fragment(fragment):
	Proto = int(fragment[0:32], 2)
	MessageId = int(fragment[32:64], 2)
	DataLength = int(fragment[64:96], 2)
	NumFrags = int(fragment[96:112], 2)
	PacketType = int(fragment[112:128], 2)
	FragMask = 31 - fragment[128:160].find('1')
	print "fragment is: "
	print fragment[160:]
	Data = "".join(chr(int(fragment[i: i+8], 2)) for i in xrange(160, len(fragment), SIZEOFBYTE))

	return {	"Proto": Proto,
				"MessageId": MessageId,
				"DataLength": DataLength,
				"NumFrags": NumFrags,
				"PacketType": PacketType,
				"FragMask": FragMask,
				"Data": Data
			}

def printFragmentDict(Dict):
	print str(Dict["MessageId"]) + ", " + str(Dict["FragMask"] + 1) + " of " + str(Dict["NumFrags"]) + " : " + Dict["Data"]

def checkAllFragArrived(list):

	for truth in list:
		if truth == False:
			return False
	return True

def sender():

	sockSend = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
 	sockSend.bind((UDP_IP, UDP_PORT_SENDER))

 	# step 1
 	for i in range(0, NUMFRAGS):
 		MessageId = 1
 		Length = 100
 		fragment = fragment_factory(MessageId, Length, NUMFRAGS, DATA, '{0:032b}'.format(1 << i), "Hello: " + str(i))
 		sockSend.sendto(fragment, (UDP_IP, UDP_PORT_RECEIVER))

 		#added
 	data, addr = sockSend.recvfrom(65535)
 	print "at sender"
 	print data
 		#added

	sockSend.close()
	print "sender closed"


def receiver():
	sockRec = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sockRec.bind((UDP_IP, UDP_PORT_RECEIVER))
	received = False
	counter = 0
	attempts = 0
	potentialRead = [sockRec]

	lastFragTimer = TimerReset(10, lastFragExpired)
	retryTimer = TimerReset(5, retryExpired)
	#ListOfMessages = []

	FirstProto = 0
	FirstMid = 0

	bitFragsArrived = []
	for i in range(0, NUMFRAGS):
		bitFragsArrived.append(False)

	while (not globalIsOver):
		ready_to_read, dont_care, don_care = select.select(potentialRead, [],[],1)
		if (len(ready_to_read) == 1):
			print ready_to_read
			data, addr = sockRec.recvfrom(65535)
			ready_to_read = None
			print "received message:", data
			counter = counter + 1

			#Decode Fragment
			thisFrag = decode_fragment(data)

			#Check that it's a valid fragment
			if thisFrag["PacketType"] != DATA:
				print "invalid fragment"
				break

			#Print contents of Fragment
			printFragmentDict(thisFrag)

			fragIndex = thisFrag["FragMask"]
			bitFragsArrived[fragIndex] = True

			#if this is the first fragment to arrive, save msg id
			if counter == 1:
				FirstProto = thisFrag["Proto"]
				FirstMid = thisFrag["MessageId"]
			else:
				if thisFrag["Proto"] != FirstProto:
					print "NOT THE SAME PROTOCOL!"
					break
				if thisFrag["MessageId"] != FirstMid:
					print "NOT THE SAME MESSAGE ID!"
					break

			if fragIndex == 0:
				lastFragTimer.start()
				
			if (fragIndex == 31) and (attempts == 0):
				lastFragTimer.cancel()
				attempts = 1
				if checkAllFragArrived(bitFragsArrived) == False:
					retryTimer.start()

			if checkAllFragArrived(bitFragsArrived) == True:
				retryTimer.cancel()
				print "Yay all fragments arrived!"
				break
			#counter = counter+1

			print counter

	# FirstProto = decode_fragment(ListOfMessages[0])["Proto"]
	# FirstMid = decode_fragment(ListOfMessages[0])["MessageId"]
	# NumFrags = decode_fragment(ListOfMessages[0])["NumFrags"]



	# for data in ListOfMessages:

	# 	Dict = decode_fragment(data)

	# 	if Dict["Proto"] != FirstProto:
	# 		print "invalid message"

	# 	if Dict["MessageId"] != FirstMid:
	# 		print "invalid message"

	# 	if Dict["PacketType"] != DATA:
	# 		print "invalid message"

	# 	bitFragsArrived[Dict["FragMask"]] = True

	# 	print str(Dict["MessageId"]) + ", " + str(Dict["FragMask"] + 1) + " of " + str(Dict["NumFrags"]) + " : " + Dict["Data"]


	FragMaskToSend = "".join(bitFragsArrived)
	print FragMaskToSend

	SrcMessage = fragment_factory(1, 100, 1, SRC, FragMaskToSend, "")
	print SrcMessage

	sockRec.sendto(SrcMessage, (UDP_IP, UDP_PORT_SENDER))

	sockRec.close()
	print "receiver closed"



def TimerReset(*args, **kwargs):
    """ Global function for Timer """
    return _TimerReset(*args, **kwargs)


class _TimerReset(Thread):
    """Call a function after a specified number of seconds:

    t = TimerReset(30.0, f, args=[], kwargs={})
    t.start()
    t.cancel() # stop the timer's action if it's still waiting
    """

    def __init__(self, interval, function, args=[], kwargs={}):
        Thread.__init__(self)
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.finished = Event()
        self.resetted = True

    def cancel(self):
        """Stop the timer if it hasn't finished yet"""
        self.finished.set()

    def run(self):
        print "Time: %s - timer running..." % time.asctime()

        while self.resetted:
            print "Time: %s - timer waiting for timeout in %.2f..." % (time.asctime(), self.interval)
            self.resetted = False
            self.finished.wait(self.interval)

        if not self.finished.isSet():
            self.function(*self.args, **self.kwargs)
        self.finished.set()
        print "Time: %s - timer finished!" % time.asctime()

    def reset(self, interval=None):
        """ Reset the timer """

        if interval:
            print "Time: %s - timer resetting to %.2f..." % (time.asctime(), interval)
            self.interval = interval
        else:
            print "Time: %s - timer resetting..." % time.asctime()

        self.resetted = True
        self.finished.set()
        self.finished.clear()



#
# Usage examples
#
def hello():
    print "Time: %s - hello, world" % time.asctime()

def lastFragExpired():
	print "Last Frag Timer Expired"

def retryExpired():
	print "Retry Expired for the first time"
	retryTimer = TimerReset(2, secondRetry)
	retryTimer.start()

def secondRetry():
	print "Retry Expired for the second time"
	retryTimer = TimerReset(2, lastRetry)
	retryTimer.start()

def lastRetry():
	print "Retry Expired for the third/last time"
	global globalIsOver
	globalIsOver = True
	
if __name__ == "__main__":
	receiver = Thread(target=receiver)
	sender = Thread(target=sender)
	receiver.start()
	sender.start()

	# print "Time: %s - start..." % time.asctime()
	# tim = TimerReset(5, hello)
	# tim.start()
	# #print "Time: %s - sleeping for 4..." % time.asctime()
	# time.sleep (4)
	# tim.reset()
	# time.sleep(10)
	# tim = TimerReset(4,hello)
	# tim.start()
	# #print "Time: %s - sleeping for 10..." % time.asctime()
	# #time.sleep (10)
	# #print "Time: %s - end..." % time.asctime()

	# print "\n\n"

