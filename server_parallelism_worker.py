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
import time
import sys


class KNNResource(resource.Resource):
    """Example resource which supports the GET and PUT methods. It sends large
    responses, which trigger blockwise transfer."""

    def __init__(self):
        super().__init__()

    async def render_parallelize(self, request):
        time.sleep(1)
        return aiocoap.Message(payload='this was an intense computation'.encode('ascii'))


# logging setup

logging.basicConfig(level=logging.INFO)
logging.getLogger("coap-server").setLevel(logging.DEBUG)

async def setup(index):
    # set up address and port
    address = '127.0.0.1'
    port = 5000 + int(index)

    # Resource tree creation
    root = resource.Site()

    root.add_resource(['.well-known', 'core'],
            resource.WKCResource(root.get_resources_as_linkheader))
    root.add_resource(['knn'], KNNResource())

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
    if len(sys.argv) < 2:
        raise ValueError('Need second argument specifying 5000 + i port number index')
    asyncio.get_event_loop().run_until_complete(setup(sys.argv[1]))
    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    main()
