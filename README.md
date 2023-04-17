# **Web Proxy**

A simple proxy server that handles HTTP requests between clients and servers and caches successful responses.

## **Author**

Justin Thoreson

## **Supports**
* `HTTP/1.1` and earlier
* `GET` requests
* Status codes `200`, `404`, and `500`

Since the proxy supports up to `HTTP/1.1` but uses non-persistent connections, it really just supports `HTTP/1.0`. Thus, we can humorously think of this proxy as supporting `HTTP/1.05`.

## **Usage**

To execute the web proxy on `localhost`, run:
```
python3 main.py <PORT>
```

One way of sending requests to the web proxy is to use Telnet. To connect to the
proxy via Telnet, run:
```
telnet localhost <PORT>
```

When telnet establishes a connection with the web proxy, requests can then be
issued. Requests take the following format:
```
<METHOD> <URI> <HTTP VERSION>
```

An example of a properly formatted request is as follows:
```
GET http://hostname/path HTTP/1.1
```

## **Files**
* `main.py` - Main script that runs the web proxy
* `Proxy.py` - Proxy class for handling traffic between clients and servers
* `Cache.py` - Cache class for handling cached items in the filesystem
* `HTTPRequest.py` - Wrapper class for an HTTP request
* `HTTPResponse.py` - Wrapper class for an HTTP response
* `RequestError.py` - Custom exception representing an error with an HTTP request