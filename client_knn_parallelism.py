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

num_recs = 5

async def schedule_knn(address, port, protocol, index, length, res):
    # create request
    body = {'num_recs': num_recs, 'movie_title': 'Pocahontas (1995)', 'index': index, 'length': length}
    payload = json.dumps(body).encode('ascii')
    request = Message(code=PARALLELIZE, payload=payload, uri='coap://{}:{}/knn'.format(address, port))

    # send request to parallelism worker
    response = await protocol.request(request).response
    movies = json.loads(response.payload.decode('ascii'))

    # concatenate top movie result from shard to result list
    res += movies

async def main():
    protocol = await Context.create_client_context()

    start = time.time()

    # get active worker nodes
    request = Message(code=GET, uri='coap://127.0.0.1:5000/parallelism-entity')
    response = await protocol.request(request).response
    entity = json.loads(response.payload.decode('ascii'))

    # result list for shard results
    res = []

    # schedule knn requests on worker nodes
    await asyncio.gather(*[
        schedule_knn(address, port, protocol, i, len(entity), res)
        for i, (address, port) in enumerate(entity)
    ])

    # sort movie distances in ascending order
    res.sort(key=lambda x: float(x[2]))

    # return top 5 movie recommendations
    print("YOUR RECOMMENDATIONS: ", res[:num_recs])

    # measure computation speed
    print('TIME ELAPSED: {} seconds'.format(time.time() - start))

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
