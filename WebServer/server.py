# Name: <Paavan Randhawa>   Student number: <301614138>
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

#dictionary for client requests
#the key is the client socket and the value is the request
#used to store leftover requests that will be processed later
requests_dict={}


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
    
    i=0
    while 1: #keep looping until no more requests are sent (b"" is received)
        if (conn in requests_dict): #if the client has sent a request before, get the leftover request from the dictionary
            message=requests_dict[conn] #fill message with the leftover request
            if "\r\n\r\n".encode() in message: #if the full request is in the dictionary extract it
                for i in range(len(message)):
                    if message[i:i+4]=="\r\n\r\n".encode(): #when end of request is found, split into request and leftover
                        return_value=message[:i+4]
                        leftover=message[i+4:]
                        requests_dict[conn]=leftover
                        return return_value
            else: #if the full request is not in the dictionary, keep receiving from the client
                message_received=conn.recv(4096)
                if (message_received==b""): #return None if the client has finished sending 
                    return None
                else:
                    message+=message_received #append received message to current message 
                    requests_dict[conn]=message #store in the dictionary
        else: #case where the client has not sent a message before
            #dictionary entry must be set up for possible future messages
            message="".encode() #initial message buffer starts out empty
            message_received=conn.recv(4096)
            if (message_received==b""): #if they didn't send anything, return None
                return None
            else: #if they sent something, store it in message, and add it to the requests dictionary
                message+=message_received #add the received message to the message buffer
                requests_dict[conn]=message #create the dictionary entry with client connection and corresponding message(s)






    


def parse_request(head):
    """TASK 3. Split a header block into (method, target, version, headers).
    headers is a dict with lower-cased names. Raise ValueError if the request
    line is not three fields or a header line has no colon; handle_request turns
    that into a 400."""

    http_request = head.decode() #convert from bytes to string
    http_request=http_request.split("\r\n") #split into separate lines
    request_line=http_request[0] 
    tokenized_request_line=request_line.split() #get individual elements from the request line (e.g: method, target, version (HTTP/1.1))
    if len(tokenized_request_line)!=3:  #request line should only contain method, target and version
        raise ValueError
    method=tokenized_request_line[0]
    target=tokenized_request_line[1]
    version=tokenized_request_line[2]


    headers_dict={}
    for header in http_request[1:-1]: #skip first line and empty line at the end
        if len(header)==0: #if the line is empty don't parse it 
            continue
        elif ":" not in header: #invalid header line case
            raise ValueError 
        else:  #pearse header lines, convert to lower case, and add to the dictionary
            header_title=header.split(":",1)[0]
            header_value=header.split(":",1)[1]
            header_title=header_title.lower()
            headers_dict[header_title]=header_value


    if "host" not in headers_dict: #the header lines must contain a host header line
        raise ValueError
    return method,target,version,headers_dict
            





