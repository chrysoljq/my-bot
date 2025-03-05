import struct
from urllib.parse import urlparse
from socket import *


def parse(address: str):
    tmp = urlparse('//'+address)
    if not tmp.hostname:
        raise ValueError(f'Invalid address {address}')
    else:
        return (tmp.hostname, tmp.port)


# 返回服务器真实地址，简单的SRV解析
def lookup(addr: str):
    host, port = parse(addr)
    # 构造 SRV 请求报文
    original = b'\x00\x02\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x0a' + \
        b'_minecraft\x04_tcp'
    for i in host.split('.'):
        original += struct.pack('B', len(i))+i.encode()
    original += b'\x00\x00\x21\x00\x01'

    sock = socket(AF_INET, SOCK_DGRAM, 0)
    sock.connect(('114.114.114.114', 53))
    sock.settimeout(5)
    sock.send(original)
    resp = sock.recv(1024)
    sock.close()
    # print(resp)
    if resp[2:4] == b'\x81\x80' and resp[6:8] != b'\x00\x00':  # no error and AnswerRRs isn't none
        AnswerRR = resp.split(b'\xc0\x0c')
        _seq = 14
        port = (AnswerRR[1][_seq]<<8)+AnswerRR[1][_seq+1]

        _seq += 2
        _len = AnswerRR[1][_seq]
        _host = b''
        while _len:
            _seq += _len+1
            _host += AnswerRR[1][_seq-_len:_seq]+b'.'
            _len = AnswerRR[1][_seq]
        host = _host.decode('utf-8')[:-1]
    return (host, port)