#!/usr/bin/python
""" This module provide a MirrorClient class that listen to a Mirror device
(from Violet). This class is a little adaptation to a twisted oriented code
found in the following article http://www.dad3zero.net/201012/mirror-en-python/
"""


import binascii
from twisted.internet import reactor

class MirrorClient(object):
    """ The MirrorClient listen to a device (eg: /dev/mirror) and call the
    registered callbacks (from add_callback method) with the tag and associtated
    state of the tag.
    """
    def __init__(self, device):
        """ Init the MirrorClient with an associated device to listen.
        """
        self.device = open(device, 'rb')
        self.clients = set()

    def start(self):
        """ When the start method is called, the listen method is called inside
        a thread.
        """
        reactor.callInThread(self.listen)

    def add_callback(self, callback):
        """ Add a callback which will be called when an event is read from the
        defined device.
        """
        self.clients.add(callback)

    def listen(self):
        """ Listen until the reactor is stopped and read the device. When a tag
        is detected or removed call registered callbacks.
        """
        while reactor.running:
            data = self.device.read(16)
            if data != '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00': # pylint: disable=C0301
                tag = binascii.hexlify(data)[4:]
                # Sometime a ghost tag is detected by the Mirror device.
                if tag != '0000000000000000000000000000':
                    state = True if data[0:2] == '\x02\x01' else False
                    self.data_received(tag, state)

    def data_received(self, tag, state):
        """ Call all registered callbacks.
        """
        for client in self.clients:
            client(tag, state)
