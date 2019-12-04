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
import numpy as np
import pandas as pd
from itertools import islice


class KNNResource(resource.Resource):
    """Resource managing KNN recommendation algorithm for movie-rating data."""

    def __init__(self):
        super().__init__()

        # pre-process full data set
        self._load_movie_data()

    def _load_movie_data(self):
        # import movie data
        movie_data = pd.read_csv("data/movies-small.csv",
            usecols=['movieId', 'title'],
            dtype={'movieId': 'int32', 'title': 'str'})

        # import corresponding ratings
        rating_data = pd.read_csv("data/ratings-small.csv",
            usecols=['userId', 'movieId', 'rating'],
            dtype={'userId': 'int32', 'movieId': 'int32', 'rating': 'float32'})

        print("read in csv")

        # determine least popular movies and drop
        movies_count = pd.DataFrame(rating_data.groupby('movieId').size(), columns=['count'])
        popular_movie_ids = movies_count[movies_count['count'] >= 50].index
        ratings_drop_movies = rating_data[rating_data.movieId.isin(popular_movie_ids)]
        updated_movie_data = movie_data[movie_data.movieId.isin(popular_movie_ids)]

        print("drop least popular movies")

        # determine least active users and drop
        ratings_count = pd.DataFrame(rating_data.groupby('userId').size(), columns=['count'])
        active_user_ids = ratings_count[ratings_count['count'] >= 50].index
        ratings_drop_movies_users = ratings_drop_movies[ratings_drop_movies.userId.isin(active_user_ids)]

        print("drop least active users")

        # create movie vs user matrix for KNN computations
        self.data = ratings_drop_movies_users.pivot(index='movieId', columns='userId', values='rating').fillna(0)

        # reformat movie_data to be indexed on movie_id
        movie_data = movie_data.set_index('movieId')
        self.movie_mapping = movie_data

    def _euclidean_distance(self, x, y):
        return np.linalg.norm(x - y)

    async def render_parallelize(self, request):
        payload = json.loads(request.payload.decode('ascii'))

        # load parameters
        num_recs = int(payload["num_recs"])
        movie_title = payload["movie_title"]
        index = int(payload["index"])
        length = int(payload["length"])
        print('PARALLELIZE payload: %s' % payload)

        # get id for input movie
        movie_id = self.movie_mapping[self.movie_mapping["title"] == movie_title].index[0]
        print(movie_id)
        movie_data = self.data.loc[movie_id]

        # list to save all distances
        dists = []

        # compute start and end indices for this shard
        window_size = int(len(self.data) / length)
        start = window_size * index
        end = start + window_size if index < length - 1 else None

        # find euclidean distances for all movies in this shard
        for index, row in islice(self.data.iterrows(), start, end):
            # skip over input movie
            if (str(index) != str(movie_id)):
                dist = self._euclidean_distance(movie_data, row)
                dists.append((index, dist))

        # sort distances in ascending order
        dists.sort(key=lambda x: x[1])

        # trim to num_recs recommendations
        top_movies = dists[:num_recs]

        # convert to string data type for json
        for i in range(len(top_movies)):
            movie_id = str(top_movies[i][0])
            title = self.movie_mapping.loc[top_movies[i][0]]["title"]
            dist = str(top_movies[i][1])
            top_movies[i] = (movie_id, title, dist)

        # create payload
        payload = json.dumps(top_movies).encode('ascii')

        return aiocoap.Message(code=aiocoap.COMPUTED, payload=payload)


# logging setup

logging.basicConfig(level=logging.INFO)
logging.getLogger("coap-server").setLevel(logging.DEBUG)

async def setup(port):
    # set up address and port
    address = '127.0.0.1'
    port = int(port)

    # resource tree creation
    root = resource.Site()

    root.add_resource(['.well-known', 'core'],
            resource.WKCResource(root.get_resources_as_linkheader))
    root.add_resource(['knn'], KNNResource())

    protocol = await asyncio.Task(aiocoap.Context.create_server_context(root, bind=('127.0.0.1', port)))

    # create payload for parallelism entity registration
    payload = {"entity": 0, "address": address, "port": port}
    s_payload = json.dumps(payload).encode('ascii')
    uri = 'coap://127.0.0.1:5000/parallelism-entity'

    # add this worker to base parallelism entity (id 0)
    request = aiocoap.Message(code=aiocoap.PUT, payload=s_payload, uri=uri)

    try:
        response = await protocol.request(request).response
    except Exception as e:
        print('Failed to join parallelism entity')
    else:
        print('Result: %s\n%r'%(response.code, json.loads(response.payload.decode('ascii'))))

def main():
    if len(sys.argv) < 2:
        raise ValueError('Usage: ./server_knn_parallelism_worker [PORT]')

    # wait for parallelism entity registration to complete
    asyncio.get_event_loop().run_until_complete(setup(sys.argv[1]))

    # listen for parallelism requests from clients
    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    main()
