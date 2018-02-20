import asyncio
from contextlib import contextmanager

import aiohttp
import docker


@contextmanager
def using_container(docker_client, *args, **kwargs):
    container = docker_client.containers.run(*args, **kwargs, detach=True)

    while container.status == 'created':
        container.reload()

    try:
        yield container
    finally:
        container.kill()
        container.wait()
        container.remove()


async def main():
    dclient = docker.from_env()

    with using_container(
            dclient,
            image="abingham/aio-server",
            name="aio-server",
            ports={
                '4647/tcp': 4647,
            },
    ) as container:

        async with aiohttp.ClientSession() as session:
            async with session.get('http://docker.for.mac.host.internal:4647/foo') as resp:
                print(resp.status)
                print(await resp.text())

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
