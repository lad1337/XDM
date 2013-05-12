
from lib import requests
import hashlib

#-------------------------------------------------------------------------------
# String Constants
baseURL = "http://api.trakt.tv/"
movieWatchlistURL = baseURL + "user/watchlist/movies.json/"
unwatchlistMovieURL = baseURL + "movie/unwatchlist.json/"


#-------------------------------------------------------------------------------
# SHA1 hash
def hash(value):
    m = hashlib.sha1()
    m.update(value)
    return m.hexdigest()


#-------------------------------------------------------------------------------
# construct the url
def makeURL(url, apiKey, username):
    result = url + apiKey
    if username != "":
        result += "/" + username
    return result


#-------------------------------------------------------------------------------
# get the movie watchlist
def movieWatchlist(username, password, apiKey):
    url = makeURL(movieWatchlistURL, apiKey, username)

    r = requests.get(url, auth=(username, hash(password)))
    print r.url
    movies = r.json()
    return movies


#-------------------------------------------------------------------------------
def removeMovieFromWatchlist(username, password, apiKey, title, year, imdb_id):
    url = makeURL(unwatchlistMovieURL, apiKey, "")
    
    postdata = {
                    'movies':   [{ 'title': title,
                                    'year': year,
                                    'imdb_id': imdb_id
                                }]
                }
    
    r = requests.get(url, params=postdata, auth=(username, hash(password)))
   

#-------------------------------------------------------------------------------
