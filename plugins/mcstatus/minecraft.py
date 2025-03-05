import socket
import struct
import json
import time
from .dns import lookup,parse

class StatusPing:
    """ Get the ping status for the Minecraft server """

    def __init__(self, addr, timeout=5):
        """ Init the hostname and the port """
        try:
            self._host, self._port = lookup(addr)
        except:
            self._host, self._port = parse(addr)
        if self._port == None:
            self._port = 25565
        self._timeout = timeout

    def _unpack_varint(self, sock):
        """ Unpack the varint """
        data = 0
        for i in range(5):
            ordinal = sock.recv(1)

            if len(ordinal) == 0:
                break

            byte = ord(ordinal)
            data |= (byte & 0x7F) << 7 * i

            if not byte & 0x80:
                break

        return data

    def _pack_varint(self, data):
        """ Pack the var int """
        ordinal = b''

        while True:
            byte = data & 0x7F
            data >>= 7
            ordinal += struct.pack('B', byte | (0x80 if data > 0 else 0))

            if data == 0:
                break

        return ordinal

    def _pack_data(self, data):
        """ Page the data """
        if type(data) is str:
            data = data.encode('utf8')
            return self._pack_varint(len(data)) + data
        elif type(data) is int:
            return struct.pack('H', data)
        elif type(data) is float:
            return struct.pack('Q', int(data))
        else:
            return data

    def _send_data(self, connection, *args):
        """ Send the data on the connection """
        data = b''

        for arg in args:
            data += self._pack_data(arg)

        connection.send(self._pack_varint(len(data)) + data)

    def _read_fully(self, connection, extra_varint=False):
        """ Read the connection and return the bytes """
        packet_length = self._unpack_varint(connection)
        packet_id = self._unpack_varint(connection)
        byte = b''

        if extra_varint:
            # Packet contained netty header offset for this
            if packet_id > packet_length:
                self._unpack_varint(connection)

            extra_length = self._unpack_varint(connection)

            while len(byte) < extra_length:
                byte += connection.recv(extra_length)

        else:
            byte = connection.recv(packet_length)

        return byte

    def get_status(self):
        init_time = int(time.time()*1000)
        """ Get the status response """
        with socket.create_connection((self._host,self._port),timeout=self._timeout) as connection:

            # Send handshake + status request
            self._send_data(connection, b'\x00\x00',
                            self._host, self._port, b'\x01')
            self._send_data(connection, b'\x00')

            # Read response, offset for string length
            data = self._read_fully(connection, extra_varint=True)
            # print(data)

            # Send and read unix time
            self._send_data(connection, b'\x01', time.time() * 1000)
            unix = self._read_fully(connection)

        # Load json and return
        # print(data.decode('utf-8',errors='replace').replace('}S{',','),'\n\n')
        # js_index = 0 # data.index(b'{')
        response = json.loads(data.decode('utf-8').replace('}S{',',').replace('}W{',',').replace(',"version":"0.2.0"}','}'))
        try:
            response['ping'] = int(time.time() * 1000) - \
            struct.unpack('Q', unix)[0]
        except Exception:
            response['ping'] = -int(time.time() * 1000) + init_time

        return response

# client=StatusPing('mc.jwzs.xyz:2700')
# s=client.get_status()
# print(s)
