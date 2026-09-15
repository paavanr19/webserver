# Name: <your full name>   Student number: <your student number>
"""CMPT 371 Project 1 - HTTP/1.1 client on a raw TCP socket.

Usage: python3 client.py --host H --port P --path /a [--path /b] [--out FILE ...]
"""

import argparse
import socket
import sys


def parse_args(argv):
    """TASK 4. Parse --host (default 127.0.0.1), --port (int), --path
    (repeatable), --out (repeatable, paired with --path in order)."""
    raise NotImplementedError


def send_request(sock, host, path):
    """TASK 4. Send one GET request line, a Host header, and the blank line
    that ends it."""
    raise NotImplementedError


def read_head(sock, pending):
    """TASK 4. Read until the blank line ending the response head.
    Return (head_bytes, leftover) where leftover is body already received. The
    leftover is the start of the body and cannot be read again, so it must be
    counted toward Content-Length rather than discarded."""
    raise NotImplementedError


def parse_head(head):
    """TASK 4. Split a response head into (status_code, reason, headers).
    headers is a dict with lower-cased names."""
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
    raise NotImplementedError


if __name__ == "__main__":
    sys.exit(main())
