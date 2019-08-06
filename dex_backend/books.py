# books.py

# Let's get this party started!
import falcon
import json
import uuid
import mimetypes

book_list = ['Hello world!', 'Winnie']

# Falcon follows the REST architectural style, meaning (among
# other things) that you think in terms of resources and state
# transitions, which map to HTTP verbs.
class Book(object):
    _CHUNK_SIZE_BYTES = 4096


    def on_get(self, req, resp):
        """Handles GET requests"""
        # print(req.query_string)
        print(req.path)
        resp.status = falcon.HTTP_200  # This is the default status
        resp.body = book_list[0]

    #     TODO: Find how to get path param


    def on_post(self, req, resp):
        data = json.loads(req.stream.read().decode('utf-8'))
        print(data["doc"])
        book_list.append(data["doc"])
        resp.status = falcon.HTTP_201

# falcon.API instances are callable WSGI apps
app = falcon.API()

# Resources are represented by long-lived class instances
books = Book()

# things will handle all requests to the '/things' URL path
app.add_route('/books', books)
# app.add_route('/books/{id}', books)
