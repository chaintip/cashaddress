from cashaddress.crypto import *
from base58 import b58decode_check, b58encode_check


class InvalidAddress(Exception):
    pass


class Address:
    VERSION_MAP = {
        'legacy': [
            ('P2SH', 5),
            ('P2PKH', 0)
        ],
        'cash': [
            ('P2SH', 8),
            ('P2PKH', 0)
        ]
    }
    DEFAULT_PREFIX = 'bitcoincash'

    def __init__(self, version, payload, prefix=None):
        self.version = version
        self.payload = payload
        if prefix:
            self.prefix = prefix
        else:
            self.prefix = self.DEFAULT_PREFIX

    def __str__(self):
        return 'version: {}\npayload: {}\nprefix: {}'.format(self.version, self.payload, self.prefix)

    def legacy_address(self):
        version_int = Address._address_type('legacy', self.version)[1]
        return b58encode_check(Address.code_list_to_string([version_int] + self.payload))

    def cash_address(self):
        version_int = Address._address_type('cash', self.version)[1]
        payload = [version_int] + self.payload
        payload = convertbits(payload, 8, 5)
        checksum = calculate_checksum(self.prefix, payload)
        return self.prefix + ':' + b32encode(payload + checksum)

    @staticmethod
    def code_list_to_string(code_list):
        output = ''
        for code in code_list:
            output += chr(code)
        return output

    @staticmethod
    def _address_type(address_type, version):
        for mapping in Address.VERSION_MAP[address_type]:
            if mapping[0] == version or mapping[1] == version:
                return mapping
        raise InvalidAddress('Could not determine address version')

    @staticmethod
    def from_string(address_string):
        if not isinstance(address_string, str):
            raise InvalidAddress('Expected string as input')
        if ':' not in address_string:
            return Address._legacy_string(address_string)
        else:
            return Address._cash_string(address_string)

    @staticmethod
    def _legacy_string(address_string):
        try:
            decoded = bytearray(b58decode_check(address_string))
        except ValueError:
            raise InvalidAddress('Could not decode legacy address')
        version = Address._address_type('legacy', decoded[0])[0]
        payload = list()
        for letter in str(decoded[1:]):
            payload.append(ord(letter))
        return Address(version, payload)

    @staticmethod
    def _cash_string(address_string):
        if address_string.upper() != address_string and address_string.lower() != address_string:
            raise InvalidAddress('Cash address contains uppercase and lowercase characters')
        address_string = address_string.lower()
        if ':' not in address_string:
            address_string = Address.DEFAULT_PREFIX + ':' + address_string
        prefix, base32string = address_string.split(':')
        decoded = b32decode(base32string)
        if not verify_checksum(prefix, decoded):
            raise InvalidAddress('Bad cash address checksum')
        converted = convertbits(decoded, 5, 8)
        version = Address._address_type('cash', converted[0])[0]
        payload = converted[1:-6]
        return Address(version, payload, prefix)


def to_cash_address(address):
    return Address.from_string(address).cash_address()


def to_legacy_address(address):
    return Address.from_string(address).legacy_address()


def is_valid(address):
    try:
        Address.from_string(address)
        return True
    except InvalidAddress:
        return False
