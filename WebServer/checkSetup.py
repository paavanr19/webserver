# CMPT 371 Project 1 - setup check. Carries no marks and checks no answers.
"""Answers one question: can the grader run your submission at all?

Run it from inside your WebServer folder: python3 checkSetup.py
"""

import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
START_TIMEOUT = 6.0


def fail(message):
    print("setup PROBLEM: " + message)
    sys.exit(1)


def drain(stream, sink):
    for line in iter(stream.readline, ""):
        sink.append(line)


def main():
    if sys.version_info < (3, 11):
        fail("this is Python %d.%d; the project needs 3.11 or newer. Run it as python3."
             % sys.version_info[:2])
    for name in ("server.py", "client.py"):
        path = os.path.join(HERE, name)
        if not os.path.exists(path):
            fail("no file named %s in %s (the name is case-sensitive)" % (name, HERE))
        if not open(path, encoding="utf-8", errors="replace").readline().lstrip().startswith("#"):
            fail("line 1 of %s is not a comment; it must hold your name and student number" % name)

    root = tempfile.mkdtemp()
    with open(os.path.join(root, "index.html"), "w") as fh:
        fh.write("<html><body>ok</body></html>")
    proc = subprocess.Popen([sys.executable, "server.py", "--port", "0", "--root", root,
                             "--workers", "4"], cwd=HERE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True)
    # The deadline has to be enforced by the clock, not by readline(). A server
    # that binds and listens but never prints anything leaves readline() blocked
    # forever, and before the 2026-09-03 audit that is what this loop did: the
    # script promised a diagnosis in six seconds and instead hung indefinitely,
    # on one of the two failures it exists to name.
    out, err = [], []
    threading.Thread(target=drain, args=(proc.stdout, out), daemon=True).start()
    threading.Thread(target=drain, args=(proc.stderr, err), daemon=True).start()
    port, deadline = None, time.time() + START_TIMEOUT
    while time.time() < deadline:
        match = re.search(r"[Ll]istening on port\s+(\d+)", "".join(out))
        if match:
            port = int(match.group(1))
            break
        if proc.poll() is not None:
            break
        time.sleep(0.05)
    if port is None:
        proc.kill()
        shutil.rmtree(root, ignore_errors=True)
        detail = ("".join(err) or "".join(out)).strip().splitlines()
        fail("server.py did not print 'Listening on port <n>' on stdout within %d seconds "
             "(check the flag names, and flush the print)%s"
             % (START_TIMEOUT, ("; it said: " + detail[-1][:200]) if detail else ""))
    if port == 0:
        proc.kill()
        shutil.rmtree(root, ignore_errors=True)
        fail("server.py printed 'Listening on port 0'. --port 0 asks the operating system for "
             "a free port; print the port it actually assigned, from getsockname()")

    try:
        sock = socket.create_connection(("127.0.0.1", port), 5)
        sock.settimeout(5)
        sock.sendall(b"GET /index.html HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n")
        if not sock.recv(64).startswith(b"HTTP/"):
            fail("server.py answered, but not with a line starting 'HTTP/'")
        sock.close()
        result = subprocess.run([sys.executable, "client.py", "--host", "127.0.0.1", "--port",
                                 str(port), "--path", "/index.html", "--out",
                                 os.path.join(root, "got")], cwd=HERE, capture_output=True,
                                timeout=15)
        if result.returncode != 0:
            fail("client.py exited %d with the documented flags: %s"
                 % (result.returncode, result.stderr.decode()[-200:].strip()))
    except (OSError, subprocess.TimeoutExpired) as exc:
        fail("server.py or client.py could not complete one request: %s" % exc)
    finally:
        proc.kill()
        shutil.rmtree(root, ignore_errors=True)

    if os.path.basename(HERE) != "WebServer":
        print("warning: this folder is named %r, not 'WebServer'" % os.path.basename(HERE))
    if not os.path.exists(os.path.join(HERE, "readme.pdf")):
        print("warning: no readme.pdf here; that line scores 0 without it")
    print("setup OK")


if __name__ == "__main__":
    main()
