# Name: <your full name>   Student number: <your student number>
"""CMPT 371 Project 1 - static HTTP/1.1 server on raw TCP sockets.

Usage: python3 server.py --port PORT --root DIR [--workers N]
"""

import argparse
import mimetypes
import os
import queue
import socket
import sys
import threading
import time
from email.utils import formatdate

KNOWN_METHODS = {"GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "TRACE", "CONNECT"}

requests_served = 0
counter_lock = threading.Lock()


def parse_args(argv):
    """TASK 1. Parse --port (int, 0 means pick any free port), --root
    (directory), --workers (int, how many threads the pool starts with,
    default 8). Accept --workers from task 1 even though nothing uses it until
    task 5: every command in the handout passes it."""

    args_parser = argparse.ArgumentParser() #create an argument parser object

    #parse the arguments
    args_parser.add_argument("--port", action=None, type=int,required=True)
    args_parser.add_argument("--root",action=None, required=True)
    args_parser.add_argument("--workers",action=None, type=int, default=8)

    args = args_parser.parse_args() #store parsed arguments in args object

    
    return args



def recv_request_head(conn):
    """TASK 3. Call recv() repeatedly until the blank line that ends the header
    block has arrived. Return the head bytes including that blank line, or None
    if the client closed the connection first.
    In task 1 handle_connection may read the head with a single recv(); this is
    what replaces that call, and is where reading becomes correct."""
    raise NotImplementedError


def parse_request(head):
    """TASK 3. Split a header block into (method, target, version, headers).
    headers is a dict with lower-cased names. Raise ValueError if the request
    line is not three fields or a header line has no colon; handle_request turns
    that into a 400."""
    raise NotImplementedError


def resolve_path(root, target):
    """TASK 1. Turn a request target into an absolute path inside root: drop any
    query string, percent-decode, append index.html for a target ending in '/'.
    Return None if the target is malformed.
    All three rules are graded: /index.html?x=1 and /index.html are the same
    file, / is that directory's index.html, and /page/sub.html works."""

    #drop any query string
    target=target.split('?')[0] #remove anything after ?

    #percent decode
    decoded_target = '' #will eventually contain the decoded target
    hexchar = '' #will be filled with the hex characters after a percent sign
    str_length = len(target) #length of original target


    #decode percent-encoded characters
    i = 0
    while i < str_length:
        if target[i] == '%': 
            if (i+2)>=str_length: #first check if there are two characters after the percent sign
                return None
            #first, fill hexchar variable with the two characters following %
            hexchar = target[i + 1] + target[i + 2]
            
            #check if the hex characters are valid
            try:
                decoded_hex = int(hexchar,16)
            except ValueError:
                return None #malformed target detected
            
            decoded_target += chr(decoded_hex) #add decoded characters to decoded_target string
            i+=3 #advance the index by 3
        else:
            decoded_target+=target[i]  #else keep copying characters
            i+=1 #move to next character 


        #append index.html for a target ending in '/'
    if decoded_target[-1] == '/':
        decoded_target += 'index.html'

   
    path=os.path.join(root, decoded_target.lstrip('/'))
    return path
            


def build_response(status, reason, body, content_type, extra=None):
    """TASK 1. Return the full response as bytes: status line, the Date, Server,
    Content-Type, Content-Length and Connection headers, any extra headers,
    a blank line, then body.
    Every response goes through here, including 404, 400, 405 and 501, so every
    response carries all five headers. Content-Length is the number of body
    bytes that follow, and nothing else."""

    #convert strings to bytes
    status=status.encode()
    reason=reason.encode()
    content_type=content_type.encode()
    date=formatdate(usegmt=True).encode()
    server_string="cmpt371/1.0".encode()
    content_length=str(len(body)).encode()
    connection_header="keep-alive".encode()

    
    if (extra=="GET"):
        #build the entire response in bytes
        response = ("HTTP/1.1 ".encode() + status + " ".encode() + reason + "\r\n".encode()
    + "Date: ".encode() + date + "\r\n".encode()
    + "Server: ".encode() + server_string + "\r\n".encode()
    + "Content-Type: ".encode() + content_type + "\r\n".encode()
    + "Content-Length: ".encode() + content_length + "\r\n".encode()
    + "Connection: ".encode() + connection_header + "\r\n".encode()
    + "\r\n".encode() + body)
        return response
    elif (extra=="HEAD"):
        #build the entire response in bytes and omit body
        response = ("HTTP/1.1 ".encode() + status + " ".encode() + reason + "\r\n".encode()
    + "Date: ".encode() + date + "\r\n".encode()
    + "Server: ".encode() + server_string + "\r\n".encode()
    + "Content-Type: ".encode() + content_type + "\r\n".encode()
    + "Content-Length: ".encode() + content_length + "\r\n".encode()
    + "Connection: ".encode() + connection_header + "\r\n".encode()
    + "\r\n".encode())
        return response









def handle_request(head, root):
    #print("handle_request called", flush=True)
    """TASK 1, extended in tasks 2 and 3. Turn one header block into a complete
    response.
    Task 1: 200 and 404. Task 2: HEAD, which carries no body, and Content-Type
    from the file extension. Task 3: 400 (malformed request line or header line,
    no Host), 405 (POST and the other known methods, with Allow: GET, HEAD) and
    501 (a token that is not an HTTP method)."""

    #convert bytes to string and split on whitespace
    tokens = head.decode().split()
    method = tokens[0] 
    target = tokens[1]
    http_version = tokens[2]

    path=resolve_path(root,target) #build a proper path

    if (method == "GET"):
        if not (os.path.isfile(path)): #file not found, build 404 response
            status=str(404)
            reason="Not Found"
            body="404 Not Found\n".encode()
            content_type,encoding=mimetypes.guess_type(path)
            return build_response(status,reason,body,content_type,"GET")

        else:
            #build a 200 response
            status=str(200)
            reason="OK"
            
            #open file and read contents and place them in body variable
            opened_file=open(path,"rb")
            body=opened_file.read()
            opened_file.close()

            content_type, encoding=mimetypes.guess_type(path)
            return build_response(status,reason,body,content_type,"GET")

    elif (method=="HEAD"):
        if not (os.path.isfile(path)): #file not found, build 404 response
            status=str(404)
            reason="Not Found"
            body="404 Not Found\n".encode()
            content_type,encoding=mimetypes.guess_type(path)
            return build_response(status,reason,body,content_type,"HEAD")

        else:
            #build a 200 response
            status=str(200)
            reason="OK"
            
            #open file and read contents and place them in body variable
            opened_file=open(path,"rb")
            body=opened_file.read()
            opened_file.close()
            content_type, encoding=mimetypes.guess_type(path)
            return build_response(status,reason,body,content_type,"HEAD")
    
    
    
        
        


def handle_connection(conn, root):
    """TASK 1, extended in tasks 3 and 5. Serve requests on one connection until
    the client closes it or it goes idle -- a few seconds; five is reasonable.
    Task 1: read the head (one recv() is enough for now), call handle_request,
    sendall() the response, and loop. Task 3: replace that read with
    recv_request_head. Task 5: after each response, increment requests_served
    under counter_lock and print 'served <n>' to stderr, where n is the value
    this request produced, read inside the same lock that incremented it."""

    message = conn.recv(4096) #receive up to 4096 bytes from client
    response = handle_request(message,root) #send message received to handle_request
    conn.sendall(response) #send the response back




def worker(work_queue, root):
    """TASK 5. Take accepted connections off work_queue and serve them, forever.
    Every worker thread runs this; none of them is created per connection.
    Nothing before task 5 calls this, and main must not start any worker threads
    until you write it."""
    raise NotImplementedError


def main(argv=None):
    """TASK 1, replaced in task 5. Bind 127.0.0.1 on the requested port, listen,
    print the port line below, then serve connections.
    Task 1: accept one connection at a time and pass each to handle_connection.
    Task 5: replace that loop -- create --workers threads running worker() and a
    queue.Queue, and let main do nothing but accept and enqueue."""
    # Given. The grading script reads this line to find your server, so print it
    # exactly as written, immediately after listen(), and keep flush=True.
    #     print("Listening on port %d" % listener.getsockname()[1], flush=True)

    args=parse_args(argv)
    server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM) #create the socket object
    server_socket.bind(("127.0.0.1",args.port)) #bind the socket to ip address 127.0.0.1 and given port number
    server_socket.listen(1) 
    print("Listening on port %d" % server_socket.getsockname()[1], flush=True)

    while 1: #keep accepting clients and handling them
        client, address = server_socket.accept() #wait until a client connects to the server
        handle_connection(client, args.root) #pass the client over to handle_connection
    


if __name__ == "__main__":
    main()

   
