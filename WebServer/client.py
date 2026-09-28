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
    if len(args.path) != len(args.out):
        print("ERROR: number of paths does not equal number of output files. Exiting program.")
        sys.exit()
    
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
    response=response_lines.split("\r\n")  #split rest of message
    response_line_1=response[0].split(" ") #store the firt line of the response
    status_code=response_line_1[1] #extract the status code from the first line of the response
    reason="" #empty buffer for reason since it may be more than one word


    i=2
    #get the reason
    while i<(len(response_line_1)):
        reason+=response_line_1[i] #add the current word to the string
        if (i != (len(response_line_1))-1): #if this is not the last word add a space
            reason+=" " #add a space between words
        i+=1 #advance pointer to next word
    
    headers_dict={}

    header_lines=response[1:] #the headers are everything after the status code+reason line and before the body
    for header in header_lines:
        if (len(header)==0): #don't add empty header lines to the dictionary
            continue
        #split the lines and add them to the dictionary
        header_title=header.split(":",1)[0]
        header_value=header.split(":",1)[1]
        header_title=header_title.lower()
        headers_dict[header_title]=header_value
    
    return status_code,reason,headers_dict



def read_body(sock, length, pending):
    """TASK 4. Return exactly length body bytes, counting what is already in
    pending, plus any bytes left over past them. Do not read until the connection
    closes: the server keeps it open, so a read-to-EOF client never returns.
    Every check in task 4 runs against a server that holds the connection open
    for a full minute, so reading to EOF fails all four, not just the timing
    one."""

    body="".encode() #start with an empty buffer for body
    temp_pending="".encode() #will store leftover bytes a
    i=0
    while 1: #keep looping until current body has been collected
        if i==length: #check if we have collected the required number of bytes
            temp_pending=pending[i:] #leftover bytes are everything after what we've collected
            pending=temp_pending 
            return body,pending
        if (len(pending))<length: #if we haven't yet collected required number of bytes
            received_msg=sock.recv(4096) #receive more
            if (received_msg==b""): #if we receive an empty msg return  None
                return None
            else:
                pending+=received_msg #add received message to pending
        else: #pending has enough bytes for the entire body
            while i<(length):  #extract the body
                body+=pending[i:i+1] #add one byte to the body
                i+=1
        


def main(argv=None):
    """TASK 4. Connect once, then for each --path in turn: send the request,
    read the head, read exactly Content-Length bytes, print
    '<status> <reason> <n> bytes', and write the body to the matching --out file.
    Return 0 on success. All the paths travel over the one connection, so
    whatever is left in the buffer past one body is the start of the next
    response."""

    args=parse_args(argv) #parse the arguments and store them in args

    client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM) #create the socket object
    client_socket.connect((args.host,args.port)) #connect to the server socket

    pending="".encode() #create empty bytes buffer for messages
    for i in range(len(args.path)): #loop through every path
        send_request(client_socket,args.host,args.path[i]) #send a GET request for the path
        read_head_output=read_head(client_socket, pending) #read the response headers
        if read_head_output is None: #if server disconnected exit with -1
            return -1
        headers,pending=read_head_output #store headers and leftover bytes
        status_code,reason,headers_dict=parse_head(headers) #parse the status code, headers and response
        content_length=int(headers_dict["content-length"]) #store content-length in a variable for printing
        read_body_output=read_body(client_socket,content_length,pending) #read the output of the vody into read_body_output
        if read_body_output is None: #if server disconnected return -1
            return -1
        body,pending=read_body_output #store body and pending bytes
        print_str=status_code+" "+reason+" "+str(content_length)+" bytes" #print the status code,reason and the number of bytes read
        print(print_str) #print info to the terminal
        with open(args.out[i],"wb") as file: #Write the body to the specified file
            file.write(body)
    return 0 #return 0 on success





        
        #read the head
        #read exactly content-length bytes
        #print <status> <reason> <n> bytes
        #write the body to the matching --out file
        #return 0 on success



if __name__ == "__main__":
    sys.exit(main())
