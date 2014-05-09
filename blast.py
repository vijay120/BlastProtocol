import socket
import base64
import sys
from select import select
from threading import Thread

class blastProtocol:

	def _init_(self):
		self.UDP_PORT = 5005
		self.UDP_IP = "127.0.0.1"

	def sender(self):
		protnum = "four"
		midField = "000000000000000000000000000000"
		lengthField = "000000000000000000000000000000"
		NumFrags = "0000000000000000"
		typeField = "0000000000000000"
		fragMaskField = "000000000000000000000000000000"
		
		MESSAGE = protnum + MID + lengthField + NumFrags + typeField + fragMaskField
		
		sockSend = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

		for i in range(0,100):
			sockSend.sendto(MESSAGE, (self.UDP_IP, self.UDP_PORT))

		sockSend.close()
		print "sender closed"


	def receiver(self):
		sockRec = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sockRec.bind((self.UDP_IP, self.UDP_PORT))
		received = False
		while (received == False):
			data, addr = sockRec.recvfrom(1024)
			print "received message:", data

		sockRec.close()
		print "receiver closed"

	
if __name__ == "__main__":

	senderInt = blastProtocol()
	receiverInt = blastProtocol()
	sender = Thread(target=blastProtocol.sender(), args = senderInt)
	sender.start()
	receiver = Thread(target=blastProtocol.receiver(), args = receiverInt)
	receiver.start()
