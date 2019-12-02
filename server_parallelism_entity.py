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


class ParallelismEntityResource(resource.Resource):
    """Example resource which supports the GET and PUT methods. It sends large
    responses, which trigger blockwise transfer."""

    def __init__(self, root):
        super().__init__()
        self.root = root

    async def render_get(self, request):
        entity = list(self.root.get_parallelism_entity_by_id(0))
        return aiocoap.Message(payload=json.dumps(entity).encode('ascii'))

    async def render_put(self, request):
        print('PUT payload: %s' % request.payload.decode('ascii'))
        payload = json.loads(request.payload.decode('ascii'))
        self.root.add_parallelism_entity_member(payload["entity"], (payload["address"], payload["port"]))
        entity = list(self.root.get_parallelism_entity_by_id(payload["entity"]))
        return aiocoap.Message(code=aiocoap.CHANGED, payload=json.dumps(entity).encode('ascii'))


# logging setup

logging.basicConfig(level=logging.INFO)
logging.getLogger("coap-server").setLevel(logging.DEBUG)

def main():
    # set up address and port
    address = '127.0.0.1'
    port = 5000

    # Resource tree creation
    root = resource.Site()

    root.add_resource(['.well-known', 'core'],
            resource.WKCResource(root.get_resources_as_linkheader))
    root.add_resource(['parallelism-entity'], ParallelismEntityResource(root))

    # set up server as parallelism directory
    root.set_up_as_parallelism_directory()
    root.create_parallelism_entity((address, port))

    asyncio.Task(aiocoap.Context.create_server_context(root, bind=(address, port)))

    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    main()
