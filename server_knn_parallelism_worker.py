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
    """Example resource which supports the GET and PUT methods. It sends large
    responses, which trigger blockwise transfer."""

    def __init__(self):
        super().__init__()
        self._load_movie_data()

    def _load_movie_data(self):
        # import movie data
        movie_data = pd.read_csv("data/movies.csv",
            usecols=['movieId', 'title'],
            dtype={'movieId': 'int32', 'title': 'str'})

        # import corresponding ratings
        rating_data = pd.read_csv("data/ratings.csv",
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

        # create movie vs user matrix for kNN computations
        self.data = ratings_drop_movies_users.pivot(index='movieId', columns='userId', values='rating').fillna(0)
        self.movie_mapping = movie_data

    def _euclidean_distance(self, x, y):
        return np.linalg.norm(x - y)

    async def render_parallelize(self, request):
        payload = json.loads(request.payload.decode('ascii'))
        num_recs = int(payload["num_recs"])
        movie_title = payload["movie_title"]
        index = int(payload["index"])
        length = int(payload["length"])
        print('PARALLELIZE payload: %s' % payload)

        # get movie_id
        movie_id = self.movie_mapping[self.movie_mapping["title"] == movie_title]["movieId"].values[0]
        movie_data = self.data.loc[movie_id]

        # list to save all distances
        dists = []

        # compute start and end indices
        window_size = int(len(self.data) / length)
        start = window_size * index
        end = start + window_size if index < length - 1 else None
        print(len(self.data), start, end, window_size, length)

        for index, row in islice(self.data.iterrows(), start, end):
            if (str(index) != str(movie_id)):
                dist = self._euclidean_distance(movie_data, row)
                dists.append((index, dist))

        # sort distances in ascending order
        print("DIST: ", len(dists))
        dists.sort(key=lambda x: x[1])

        # trim to num_recs recommendations and drop first
        top_movies = dists[:num_recs]

        # convert to string data type for json
        for i in range(len(top_movies)):
            movie_id = str(top_movies[i][0])
            title = self.movie_mapping[self.movie_mapping["movieId"] == int(movie_id)]["title"].values[0]
            dist = str(top_movies[i][1])
            top_movies[i] = (movie_id, title, dist)

        # create payload
        payload = json.dumps(top_movies).encode('ascii')

        # time.sleep(1)
        return aiocoap.Message(code=aiocoap.COMPUTED, payload=payload)


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
