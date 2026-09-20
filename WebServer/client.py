# Name: <Paavan Randhawa>   Student number: <301614138>
"""CMPT 371 Project 1 - HTTP/1.1 client on a raw TCP socket.

Usage: python3 client.py --host H --port P --path /a [--path /b] [--out FILE ...]
"""

import argparse
import socket
import sys



def parse_args(argv):
    """TASK 4. Parse --host (default 127.0.0.1), --port (int), --path
    (repeatable), --out (repeatable, paired with --path in order)."""
    args_parser = argparse.ArgumentParser() #create an argument parser object

    #parse the arguments
    args_parser.add_argument("--host", action=None, type=str,default="127.0.0.1")
    args_parser.add_argument("--port", action=None, type=int, required=True)
    args_parser.add_argument("--path", action="append",type=str,required=True)
    args_parser.add_argument("--out",action="append",type=str,required=True)

    args = args_parser.parse_args(argv) #store parsed arguments in args object
    return args


def send_request(sock, host, path):
    """TASK 4. Send one GET request line, a Host header, and the blank line
    that ends it."""

    #build request
    request = "GET "+path+" HTTP/1.1\r\n"
    host_line="Host: "+host+"\r\n\r\n"
    full_request=request+host_line #combine both lines
    full_request=full_request.encode() #encode request in bytes

    sock.sendall(full_request) #send request



def read_head(sock, pending):
    """TASK 4. Read until the blank line ending the response head.
    Return (head_bytes, leftover) where leftover is body already received. The
    leftover is the start of the body and cannot be read again, so it must be
    counted toward Content-Length rather than discarded."""

    while 1:
        if "\r\n\r\n".encode() in pending: #full message has been received
            for i in range (len(pending)):
                if pending[i:i+4]=="\r\n\r\n".encode():
                    headers=pending[:i+4]
                    leftover=pending[i+4:]
                    return headers, leftover
        else:  # full message has not been received
            response_received=sock.recv(4096)
            if response_received == b"":
                return None
            else:
                pending+=response_received
    


def parse_head(head):
    """TASK 4. Split a response head into (status_code, reason, headers).
    headers is a dict with lower-cased names."""

    head=head.decode()
    response_lines=head.split("\r\n\r\n")[0] #cut off body
    response=response_lines.split("\r\n") 
    response_line_1=response[0].split(" ")
    status_code=response_line_1[1]
    reason=""
    i=2

    #get the reason
    while i<(len(response_line_1)):
        reason+=response_line_1[i]
        if (i != (len(response_line_1))-1):
            reason+=" "
        i+=1
    
    headers_dict={}

    header_lines=response[1:]
    for header in header_lines:
        if (len(header)==0):
            continue
        header_title=header.split(":",1)[0]
        header_value=header.split(":",1)[1]
        header_title=header_title.lower()
        headers_dict[header_title]=header_value
    
    return status_code,reason,headers_dict


    



    raise NotImplementedError


def read_body(sock, length, pending):
    """TASK 4. Return exactly length body bytes, counting what is already in
    pending, plus any bytes left over past them. Do not read until the connection
    closes: the server keeps it open, so a read-to-EOF client never returns.
    Every check in task 4 runs against a server that holds the connection open
    for a full minute, so reading to EOF fails all four, not just the timing
    one."""
    raise NotImplementedError


def main(argv=None):
    """TASK 4. Connect once, then for each --path in turn: send the request,
    read the head, read exactly Content-Length bytes, print
    '<status> <reason> <n> bytes', and write the body to the matching --out file.
    Return 0 on success. All the paths travel over the one connection, so
    whatever is left in the buffer past one body is the start of the next
    response."""

    args=parse_args(argv)

    client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM) #create the socket object
    client_socket.connect((args.host,args.port)) #connect to the server socket

    for i in range(len(args.path)):
        #send the request
        #read the head
        #read exactly content-length bytes
        #print <status> <reason> <n> bytes
        #write the body to the matching --out file
        #return 0 on success

    raise NotImplementedError


if __name__ == "__main__":
    sys.exit(main())
