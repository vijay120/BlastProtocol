import socket
import base64
import sys
from select import select
<<<<<<< HEAD
from threading import Thread, Event, Timer
=======
from threading import Thread, Timer
>>>>>>> 60b92298b86fd780ea409627a4b39c75afdf889e
import time

UDP_PORT = 4019
UDP_IP = "127.0.0.1"

PROTO = "prot"
NODATA = ""
DATA = 2
SIZEOFBYTE = 8
NUMFRAGS = 32

def hello():
    print "hello, world"

def fragment_factory(MessageId, DataLength, NumFrags, PacketType, FragMask, Data):
	binProto = ''.join(format(ord(x), 'b') for x in PROTO) + "0000"
	binMessageId = '{0:032b}'.format(MessageId)
	binDataLength = '{0:032b}'.format(DataLength)
	binNumFrags = '{0:016b}'.format(NumFrags)
	binPacketType = '{0:016b}'.format(PacketType)
	binFragMask = '{0:032b}'.format(1 << FragMask)
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


def sender():

	sockSend = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
 	
 	# step 1
 	for i in range(0, NUMFRAGS):
 		MessageId = 1
 		Length = 100
 		fragment = fragment_factory(MessageId, Length, NUMFRAGS, 2, i, "Hello: " + str(i))
 		sockSend.sendto(fragment, (UDP_IP, UDP_PORT))

	sockSend.close()
	print "sender closed"


def receiver():
	sockRec = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sockRec.bind((UDP_IP, UDP_PORT))
	received = False
	counter = 0
	ListOfMessages = []

	while (counter < 32):
		data, addr = sockRec.recvfrom(65535)
		print "received message:", data
		ListOfMessages.append(data)
		counter = counter+1
		print counter

	FirstProto = decode_fragment(ListOfMessages[0])["Proto"]
	FirstMid = decode_fragment(ListOfMessages[0])["MessageId"]
	NumFrags = decode_fragment(ListOfMessages[0])["NumFrags"]

	bitFragsArrived = []
	for i in range(0, NumFrags):
		bitFragsArrived.append(False)

	for data in ListOfMessages:

		Dict = decode_fragment(data)

		if Dict["Proto"] != FirstProto:
			print "invalid message"

		if Dict["MessageId"] != FirstMid:
			print "invalid message"

		if Dict["PacketType"] != DATA:
			print "invalid message"

		bitFragsArrived[Dict["FragMask"]] = True

		print str(Dict["MessageId"]) + ", " + str(Dict["FragMask"] + 1) + " of " + str(Dict["NumFrags"]) + " : " + Dict["Data"]


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
	
if __name__ == "__main__":

	receiver = Thread(target=receiver)
	receiver.start()
	sender = Thread(target=sender)
	sender.start()

	print "Time: %s - start..." % time.asctime()
	tim = TimerReset(5, hello)
	tim.start()
	#print "Time: %s - sleeping for 4..." % time.asctime()
	time.sleep (4)
	tim.reset()
	time.sleep(10)
	tim = TimerReset(4,hello)
	tim.start()
	#print "Time: %s - sleeping for 10..." % time.asctime()
	#time.sleep (10)
	#print "Time: %s - end..." % time.asctime()

	print "\n\n"