def resolve_path(root, target):
    """TASK 1. Turn a request target into an absolute path inside root: drop any
    query string, percent-decode, append index.html for a target ending in '/'.
    Return None if the target is malformed.
    All three rules are graded: /index.html?x=1 and /index.html are the same
    file, / is that directory's index.html, and /page/sub.html works."""

    #drop any query string
    target=target.split('?')[0] #chop off anything after ?

    #percent decode
    decoded_target = '' #will eventually contain the decoded target
    hexchar = '' #will be filled with the hex characters after a percent sign to decode
    str_length = len(target) #length of original target


    #decode percent-encoded characters
    i = 0
    while i < str_length: #parse through string
        if target[i] == '%': 
            if (i+2)>=str_length: #first check if there are two characters after the percent sign
                return None #invalid if two characters dont follow the % sign
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
    if len(decoded_target)!=0 and decoded_target[-1] == '/':
        decoded_target += 'index.html'

   
    path=os.path.join(root, decoded_target.lstrip('/'))  #put together the resolved path
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

    
    if (extra=="GET"): #special response for GET requetss
        #build the entire response in bytes
        response = ("HTTP/1.1 ".encode() + status + " ".encode() + reason + "\r\n".encode()
    + "Date: ".encode() + date + "\r\n".encode()
    + "Server: ".encode() + server_string + "\r\n".encode()
    + "Content-Type: ".encode() + content_type + "\r\n".encode()
    + "Content-Length: ".encode() + content_length + "\r\n".encode()
    + "Connection: ".encode() + connection_header + "\r\n".encode()
    + "\r\n".encode() + body)
        return response
    elif (extra=="HEAD"): #special response for HEAD requests
        #build the entire response in bytes and omit body
        response = ("HTTP/1.1 ".encode() + status + " ".encode() + reason + "\r\n".encode()
    + "Date: ".encode() + date + "\r\n".encode()
    + "Server: ".encode() + server_string + "\r\n".encode()
    + "Content-Type: ".encode() + content_type + "\r\n".encode()
    + "Content-Length: ".encode() + content_length + "\r\n".encode()
    + "Connection: ".encode() + connection_header + "\r\n".encode()
    + "\r\n".encode())
        return response
    elif (extra=="error"): #special response for 400/501 requests 
        response = ("HTTP/1.1 ".encode() + status + " ".encode() + reason + "\r\n".encode()
    + "Date: ".encode() + date + "\r\n".encode()
    + "Server: ".encode() + server_string + "\r\n".encode()
    + "Content-Type: ".encode() + content_type + "\r\n".encode()
    + "Content-Length: ".encode() + content_length + "\r\n".encode()
    + "Connection: ".encode() + connection_header + "\r\n".encode()
    + "\r\n".encode() + body)
        return response
    else:  #used for 405 method not allowed 
        response = ("HTTP/1.1 ".encode() + status + " ".encode() + reason + "\r\n".encode()
    + "Date: ".encode() + date + "\r\n".encode()
    + "Server: ".encode() + server_string + "\r\n".encode()
    + "Content-Type: ".encode() + content_type + "\r\n".encode()
    + "Content-Length: ".encode() + content_length + "\r\n".encode()
    + "Connection: ".encode() + connection_header + "\r\n".encode() 
    + extra.encode() + "\r\n".encode() + body)
        return response











def handle_request(head, root):
    """TASK 1, extended in tasks 2 and 3. Turn one header block into a complete
    response.
    Task 1: 200 and 404. Task 2: HEAD, which carries no body, and Content-Type
    from the file extension. Task 3: 400 (malformed request line or header line,
    no Host), 405 (POST and the other known methods, with Allow: GET, HEAD) and
    501 (a token that is not an HTTP method)."""


    #if message not parsed correctly due to bad request, handle that specific response
    try:
        method,target,version,headers=parse_request(head) 
    except ValueError: #build the 40 bad request response
        #handle 400 Bad Request
        status=str(400)
        reason="Bad Request"
        body="400 Bad Request\n".encode()
        response=build_response(status,reason,body,"text/plain","error")
        return response


    if method not in KNOWN_METHODS:
        status=str(501)
        reason="Not Implemented"
        body="501 Not Implemented\n".encode()
        content_type="text/plain"
        return build_response(status,reason,body,content_type,"error")
    if method in KNOWN_METHODS and method not in ["GET","HEAD"]:
        status=str(405)
        reason="Method Not Allowed"
        body="405 Method Not Allowed\n".encode()
        content_type="text/plain"
        allow="Allow: GET, HEAD"
        return build_response(status,reason,body,content_type,allow)
   

    path=resolve_path(root,target) #build a proper path

    if (method == "GET"): #build get response
        if path is None or not (os.path.isfile(path)): #file not found, build 404 response
            status=str(404)
            reason="Not Found"
            body="404 Not Found\n".encode()
            content_type="text/plain"
            return build_response(status,reason,body,content_type,"GET")

        else: #everything went well - build a 200 OK response
            #build a 200 response
            status=str(200)
            reason="OK"
            
            #open file and read contents and place them in body variable
            opened_file=open(path,"rb") #open in read bytes mode
            body=opened_file.read()
            opened_file.close()

            content_type, encoding=mimetypes.guess_type(path) #look at file extenstion and determine type (e.g: png, jpg,pdf)
            if (content_type==None): #if type cannot be determined, set type to application/octet-stream
                content_type="application/octet-stream"
            return build_response(status,reason,body,content_type,"GET")

    elif (method=="HEAD"): #handle cases within a get response (either 404 or 200)
        if path is None or not (os.path.isfile(path)): #file not found, build 404 response
            status=str(404)
            reason="Not Found"
            body="404 Not Found\n".encode()
            content_type="text/plain"
            return build_response(status,reason,body,content_type,"HEAD")

        else:
            #build a 200 response
            status=str(200)
            reason="OK"
            
            #open file and read contents and place them in body variable
            opened_file=open(path,"rb") #open in read bytes mode
            body=opened_file.read()
            opened_file.close()

            content_type, encoding=mimetypes.guess_type(path) #determine file type from file extension
            if (content_type==None): #if file type cannot be determined, set it to application/octet-stream
                content_type="application/octet-stream"
            return build_response(status,reason,body,content_type,"HEAD")
    
    
    
        
        


