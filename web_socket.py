#!/usr/bin/env python
# encoding: utf-8
"""
@version: v1.0
@author: W_H_J
@license: Apache Licence
@contact: 415900617@qq.com
@software: PyCharm
@file: serverTest.py
@time: 2019/2/19 9:49
@describe: 基于socket 的websocket服务端
连接成功可查看浏览器的network headers部分状态是否为101
source: https://blog.csdn.net/sinat_32651363/article/details/87880225
"""
import sys
import os
import base64
import hashlib
import socket

sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/' + '..'))
sys.path.append("..")

sock = socket.socket()
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# 绑定host，默认端口5000
sock.bind(("0.0.0.0", 5000))
sock.listen(5)


def get_headers(data):
    """
    request header dictionary
    :param data: parse header data
    :return: request header dictionary
    """
    header_dict = {}
    data = str(data)
    """
    request header format
    b'
        GET / HTTP/1.1\r\n
        Host: 127.0.0.1:8080\r\n
        Connection: Upgrade\r\n
        Pragma: no-cache\r\n
        Cache-Control: no-cache\r\n
        Upgrade: websocket\r\n
        Origin: http://localhost:63342\r\n
        Sec-WebSocket-Version: 13\r\n
        User-Agent: Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36\r\n
        Accept-Encoding: gzip, deflate, br\r\n
        Accept-Language: zh-CN,zh;q=0.8\r\n
        Sec-WebSocket-Key: +uL/aiakjNABjEoMzAqm6Q==\r\n
        Sec-WebSocket-Extensions: permessage-deflate; client_max_window_bits\r\n\r\n'
    """
    header, body = data.split("\r\n\r\n", 1)  #header tail
    ###
    header_list = header.split("\r\n")
    for i in range(0, len(header_list)):
        if i == 0:
            if len(header_list[0].split(" ")) == 3:
                header_dict['method'], header_dict['url'], header_dict['protocol'] = header_list[0].split(" ")
        else:
            k, v = header_list[i].split(":", 1)
            header_dict[k] = v.strip()
    return header_dict


def get_data(info):
    """
    parse return data
    :param info: data
    :return:
    """
    payload_len = info[1] & 127
    if payload_len == 126:
        extend_payload_len = info[2:4]
        mask = info[4:8]
        decoded = info[8:]
    elif payload_len == 127:
        extend_payload_len = info[2:10]
        mask = info[10:14]
        decoded = info[14:]
    else:
        extend_payload_len = None
        mask = info[2:6]
        decoded = info[6:]
    bytes_list = bytearray()
    for i in range(len(decoded)):
        chunk = decoded[i] ^ mask[i % 4]
        bytes_list.append(chunk)
    body = str(bytes_list)
    return body


# connection
conn, addr = sock.accept()
print("conn from==>", conn, addr)
# magic string ,sha1
# send to client
# handshake
data = conn.recv(8096)
headers = get_headers(data)

# 对请求头中的sec-websocket-key进行加密
response_tpl = "HTTP/1.1 101 Switching Protocols\r\n" \
               "Upgrade:websocket\r\n" \
               "Connection: Upgrade\r\n" \
               "Sec-WebSocket-Accept: %s\r\n" \
               "WebSocket-Location: ws://%s%s\r\n\r\n"

magic_string = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
# 确认握手Sec-WebSocket-Key固定格式：headers头部的Sec-WebSocket-Key+'258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
value = headers['Sec-WebSocket-Key'] + magic_string
ac = base64.b64encode(hashlib.sha1(value.encode('utf-8')).digest())
response_str = response_tpl % (ac.decode('utf-8'), headers['Host'], headers['url'])

# 响应【握手】信息
conn.send(bytes(response_str))

# 可以进行通信--接收客户端发送的消息
while True:
    data = conn.recv(8096)
    data = get_data(data)
    try:
        conn.send("hello".encode())
    except:
        conn.close()
    print("Receive msg==>", data)

