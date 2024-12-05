#!/usr/bin/env python3

from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import Factory
from twisted.internet import reactor

MAX_USERS = 100
MAX_MSG_LENGTH = 255
MAX_USER_LENGTH = 16
PORT = 8000

class ChatProtocol(LineReceiver):
    def __init__(self, factory):
        self.factory = factory
        self.name = None
        self.palabrasprohibidas = self.prohibidas("Prohibida.txt")


  	def prohibidas(self,archivo):
        fd = open(archivo)
        vp = []
        for linea in fd:
            vp = vp + [linea[:-1]]
        return vp

    def connectionMade(self):
       if len(self.factory.users) == MAX_USERS:
            self.sendLine(b"-1")
            self.transport.loseConnection()
        else:
            self.sendLine(b"FTR0 1 1 0")
            userlist = " ".join(self.factory.users.keys()).encode("utf-8")
            self.sendLine(b"USR" + userlist)

    def connectionLost(self, reason):
        if self.name:
            del self.factory.users[self.name]
            self.broadcastMessage("OUT" + self.name)

    def lineReceived(self, line):
        line = line.decode("utf-8")

        if line.startswith("NME") and not self.name:
            name = line[3:]
            if " " in name:
                self.sendLine(b"-2")
            elif len(name) > MAX_USER_LENGTH:
                self.sendLine(b"-3")
            elif name in self.factory.users.keys():
                self.sendLine(b"-4")
            else:
                self.name = name
                self.factory.users[self.name] = self
                self.broadcastMessage("INN" + self.name)
                self.sendLine(b"+")
        elif line.startswith("MSG") and self.name:
            self.factory.timer.reset(10)
            message = line[3:]
            if len(message) > MAX_MSG_LENGTH:
                self.sendLine(b"-5")
            else:
                msg = message.split()
                for i in range (len(msg)):
                    if(msg[i] in self.palabrasprohibidas):
                        msg[i] = "#####"
                message = ' '.join(msg)
                message = "MSG{} {}".format(self.name, message)
                self.broadcastMessage(message)
                self.sendLine(b"+")
        elif line == "WRT":
            message = "WRT"+self.name
            self.broadcastMessage(message)

            
        else:
            self.sendLine(b"-0")

    def broadcastMessage(self, message):
        for protocol in self.factory.users.values():
            if protocol != self:
                protocol.sendLine(message.encode("utf-8"))

class ChatFactory(Factory):
    def __init__(self):
        self.users = {}
        self.timer = reactor.callLater(10,self.noMSG)

    def buildProtocol(self, addr):
        return ChatProtocol(self)
        
    def noMSG(self):
        msg = "NOP10"
        for protocol in self.users.values():
                protocol.sendLine(msg.encode("utf-8"))
        self.timer = reactor.callLater(10,self.noMSG)

if __name__ == "__main__":
	reactor.listenTCP(PORT, ChatFactory())
	reactor.run()
