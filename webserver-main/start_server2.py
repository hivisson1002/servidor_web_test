#!/usr/bin/env python3
"""
Usage: ./start_server -p(multi process)? -t(multi thread)? -w? <workers>

This will create a HTTP server listening at LOCALHOST:PORT
"""

import socket
import multiprocessing
import threading
import os
import time
import argparse

# Max number of connections in the socket queue
BACKLOG = 5

# Max size of data read from a socket
MAX_DATA_SIZE = 1024

# Encoding style
STYLE = "utf-8"

# Localhost
LOCALHOST = "127.0.0.1"

# Port to start the server at
PORT = 2000

# Number of Worker processes/threads
WORKER_SIZE = 5

# Uses multi-processing if set to 0
USE_THREADING = 0

# Global shutdown variable
shutdown = False

# Timeout for socket.accept()
SOCK_TIMEOUT = 2

def cpu_bound_task():
    print("Running CPU bound task")
    # A dummy CPU bound task
    def is_prime(n):
        if n <= 1:
            return False
        elif n == 2:
            return True
        elif n % 2 == 0:
            return False
        else:
            for i in range(3, int(n**0.5) + 1, 2):
                if n % i == 0:
                    return False
            return True

    def find_primes_in_range(start, end):
        primes = []
        for number in range(start, end + 1):
            if is_prime(number):
                primes.append(number)
        return primes

    res = find_primes_in_range(1, 1000000)
    print("CPU bound task completed")

def io_bound_task():
    print("Running I/O bound task")
    # Simulates a file read or any other operation that requires I/O
    time.sleep(1)
    print("I/O bound task completed")

def get_page(path):
    # Special set-up for testing
    if path == "/cpu":
        path = "/"
        cpu_bound_task()

    if path == "/io":
        path = "/"
        io_bound_task()

    WEB_DIR = "www"  # Directory to store all webpages
    if path == "":
        return None
    if path == "/":
        path = "/index.html"

    try:
        with open(WEB_DIR + path, 'r') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        return None

def handle_request(client_socket):
    data = client_socket.recv(MAX_DATA_SIZE).decode(STYLE)
    lines = data.split('\r\n')
    if lines:
        line = lines[0]
        words = line.split(' ')
        path = "" if len(words) < 2 else words[1]
        content = get_page(path)
        response_code = "200 OK" if content else "404 Not Found"
        # Create the response
        response = f"HTTP/1.1 {response_code}\r\n\r\n"
        if content:
            response += f"{content}\r\n"
        # Respond to the client
        client_socket.sendall(response.encode(STYLE))

def setup_server(host, port):
    """
    Returns a socket listening on (host, port)
    """
    # Create a socket object
    # socket.AF_INET: indicates IPv4
    # socket.SOCK_STREAM: indicates TCP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Allow reuse of the local address the socket is bound to.
    # Avoids the "Address already in use" error that might occur if the server
    # is restarted and the previous socket is still in the TIME_WAIT state.
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind the socket to a specific host and port
    # Should complain if host or port is not valid
    server_socket.bind((host, port))

    # Timeout is essential to prevent waiting forever
    server_socket.settimeout(SOCK_TIMEOUT)

    # Start listening
    server_socket.listen(BACKLOG)
    print(f"Server listening on {host}:{port}")
    return server_socket

def handle_connections(server_socket):
    """
    Accepts HTTP requests (forever) listening on server_socket
    """
    print(f"Starting connection worker for {server_socket.getsockname()},"
          f" pid: {os.getpid()}, tid: {threading.get_ident()}")
    global shutdown
    while not shutdown:
        client_socket = None
        try:
            # Wait for a connection
            # Note that accept() is thread safe
            client_socket, client_address = server_socket.accept()
            print(f"Received a new connection from {client_address}")
            handle_request(client_socket)
        except socket.timeout:
            pass
        except socket.error as e:
            if e.errno == 10035:  # WSAEWOULDBLOCK
                # Non-blocking call, try again later
                continue
            else:
                print(str(e))
        except SystemExit:
            print("Worker terminating....")
        except Exception as e:
            print(str(e))
        finally:
            if client_socket:
                client_socket.close()
                print(f"Closed the connection from {client_address}")
    # Close the connection (will not happen if worker gets terminated!)
    print(f"Closing connection worker for: pid: {os.getpid()},"
          f" tid: {threading.get_ident()}")

def get_args():
    # ToDo: Enhance this to include host and port as well
    parser = argparse.ArgumentParser(description="A script to start a basic HTTP server")
    parser.add_argument("-p", "--process", action='store_true',
                        help="Flag indicating server will run in multi-process mode")
    parser.add_argument("-t", "--thread", action='store_true',
                        help="Flag indicating server will run in multi-thread mode")
    parser.add_argument('-w', '--workers', type=int, help='Number of workers')
    args = parser.parse_args()
    if args.process and args.thread:
        raise ValueError("Please use -p OR -t")
    return args

def main():
    server_host = LOCALHOST
    server_port = PORT
    server_socket = None
    args = get_args()

    if args.thread:
        global USE_THREADING
        USE_THREADING = True
    if args.workers:
        global WORKER_SIZE
        WORKER_SIZE = args.workers

    try:
        server_socket = setup_server(server_host, server_port)
    except Exception as e:
        print(str(e))
        print("setup_server failed! Exiting...")
        return

    if server_socket is None:
        print("Invalid server socket. Exiting")
        return

    workers = []

    for i in range(WORKER_SIZE):
        p = None
        if USE_THREADING:
            p = threading.Thread(target=handle_connections, args=(server_socket,))
        else:
            p = multiprocessing.Process(target=handle_connections, args=(server_socket,))
        workers.append(p)

    for worker in workers:
        worker.start()

    try:
        print(f"Main thread tid: {threading.get_ident()}")
        # Wait until main process is manually killed
        while True:
            # Do nothing
            pass
    except KeyboardInterrupt:
        print(f"\nExiting due to a Keyboard interrupt\n")
    finally:
        global shutdown
        shutdown = True
        # Close all the workers
        if not USE_THREADING:
            for worker in workers:
                worker.terminate()

        # Wait for all workers to join
        for worker in workers:
            # In case of threads this will wait
            # forever, user will have to send
            # keyboard interrupt again
            # Not optimal.
            worker.join()

        print("Server is shutting down.")
        # Close the server socket
        if server_socket:
            server_socket.close()

if __name__ == "__main__":
    main()
