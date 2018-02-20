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
