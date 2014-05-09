import socket
import base64
import sys
from select import select
from threading import Thread, Timer
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

	
if __name__ == "__main__":

	# t = Timer(1.0, hello)
	# t.start()
	receiver = Thread(target=receiver)
	receiver.start()
	sender = Thread(target=sender)
	sender.start()
