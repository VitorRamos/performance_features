import socket, struct, os, sys

path= '.'
if sys.argv[1]:
    path= sys.argv[1]

def send_data(sock):
    for f in os.listdir(path):
        if f.endswith('.dat'):
            data= open(os.path.join(path, f), 'rb+').read()
            lens= struct.pack('II', len(f), len(data))
            print(f, len(f), len(data))
            sock.send(lens+f.encode()+data)

try:
    s= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1',5656))
    s.listen(5)
    #while 1:
    conn, addr= s.accept()
    print(addr, "connected")
    try:
        send_data(conn)
        conn.close()
    except Exception as e:
        print("Error seding data", e)
        conn.close()
except Exception as e:
    print(e)
    s.close()