#!/usr/bin/python
""" This module provide a MirrorClient class that listen to a Mirror device
(from Violet). This class is a little adaptation to a twisted oriented code
found in the following article http://www.dad3zero.net/201012/mirror-en-python/
"""


import binascii
from time import sleep
from twisted.internet import reactor


class MirrorClient(object):
    """ The MirrorClient listen to a device (eg: /dev/mirror) and call the
    registered callbacks (from add_callback method) with the tag and
    associtated state of the tag.
    """
    def __init__(self, device):
        """ Init the MirrorClient with an associated device to listen.
        """
        self._device = None
        self._device_name = device
        self._subscribers = set()
        self._open()

    def start(self):
        """ When the start method is called, the listen method is called inside
        a thread.
        """
        reactor.callInThread(self._listen)

    def subscribe(self, callback):
        """ Add a callback which will be called when an event is read from the
        defined device.
        """
        self._subscribers.add(callback)

    def _open(self):
        """ Open the device if it's possible (connected)
        """
        try:
            self._device = open(self._device_name, 'rb')
        except IOError:
            self._device = None

    def _listen(self):
        """ Listen until the reactor is stopped and read the device. When a tag
        is detected or removed call registered callbacks.
        """
        while reactor.running:
            if not self._device or self._device.closed is True:
                self._device_disconnected()
            else:
                self._read_device()

    def _read_device(self):
        """ Read 16bytes from the device and search for a tag event.
        """
        try:
            data = self._device.read(16)
            if data != '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00':  # pylint: disable=C0301
                bin_state = binascii.hexlify(data)[:4]
                tag = binascii.hexlify(data)[4:]
                # Sometime a ghost tag is detected by the Mirror device.
                if bin_state != '0104':
                    state = True if bin_state == '0201' else False
                    reactor.callFromThread(self._data_received, tag, state)
        except IOError:
            self._device.close()

    def _device_disconnected(self):
        """ When the mirror is disconnected from the computer wait 500ms
        and try to reopen the device.
        """
        sleep(0.5)
        self._open()

    def _data_received(self, tag, state):
        """ Call all registered callbacks.
        """
        for subscriber in self._subscribers:
            subscriber(tag, state)
