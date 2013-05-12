
from xdm.plugins import *
from lib import requests
import hashlib
import json


baseURL = "http://api.trakt.tv/"
movieWatchlistURL = baseURL + "user/watchlist/movies.json/"
unwatchlistMovieURL = baseURL + "movie/unwatchlist.json/"


class TraktWatchlist(MediaAdder):
    version = "0.1"
    addMediaTypeOptions = 'runFor'
    screenName = 'Trakt Wachlist'
    _config = {'username': '',
               'password': '',
               'apikey': '',
               'remove_movies': True}
    config_meta = {'plugin_desc': 'Add movies from your http://trakt.tv account. Get your apikey at http://trakt.tv/settings/api',
                   'remove_movies': {'human': 'Remove movies after a successful add'}}

    types = ['de.lad1337.movies']

    def __init__(self, instance='Default'):
        MediaAdder.__init__(self, instance=instance)

    def runShedule(self):
        if not (self.c.username or self.c.password or self.c.apikey):
            return []
        movies = self._getMovieWatchlist(self.c.username, self.c.password, self.c.apikey)
        out = []
        for movie in movies:
            additionalData = {}
            additionalData['tmdb_id'] = movie['tmdb_id']
            additionalData['imdb_id'] = movie['imdb_id']
            out.append(self.Media('de.lad1337.movies',
                                  movie['tmdb_id'],
                                  'tmdb',
                                  'Movie',
                                  movie['title'],
                                  additionalData=additionalData))
        return out

    def successfulAdd(self, mediaList):
        """media list is a list off all the stuff to remove
        with the same objs that where returned in runShedule() """
        if self.c.remove_movies and len(mediaList):
            return self._removeMovieFromWatchlist(self.c.username, self.c.password, self.c.apikey, mediaList)
        return True

    # get the movie watchlist
    def _getMovieWatchlist(self, username, password, apikey):
        url = self._makeURL(movieWatchlistURL, apikey, username)
        r = requests.get(url, auth=(username, self._hash(password)))
        return r.json()

    def _removeMovieFromWatchlist(self, username, password, apikey, movieList):
        url = self._makeURL(unwatchlistMovieURL, apikey, "")
        traktMovieList = []
        for movie in movieList:
            traktMovieList.append({'tmdb_id': movie.additionalData['tmdb_id'],
                                   'imdb_id': movie.additionalData['imdb_id']
                                   })
        log.info('Removing movies from trakt watch list %s' % movieList)
        postdata = {'movies': traktMovieList,
                    'username': username,
                    'password': self._hash(password)}

        r = requests.post(url, data=json.dumps(postdata))
        try:
            return r.json()['status'] == 'success'
        except ValueError:
            return False

    # construct the url
    def _makeURL(self, url, apiKey, username):
        result = url + apiKey
        if username != "":
            result += "/" + username
        return result

    # SHA1 hash
    def _hash(self, value):
        m = hashlib.sha1()
        m.update(value)
        return m.hexdigest()