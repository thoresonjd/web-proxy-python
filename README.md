# **Web Proxy**

A simple proxy server that handles HTTP requests and caches successful responses.

## **Author**

Justin Thoreson

## **Only supports**:
* `HTTP/1.1` or earlier
* `GET` requests
* Status codes `200`, `404`, and `500`

## **Usage**

To execute the web proxy on `localhost`, run:
```
python3 proxy.py <PORT>
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