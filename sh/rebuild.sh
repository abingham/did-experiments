docker rmi -f abingham/aio-server
docker rmi -f abingham/aio-client

docker build -t abingham/aio-server server
docker build -t abingham/aio-client client
