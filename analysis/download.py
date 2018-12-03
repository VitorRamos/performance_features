import socket
import struct

sock= socket.create_connection(('127.0.0.1',5656))

while 1:
    lens= sock.recv(8)
    if not lens: break

    lens= struct.unpack('II', lens)
    name= b''
    while len(name)<lens[0]:
        name+= sock.recv(lens[0]-len(name))
    data= b''
    while len(data)<lens[1]:
        data+= sock.recv(lens[1]-len(data))
    print(name, lens, len(data), len(name))

    with open(name, 'wb+') as f:
        f.write(data)
    
    if (lens[1] != len(data)) or (lens[0] != len(name)):
        print("Error")
        break

print("Exited")