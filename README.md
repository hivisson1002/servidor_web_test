This is a basic HTTP server written from scratch in Python which can respond to GET requests for webpages stored in `www` directory. The motivation behind this project is [this coding challenge](https://codingchallenges.fyi/challenges/challenge-webserver).

Beyond learning to deal with sockets, in this project, multiple server architechures are implemented along with a testing framework to understand how they compare against one another.

To start the HTTP server in multi-processing mode, you need to run:
```
./start_server -p
```

To start the HTTP server in multi-threading mode, you need to run:
```
./start_server -t
```

To start the HTTP server in async(coroutine) mode, you need to run:
```
./start_async_server
```

Multi-processing(threading) modes are implemented by spinning up a number of worker processes(threads) dedicated to listening and processing client requests. Default number of workers is 5, and can be configured using:
 ```
$:~/path_to_your_repo/webserver (main)$./start_server -p -w 3
Server listening on 127.0.0.1:2000
Starting connection worker for ('127.0.0.1', 2000), pid: 26417, tid: 140647853301760
 Main thread tid: 140647853301760
Starting connection worker for ('127.0.0.1', 2000), pid: 26418, tid: 140647853301760
Starting connection worker for ('127.0.0.1', 2000), pid: 26419, tid: 140647853301760

```

To talk to this HTTP server, you can use `curl`:
```
$:~/path_to_your_repo/webserver (main)$curl -i 127.0.0.1:2000
HTTP/1.1 200 OK

<!DOCTYPE html>
<html lang="en">
  <head>
    <title>Simple Web Page</title>
  </head>
  <body>
    <h1>Test Web Page</h1>
    <p>My web server served this page!</p>
  </body>
</html>
```

or you can use send_to_server:
```
$:~/path_to_your_repo/webserver (main)$./send_to_server 127.0.0.1 2000 "GET / HTTP/1.1"
HTTP/1.1 200 OK
...
...
```

or you can type below into your browser as well:
```
http://127.0.0.1:2000/
```

To compare against different architectures, you can start the HTTP server in the mode you want and use `./test_my_server` to send concurrent connections to the server, and get back the overall response time. Example usage:
```
$:~/path_to_your_repo/webserver (main)$./test_my_server -i -nc 4 127.0.0.1 2000
http://127.0.0.1:2000/io - Status Code: 200, took 1072.60 ms
http://127.0.0.1:2000/io - Status Code: 200, took 1102.88 ms
http://127.0.0.1:2000/io - Status Code: 200, took 2155.36 ms
http://127.0.0.1:2000/io - Status Code: 200, took 2211.57 ms
Total time taken 2216.14 ms
```

Use `-c` to test cpu bound task, and `-i` for i/o bound task. Number of concurrent connection the test scripts tries to make is configurable by `-nc`.

Preliminary stats are available in the file `Performance Stats.xlsx`. 

Following graphs show response time for different architectures (in ms) as number of clients increase. (These were generated with 5 workers)

![alt text](CPU_Bound_Task.png)
![alt text](I_O_Bound_Task.png)

Couple of things evident from above data:

- Asyncio is really good for I/O bound task as all coroutines can wait in parallel
- Multi-threaded server in Python is can not beat other archs as GIL prevents true parallel processing
- If your request is CPU heavy, multi-processing continues to be the most performant

Looks like a server implementing multi-processing architecture, where each process (worker) can handle incoming request asynchronously can be best of both world for a generic set of requests.


