# Docker-in-Docker webserver experiment

I'm trying to figure out how to run a docker container from another container,
something knows as docker-in-docker. The "client" container will first start an
"server" container. This server container will run a webserver and expose an HTTP
port from the container. The client container will then run a simple web client
that attempts to get an HTTP resource from the server container's server. Simple,
right?

## Why?

I'm doing this because this is how we're planning to implement REPLs in
cyber-dojo. A long-lived container, `runner_repl`, will launch sub-containers,
`repl_containers`, when new REPL processes are needed. `runner_repl` will proxy
HTTP and websocket traffix to `repl_container`s. So this experiment is a
simplified version of that scenario to make sure we can get the plumbing to
work.

## Experiment 1: Launching containers from Python

I'm implementing this experiment (and the cyber-dojo work) in Python. So step
one is to figure out how to run docker commands from Python. Fortunately, the
excellent [docker-py](https://github.com/docker/docker-py) project makes that
pretty simple.

So our first experiment is to create a Python program that can launch the server
container and fetch a resource from it. Critically, this is *not* using
docker-in-docker; we're just creating a container from a Python process.

The code in git tag `experiment-1` implements this experiment. Interestingly, I
was only able to make this work on my mac by using Docker Toolkit.

To try it out, do something like this from the project root (and probably from a Python virtual environment):
```
git
docker rm -f aio-server
docker build -t abingham/aio-server server
pip install -r client/requirements.txt
python client/client.py
```

It should print something like:
```
200
foo
```

### Things to note

There are a few things to note about this experiment. First, as mentioned above,
it only worked on Docker Toolbox. On normal Docker for Mac it just fell over
with an error like this:

```
Traceback (most recent call last):
  File "client.py", line 41, in <module>
    asyncio.get_event_loop().run_until_complete(main())
  File "/usr/lib/python3.6/asyncio/base_events.py", line 466, in run_until_complete
    return future.result()
  File "client.py", line 36, in main
    async with session.get('http://docker.for.mac.host.internal:4647/foo') as resp:
  File "/usr/lib/python3.6/site-packages/aiohttp/client.py", line 779, in __aenter__
    self._resp = await self._coro
  File "/usr/lib/python3.6/site-packages/aiohttp/client.py", line 331, in _request
    await resp.start(conn, read_until_eof)
  File "/usr/lib/python3.6/site-packages/aiohttp/client_reqrep.py", line 678, in start
    (message, payload) = await self._protocol.read()
  File "/usr/lib/python3.6/site-packages/aiohttp/streams.py", line 533, in read
    await self._waiter
aiohttp.client_exceptions.ServerDisconnectedError: None
```

That is, the server seems to be disconnecting for no good reason.

Second, I used the default network mode. I would have thought that I would have
to specify "host", but that was not the case. With the default settings, the
Python process was able to connect to the server container's expose port 4647 at
IP address 0.0.0.0.

All in all, this gives me confidence that `docker-py` is a good tool for the
job.

## Experiment 2: Docker-in-docker

The next step is to run the client in a container. It will launch a nested
container with the server, just like before. As I understand things, if we can
get this to work, then we can get the full cyber-dojo REPL system to work.

### 2A: Simply trying `docker run`

As a first attempt, I just built a docker image that runs the `client.py`
script. I then ran it in as simple a manner as possible, something like this:

```
docker rm -f aio-server aio-client
docker build -t abingham/aio-server server
docker build -t abingham/aio-client client
docker run abingham/aio-client
```

Unfortunately this fails with a dramatic exception:

```
% docker run abingham/aio-client
Traceback (most recent call last):
  File "/usr/lib/python3.6/site-packages/urllib3/connectionpool.py", line 601, in urlopen
    chunked=chunked)
  File "/usr/lib/python3.6/site-packages/urllib3/connectionpool.py", line 357, in _make_request
    conn.request(method, url, **httplib_request_kw)
  File "/usr/lib/python3.6/http/client.py", line 1239, in request
    self._send_request(method, url, body, headers, encode_chunked)
  File "/usr/lib/python3.6/http/client.py", line 1285, in _send_request
    self.endheaders(body, encode_chunked=encode_chunked)
  File "/usr/lib/python3.6/http/client.py", line 1234, in endheaders
    self._send_output(message_body, encode_chunked=encode_chunked)
  File "/usr/lib/python3.6/http/client.py", line 1026, in _send_output
    self.send(msg)
  File "/usr/lib/python3.6/http/client.py", line 964, in send
    self.connect()
  File "/usr/lib/python3.6/site-packages/docker/transport/unixconn.py", line 46, in connect
    sock.connect(self.unix_socket)
FileNotFoundError: [Errno 2] No such file or directory

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/lib/python3.6/site-packages/requests/adapters.py", line 440, in send
    timeout=timeout
  File "/usr/lib/python3.6/site-packages/urllib3/connectionpool.py", line 639, in urlopen
    _stacktrace=sys.exc_info()[2])
  File "/usr/lib/python3.6/site-packages/urllib3/util/retry.py", line 357, in increment
    raise six.reraise(type(error), error, _stacktrace)
  File "/usr/lib/python3.6/site-packages/urllib3/packages/six.py", line 685, in reraise
    raise value.with_traceback(tb)
  File "/usr/lib/python3.6/site-packages/urllib3/connectionpool.py", line 601, in urlopen
    chunked=chunked)
  File "/usr/lib/python3.6/site-packages/urllib3/connectionpool.py", line 357, in _make_request
    conn.request(method, url, **httplib_request_kw)
  File "/usr/lib/python3.6/http/client.py", line 1239, in request
    self._send_request(method, url, body, headers, encode_chunked)
  File "/usr/lib/python3.6/http/client.py", line 1285, in _send_request
    self.endheaders(body, encode_chunked=encode_chunked)
  File "/usr/lib/python3.6/http/client.py", line 1234, in endheaders
    self._send_output(message_body, encode_chunked=encode_chunked)
  File "/usr/lib/python3.6/http/client.py", line 1026, in _send_output
    self.send(msg)
  File "/usr/lib/python3.6/http/client.py", line 964, in send
    self.connect()
  File "/usr/lib/python3.6/site-packages/docker/transport/unixconn.py", line 46, in connect
    sock.connect(self.unix_socket)
urllib3.exceptions.ProtocolError: ('Connection aborted.', FileNotFoundError(2, 'No such file or directory'))

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "client.py", line 41, in <module>
    asyncio.get_event_loop().run_until_complete(main())
  File "/usr/lib/python3.6/asyncio/base_events.py", line 467, in run_until_complete
    return future.result()
  File "client.py", line 31, in main
    '4647/tcp': 4647,
  File "/usr/lib/python3.6/contextlib.py", line 81, in __enter__
    return next(self.gen)
  File "client.py", line 10, in using_container
    container = docker_client.containers.run(*args, **kwargs, detach=True)
  File "/usr/lib/python3.6/site-packages/docker/models/containers.py", line 745, in run
    detach=detach, **kwargs)
  File "/usr/lib/python3.6/site-packages/docker/models/containers.py", line 803, in create
    resp = self.client.api.create_container(**create_kwargs)
  File "/usr/lib/python3.6/site-packages/docker/api/container.py", line 403, in create_container
    return self.create_container_from_config(config, name)
  File "/usr/lib/python3.6/site-packages/docker/api/container.py", line 413, in create_container_from_config
    res = self._post_json(u, data=config, params=params)
  File "/usr/lib/python3.6/site-packages/docker/api/client.py", line 251, in _post_json
    return self._post(url, data=json.dumps(data2), **kwargs)
  File "/usr/lib/python3.6/site-packages/docker/utils/decorators.py", line 46, in inner
    return f(self, *args, **kwargs)
  File "/usr/lib/python3.6/site-packages/docker/api/client.py", line 188, in _post
    return self.post(url, **self._set_request_timeout(kwargs))
  File "/usr/lib/python3.6/site-packages/requests/sessions.py", line 555, in post
    return self.request('POST', url, data=data, json=json, **kwargs)
  File "/usr/lib/python3.6/site-packages/requests/sessions.py", line 508, in request
    resp = self.send(prep, **send_kwargs)
  File "/usr/lib/python3.6/site-packages/requests/sessions.py", line 618, in send
    r = adapter.send(request, **kwargs)
  File "/usr/lib/python3.6/site-packages/requests/adapters.py", line 490, in send
    raise ConnectionError(err, request=request)
requests.exceptions.ConnectionError: ('Connection aborted.', FileNotFoundError(2, 'No such file or directory'))
```

The upshot of this is that the python script in the client wasn't able to create
a new container. And it wasn't able to do this because it couldn't connect to
the docker server.

## Experiment 2b: Hard-code the docker-toolbox environment variables into the client

My guess as to the problem is that the Docker Toolbox environment isn't properly
configured in the client container. Docker Toolbox defines a few variables that
the docker-py client constructor uses for connection:

```
DOCKER_HOST=tcp://192.168.99.100:2376
DOCKER_MACHINE_NAME=default
DOCKER_TLS_VERIFY=1
DOCKER_CERT_PATH=/Users/abingham/.docker/machine/machines/default
```

So as a first guess, I'm going to try hard-coding these values into a dict that
we use to construct the docker client.

The first problem with this is that the `DOCKER_CERT_PATH` doesn't exist in the
client container. So we might need to map that directory into the client
container. But that's getting out into the weeds...

## Experiment 2c: Try it with normal Docker for Mac

Before going on what might be a very wild goose chase with Docker Toolbox, I
want to try the docker on docker in normal Docker for Mac. The first attempt at
the failed with errors identical to what we saw in 2A. A bit of googling around
taught me that I need to map the docker docket into the container like this:

```
docker run -v /var/run/docker.sock:/var/run/docker.sock abingham/aio-client
```

With this in place, I get a different and more interesting error:
```
% docker run -v /var/run/docker.sock:/var/run/docker.sock abingham/aio-client
Traceback (most recent call last):
  File "/usr/lib/python3.6/site-packages/aiohttp/connector.py", line 800, in _wrap_create_connection
    return await self._loop.create_connection(*args, **kwargs)
  File "/usr/lib/python3.6/asyncio/base_events.py", line 776, in create_connection
    raise exceptions[0]
  File "/usr/lib/python3.6/asyncio/base_events.py", line 763, in create_connection
    yield from self.sock_connect(sock, address)
  File "/usr/lib/python3.6/asyncio/selector_events.py", line 451, in sock_connect
    return (yield from fut)
  File "/usr/lib/python3.6/asyncio/selector_events.py", line 481, in _sock_connect_cb
    raise OSError(err, 'Connect call failed %s' % (address,))
ConnectionRefusedError: [Errno 111] Connect call failed ('0.0.0.0', 4647)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "client.py", line 41, in <module>
    asyncio.get_event_loop().run_until_complete(main())
  File "/usr/lib/python3.6/asyncio/base_events.py", line 466, in run_until_complete
    return future.result()
  File "client.py", line 36, in main
    async with session.get('http://0.0.0.0:4647/foo') as resp:
  File "/usr/lib/python3.6/site-packages/aiohttp/client.py", line 779, in __aenter__
    self._resp = await self._coro
  File "/usr/lib/python3.6/site-packages/aiohttp/client.py", line 319, in _request
    traces=traces
  File "/usr/lib/python3.6/site-packages/aiohttp/connector.py", line 418, in connect
    traces=traces
  File "/usr/lib/python3.6/site-packages/aiohttp/connector.py", line 736, in _create_connection
    traces=None
  File "/usr/lib/python3.6/site-packages/aiohttp/connector.py", line 855, in _create_direct_connection
    raise last_exc
  File "/usr/lib/python3.6/site-packages/aiohttp/connector.py", line 838, in _create_direct_connection
    req=req, client_error=client_error)
  File "/usr/lib/python3.6/site-packages/aiohttp/connector.py", line 807, in _wrap_create_connection
    raise client_error(req.connection_key, exc) from exc
aiohttp.client_exceptions.ClientConnectorError: Cannot connect to host 0.0.0.0:4647 ssl:False [Connect call failed ('0.0.0.0', 4647)]
```

Now I'm seeing a failure of name resolution *in the client script*. So we've
created the server and client containers, but the client isn't able to find the
server at the expected location.

I'm not entirely sure I understand why this is happening. From what I gather,
networking on Docker for Mac is quite limited. You can read the gory details
[here](https://docs.docker.com/docker-for-mac/networking/#known-limitations-use-cases-and-workarounds).
One hint in there, though, is that we can use the magical host
`docker.for.mac.host.internal`. If I use this address, I see the strange disconnection that I saw in experiment 1:

```
Traceback (most recent call last):
  File "client.py", line 41, in <module>
    asyncio.get_event_loop().run_until_complete(main())
  File "/usr/lib/python3.6/asyncio/base_events.py", line 466, in run_until_complete
    return future.result()
  File "client.py", line 36, in main
    async with session.get('http://docker.for.mac.host.internal:4647/foo') as resp:
  File "/usr/lib/python3.6/site-packages/aiohttp/client.py", line 779, in __aenter__
    self._resp = await self._coro
  File "/usr/lib/python3.6/site-packages/aiohttp/client.py", line 331, in _request
    await resp.start(conn, read_until_eof)
  File "/usr/lib/python3.6/site-packages/aiohttp/client_reqrep.py", line 678, in start
    (message, payload) = await self._protocol.read()
  File "/usr/lib/python3.6/site-packages/aiohttp/streams.py", line 533, in read
    await self._waiter
aiohttp.client_exceptions.ServerDisconnectedError: None
```

While disappointing, this actually seems to be good news! It seems I was able to
spin up both containers and connect to the server.

## Experiment 2d: Try the macvlan network mode if possible

TODO


# Experiment 3: Mac is hard, let's try linux

At this point I'm pretty sure that my problems stem from Docker on Mac, so I
think the smart thing to do is try this in the Docker motherland, Linux. I'm
going to create a linux VM and see what happens there. It's turtles all the way
down...
