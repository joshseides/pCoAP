#!/usr/bin/env python3

# This file is part of the Python aiocoap library project.
#
# Copyright (c) 2012-2014 Maciej Wasilak <http://sixpinetrees.blogspot.com/>,
#               2013-2014 Christian Amsüss <c.amsuess@energyharvesting.at>
#
# aiocoap is free software, this file is published under the MIT license as
# described in the accompanying LICENSE file.

"""This is a usage example of aiocoap that demonstrates how to implement a
simple client. See the "Usage Examples" section in the aiocoap documentation
for some more information."""

import logging
import asyncio
from aiocoap import *
import json
import time


logging.basicConfig(level=logging.INFO)

async def schedule_knn(address, port, protocol):
    print("HMM", address, port)
    request = Message(code=PARALLELIZE, uri='coap://{}:{}/knn'.format(address, port))
    response = await protocol.request(request).response
    print(response.payload.decode('ascii'))

async def main():
    protocol = await Context.create_client_context()

    start = time.time()

    # get worker nodes
    request = Message(code=GET, uri='coap://127.0.0.1:5000/parallelism-entity')
    response = await protocol.request(request).response
    entity = json.loads(response.payload.decode('ascii'))

    # schedule requests on worker nodes
    await asyncio.gather(*[schedule_knn(address, port, protocol) for address, port in entity])

    print('TIME ELAPSED: {} seconds'.format(time.time() - start))

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