def handle_connection(conn, root):
    """TASK 1, extended in tasks 3 and 5. Serve requests on one connection until
    the client closes it or it goes idle -- a few seconds; five is reasonable.
    Task 1: read the head (one recv() is enough for now), call handle_request,
    sendall() the response, and loop. Task 3: replace that read with
    recv_request_head. Task 5: after each response, increment requests_served
    under counter_lock and print 'served <n>' to stderr, where n is the value
    this request produced, read inside the same lock that incremented it."""
    global requests_served #requests_served causes an error without declaring it as global
    while 1:
        message = recv_request_head(conn)
        if message is None:
            break #stop serving client if it has disconnected
        response = handle_request(message,root) #send message received to handle_request
        conn.sendall(response) #send back the response that we received from handle_request 
        with counter_lock: #using a lock, increment the number of requests served
            requests_served+=1
            mine=requests_served
        print("served %d" % mine,file=sys.stderr,flush=True) 




def worker(work_queue, root):
    """TASK 5. Take accepted connections off work_queue and serve them, forever.
    Every worker thread runs this; none of them is created per connection.
    Nothing before task 5 calls this, and main must not start any worker threads
    until you write it."""
    while 1:
        client=work_queue.get() #get a client connection from the queue
        handle_connection(client,root) #pass the client to handle_connection
        client.close() #close the client when done
        




def main(argv=None):
    ###TO DO: may want to handle invalid arguments
    """TASK 1, replaced in task 5. Bind 127.0.0.1 on the requested port, listen,
    print the port line below, then serve connections.
    Task 1: accept one connection at a time and pass each to handle_connection.
    Task 5: replace that loop -- create --workers threads running worker() and a
    queue.Queue, and let main do nothing but accept and enqueue."""
    # Given. The grading script reads this line to find your server, so print it
    # exactly as written, immediately after listen(), and keep flush=True.
    #     print("Listening on port %d" % listener.getsockname()[1], flush=True)

    workers_queue=queue.Queue() #create the queue of workers

    args=parse_args(argv) #parse the arguments
    server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM) #create the socket object
    server_socket.bind(("127.0.0.1",args.port)) #bind the socket to ip address 127.0.0.1 and given port number
    server_socket.listen(1) #start listening
    print("Listening on port %d" % server_socket.getsockname()[1], flush=True) #prints on success

    for i in range (args.workers): #create the worker threads
        thread = threading.Thread(target=worker, args=(workers_queue,args.root))
        thread.start()
    

    while 1: #keep accepting clients and handling them
        client, address = server_socket.accept() #wait until a client connects to the server
        workers_queue.put(client)
        
    


if __name__ == "__main__":
    main()

   

