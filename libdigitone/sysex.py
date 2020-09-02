from .constants import *
from binascii import hexlify, unhexlify
import logging

import mido


def decode(filename):
    """ Decodes sysex file and converts to bytestring

    :param filename: expects binary .syx file from the digitone
    :return: byte string representing binary file
    """
    with open(filename, 'rb') as file:
        sysex = file.read()
        return sysex


def encode(sysex, filename='digi_out.syx'):
    """ Encodes sysex data into an agreeable format for the digitone

        TODO: Test this function

    :param sysex: sysex byte string
    :param filename: desired output binary .syx file name
    """
    with open(filename, 'wb') as file:
        sysex = sysex
        file.write(sysex)

    file.close()


def split_list(test_list, v):
    # using list comprehension + zip() + slicing + enumerate()
    # Split list into lists by particular value
    size = len(test_list)
    idx_list = [idx for idx, val in
                enumerate(test_list) if val == v]

    res = [test_list[i: j] for i, j in
           zip([0] + idx_list, idx_list +
               ([size] if idx_list[-1] != size else []))]

    return res


def parse(sysex):
    """ Takes a sysex message and parses it into a list of bytes

    :param sysex: sysex message to parse; expects a string
    :return: list of sysex messages, parsed into lists of individual bytes
    """
    messages = []
    for message in split_list(sysex, 0xf0):

        if message[:len(SYSEX_BEGIN)] == SYSEX_BEGIN:
            messages.append(message)

    return messages


# TODO: function to combine several sysex messages after processing

#       NOTE: Doing the mido thing may render using hexlify obsolete
#       very quickly. Currently, mido returns a .syx file in an ext-
#       remely odd fashion. While the type() returns it as a list,
#       there is extra meta data that I cannot figure out how to
#       parse away.

#       Current methods may be preferable since there is an explicit
#       method for each step of the process. Mido may just be dele-
#       gated to simply handle real-time (with Bill Maher) sysex
#       transfers.


def combine(sysex):
    """ Combines list or list of lists of sysex bytes and combines them into a
        byte string ready to send to digi

    :param sysex: expects list or list of lists of sysex bytes
    :return:
    """

    # Check if the input is a list of lists or simply a list
    if type(sysex[0]) == list:
        for i in range(len(sysex)):
            sysex[i] = b''.join(sysex[i])

    sysex_out = b''.join(sysex)
    return sysex_out


# TODO: request/send individual sysex messages to digitone


def request(message, track=0):
    """ Request a sysex dump from the Digitone

    :param message: type of message to be required. Currently supports:
                        patch
    :param track: Which track or pattern to request. Currently defaults to 0
    :return: None
    """
    try:
        outport = mido.open_output('Elektron Digitone')
    except OSError:
        logging.ERROR('Cannot find Digitone Ports. Is it connected? Exiting...')
        exit()

    # wait for the outport to open up
    while outport.closed:
        pass

    logging.debug('Port is opened!')
    if message == 'patch':

        # TODO: Add this to constants.py
        # TODO: Figure out what the requests are receiving back.

        msg_array = [int('0x00', 16), int('0x20', 16), int('0x3c', 16), int('0x0d', 16), int('0x00', 16),
                     int('0x6B', 16), int('0x01', 16), int('0x01', 16), 0, int('0x00', 16),
                     int('0x00', 16), int('0x00', 16), int('0x05', 16)]
        msg = mido.Message('sysex', data=msg_array)
        # logging.debug('Requesting patch...')
        outport.send(msg)
        # logging.debug('Closing port to exit gracefully...')
        outport.close()
        while not outport.closed:
            pass
        # logging.debug('Port Closed. Exiting...')


def listen():
    """ Listens for sysex messages from the digitone. Stays open as a loop
        NOTE: The MIDO library can take up to a full  two seconds to connect
        to the Digitone midi port.

        This function is designed for testing and prototyping the library
        only. To exit the loop, a SIGINT must be sent to exit cleanly.

    :return: messages that
    """

    # The port may take a few seconds to open. The while loop stops
    # the script while waiting to connect.

    with mido.open_input('Elektron Digitone') as inport:

        # wait for the inport to open up
        while inport.closed:
            pass

        # logging.debug('Port is opened!')

        try:
            for msg in inport:
                if msg.type == 'sysex':
                    msg = bytes(msg.hex(), 'utf-8').split()
                    yield msg
        except GeneratorExit:
            # logging.debug('Waiting for Port to close...')
            inport.close()
            while not inport.closed:
                pass
            # logging.debug('Port Closed. Exiting...')

        # TODO: Change this exception. It works fine for prototyping but needs
        #       a better way to exit for a library.

        except KeyboardInterrupt:
            print()
            logging.debug('Exiting Gracefully...')
            inport.close()
            while not inport.closed:
                pass
            logging.debug('Port Closed. Exiting...')


# TODO: Write sysex send function to modify current workspace patch

# def send(messages, track=0):
#     inport = mido.open_output('Elektron Digitone Digitone out 1')


if __name__ == '__main__':
    pass
