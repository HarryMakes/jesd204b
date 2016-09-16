from litex.soc.interconnect.stream import EndpointDescription

# control characters

control_characters = {
    "R": 0b00011100, # K28.0, Start of multi-frame
    "A": 0b01111100, # K28.3, Lane alignment
    "Q": 0b10011100, # K28.4, Start of configuration data
    "K": 0b10111100, # K28.5, Group synchronization
    "F": 0b11111100, # K28.7, Frame alignment
}


# configuration data

class Field:
    def __init__(self, octet, offset, width):
        self.octet = octet
        self.offset = offset
        self.width = width


configuration_data_length = 14
configuration_data_fields = {
    #----------- octet 0 --------------
    "did":       Field(0,  0, 8), # device id
    #----------- octet 1 --------------
    "bid":       Field(1,  0, 4), # bank id
    "adjcnt":    Field(1,  4, 8), # N/A (subclass 2 only)
    #----------- octet 2 --------------
    "lid":       Field(2,  0, 5), # lane id
    "phadj":     Field(2,  5, 5), # N/A (subclass 2 only)
    "adjdir":    Field(2,  6, 6), # N/A (subclass 2 only)
    #----------- octet 3 --------------
    "l":         Field(3,  0, 5),
    "scr":       Field(3,  7, 8), # scrambling enable
    #----------- octet 4 --------------
    "f":         Field(4,  0, 8),
    #----------- octet 5 --------------
    "k":         Field(5,  0, 4),
    #----------- octet 6 --------------
    "m":         Field(6,  0, 8),
    #----------- octet 7 --------------
    "n":         Field(7,  0, 5),
    "cs":        Field(7,  6, 8),
    #----------- octet 8 --------------
    "n":         Field(8,  0, 5),
    "subclassv": Field(8,  5, 8), # device subclass version
    #----------- octet 9 --------------
    "s":         Field(9,  0, 5),
    "jesdv":     Field(9,  5, 8), # jsed204 version
    #----------- octet 10 -------------
    "cf":        Field(10, 0, 5),
    "hd":        Field(10, 5, 8),
    #----------- octet 11 -------------
    "res1":      Field(11, 0, 8),
    #----------- octet 12 -------------
    "res2":      Field(12, 0, 8),
    #----------- octet 13 -------------
    "chksum":    Field(13, 0, 8)
}


class JESD204BConfigurationData:
    def __init__(self):
        for k in configuration_data_fields.keys():
            setattr(self, k, 0)

    def get_octets(self):
        octets = [0]*configuration_data_length
        for name, field in configuration_data_fields.items():
            octets[field.octet] |= ((getattr(self, name) << field.offset) &
                                    2**(field.width-field.offset)-1)
        return octets

    def get_checksum(self):
        checksum = 0
        for octet in self.get_octets()[:-1]:
                checksum = (checksum + octet) % 256
        return checksum


# settings

class JESD204BTransportSettings:
    def __init__(self, f, s, k, cs):
        self.f = f
        self.s = s
        self.k = k
        self.cs = cs


class JESD204BPhysicalSettings:
    def __init__(self, l, m, n, np, sc):
        self.l = l
        self.m = m
        self.n = n
        self.np = np
        self.sc = sc

        # only support subclass 1
        self.subclassv = 0b001
        self.adjcnt = 0
        self.adjdir = 0
        self.phadj = 0

        # jsed204b revision
        self.jsedv = 0b001


class JESD204BSettings:
    def __init__(self,
        phy_settings,
        transport_settings,
        did, bid):
        self.phy = phy_settings
        self.transport = transport_settings
        self.did = did
        self.bid = bid

    def get_configuration_data(self):
        cd = JESD204BConfigurationData()
        for k in configuration_data_fields.keys():
            for settings in [self.phy,
                             self.transport]:
                try:
                    setattr(cd, k, getattr(settings, k))
                except:
                    pass
        cd.did = self.did
        cd.bid = self.bid

        octets = cd.get_octets()
        chksum = cd.get_checksum()
        return octets[:-1] + [chksum]

    def get_clocks(self):
        ps = self.phy
        ts = self.transport

        fc = ps.sc/ts.s
        lmfc = fc/ts.k

        lr = (ps.m*ts.s*ps.np*10/8*fc)/ps.l

        return ps.sc, fc, lmfc, lr


# layouts

def transport_layout(data_width, n):
    layout = [("data"+str(i), data_width) for i in range(n)]
    return EndpointDescription(layout)


def link_layout(data_width):
    layout = [
        ("data", data_width),
        ("ctrl", data_width//8),

        ("frame_last", data_width//8),
        ("multiframe_last", data_width//8)
    ]
    return EndpointDescription(layout)


def phy_layout(data_width, n=1):
    if n == 1:
        layout = [("data", data_width)]
        layout += [("ctrl", data_width//8)]
    else:
        layout = [("data"+str(i), data_width) for i in range(n)]
        layout += [("ctrl"+str(i), data_width//8) for i in range(n)]
    return EndpointDescription(layout)
