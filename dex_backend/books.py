# books.py

# Let's get this party started!
import falcon

book_list = ['Hello world!', 'Winnie']

# Falcon follows the REST architectural style, meaning (among
# other things) that you think in terms of resources and state
# transitions, which map to HTTP verbs.
class Book(object):
    def on_get(self, req, resp):
        """Handles GET requests"""
        resp.status = falcon.HTTP_200  # This is the default status
        resp.body = book_list[0]

# falcon.API instances are callable WSGI apps
app = falcon.API()

# Resources are represented by long-lived class instances
books = Book()

# things will handle all requests to the '/things' URL path
app.add_route('/books', books)
