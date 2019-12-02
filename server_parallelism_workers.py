#!/usr/bin/env python3

# This file is part of the Python aiocoap library project.
#
# Copyright (c) 2012-2014 Maciej Wasilak <http://sixpinetrees.blogspot.com/>,
#               2013-2014 Christian Amsüss <c.amsuess@energyharvesting.at>
#
# aiocoap is free software, this file is published under the MIT license as
# described in the accompanying LICENSE file.

"""This is a usage example of aiocoap that demonstrates how to implement a
simple server. See the "Usage Examples" section in the aiocoap documentation
for some more information."""

import datetime
import logging

import asyncio

import aiocoap.resource as resource
import aiocoap

import json


class BlockResource(resource.Resource):
    """Example resource which supports the GET and PUT methods. It sends large
    responses, which trigger blockwise transfer."""

    def __init__(self):
        super().__init__()
        self.set_content(b"This is the resource's default content. It is padded "\
                b"with numbers to be large enough to trigger blockwise "\
                b"transfer.\n")

    def set_content(self, content):
        self.content = content
        while len(self.content) <= 1024:
            self.content = self.content + b"0123456789\n"

    async def render_get(self, request):
        return aiocoap.Message(payload=self.content)

    async def render_put(self, request):
        print('PUT payload: %s' % request.payload)
        self.set_content(request.payload)
        return aiocoap.Message(code=aiocoap.CHANGED, payload=self.content)


# logging setup

logging.basicConfig(level=logging.INFO)
logging.getLogger("coap-server").setLevel(logging.DEBUG)

async def setup(index):
    # set up address and port
    address = '127.0.0.1'
    port = 5000 + index

    # Resource tree creation
    root = resource.Site()

    root.add_resource(['.well-known', 'core'],
            resource.WKCResource(root.get_resources_as_linkheader))
    root.add_resource(['other', 'block'], BlockResource())

    protocol = await asyncio.Task(aiocoap.Context.create_server_context(root, bind=('127.0.0.1', port)))

    payload = {"entity": 0, "address": address, "port": port}
    s_payload = json.dumps(payload).encode('ascii')
    uri = 'coap://127.0.0.1:5000/parallelism-entity'

    # add this worker to parallelism entity
    request = aiocoap.Message(code=aiocoap.PUT, payload=s_payload, uri=uri)

    try:
        response = await protocol.request(request).response
    except Exception as e:
        print('Failed to fetch resource:')
        print(e)
    else:
        print('Result: %s\n%r'%(response.code, json.loads(response.payload.decode('ascii'))))

def main():
    for i in range(1, 6):
        asyncio.get_event_loop().run_until_complete(setup(i))
    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    main()
