from .constants import *
from binascii import unhexlify
import logging


class Sound:

    def __init__(self, patch):
        """ Breaks a patch into it's component sections.

        :param patch: Expects a single patch as a full sysex patch message.
        """

        # Check data type
        # if patch[0x14f:0x151] != [b'02', b'48']:
        #     logging.debug(patch[0x150:0x152])
        #     raise TypeError("This is not the correct patch size! Data is probably corrupt")

        # Separate the key component sections of the patch
        self.prefix = patch[:0x05]
        self.meta = patch[0x05:0x0a]
        self.unspec = patch[0x0a:0x12]
        self.tags = patch[0x14:0x18]
        self.name = patch[0x18:0x29]
        self.data = patch[0x29:0x14e]
        self.eom = patch[0x14e:]

    @property
    def tag_list(self):
        """ Label the tags on a particular sound into human readable format

        :return: list of tags associated with the patch
        """

        _tags = []

        for t in Tag:
            if self.tags[3 - (t.value // 8)] >> (t.value % 8) & 1:
                _tags.append(t)

        return _tags

    # TODO: What exactly is this good for again?
    def param_list(self):
        """ Scan the parameter locations and return a human readable value
            for each of the parameters.

        :return: human readable strings of the parameter values
        """

        for para in PARAM:
            param_data = b''
            for byte in PARAM_LOOK[para].split():
                param_data += self.data[int(byte, 16)]

            # logging.debug('{}: {}'.format(para, param_data))

    @property
    def param_to_dict(self):
        """ Create a dictionary with all of the parameter values.

        :return: dictionary of the parameter values
        """

        param_data = {}
        for para in PARAM:
            param_data[para] = self.param(para)

        return param_data

    def param(self, param):
        """ Return the value of a single parameter.

        :param param: which parameter to retrieve a value from
        :return: the value of an individual parameter
        """

        def is_bit_set(v, bit):
            return v & (bit - 1)

        def get_byte(loc):
            pass

        # for param in PARAM:
        param_ = PARAM_LOOK[param]
        if len(param_) == 1:
            return self.data[param_[0]]

        elif len(param_) == 3:
            neg_bit = param_[0]
            neg_byte = int(self.data[param_[1]])
            value = int(self.data[param_[2]])
            if not is_bit_set(neg_byte, neg_bit):
                return value
            else:
                return value - 128

        elif len(param_) == 4:
            flag_bit = param_[0]
            flag_byte = int(self.data[param_[1]])
            msb_value = int(self.data[param_[2]])
            lsb_value = int(self.data[param_[3]])

            if param == 'b':
                msb_value = msb_value * 128
                if is_bit_set(flag_byte, flag_bit):
                    lsb_value = int((lsb_value + 127) * (64 / 127))
                else:
                    lsb_value = int((64 / 127) * lsb_value)
                return int(((msb_value) + lsb_value))

            elif 'lfo' in param:
                lsb_value = (100 / 127) * lsb_value
                if not is_bit_set(flag_byte, flag_bit):
                    msb_value = (msb_value * 2) - 128
                else:
                    msb_value = (msb_value * 2) - 127
                return round(msb_value + (lsb_value/100), 2)

            elif param == 'harm':
                msb_value = msb_value - 63
                if not is_bit_set(flag_byte, flag_bit):
                    lsb_value = int((50 / 127) * lsb_value)
                    return round(msb_value + (lsb_value / 100), 2)
                else:
                    lsb_value = int((50 / 127) * lsb_value + 50)
                    return round(msb_value + (lsb_value / 100), 2)

            # every other 3-byte function
            else:
                if not is_bit_set(flag_byte, flag_bit):
                    lsb_value = int((50 / 127) * lsb_value)
                    return round(msb_value + (lsb_value / 100), 2)
                else:
                    lsb_value = int((50 / 127) * lsb_value + 50)
                    return round(msb_value + (lsb_value / 100), 2)

    def name_to_string(self):
        """ Convert the name section into a human readable string

        :return: the name of a patch as a human readable string
        """

        name = self.name.decode('utf-8').strip('\x00')
        return name
