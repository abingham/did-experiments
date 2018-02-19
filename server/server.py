from aiohttp import web


async def handle_foo(request):
    return web.Response(text="foo")

app = web.Application()
app.router.add_get("/foo", handle_foo)

web.run_app(app, port=4647)
