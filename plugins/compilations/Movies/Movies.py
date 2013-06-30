# Author: Dennis Lutter <lad1337@gmail.com>
# URL: https://github.com/lad1337/XDM
#
# This file is part of XDM: eXtentable Download Manager.
#
#XDM: eXtentable Download Manager. Plugin based media collection manager.
#Copyright (C) 2013  Dennis Lutter
#
#XDM is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#XDM is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see http://www.gnu.org/licenses/.

from xdm.plugins import *
from lib.dateutil.parser import *
import tmdb


class Movie(object):
    name = ''
    genres = ''
    year = ''
    release_date = ''
    overview = ''
    runtime = ''
    poster_image = ''

    _orderBy = 'name'

    def getTemplate(self):
        # this is this object !!
        # each field can be accesed directly
        # special stiff like {{actions}} will be explained defined later
        # {{image}} will return the field value
        # {{this.image}} will return the local src
        # {{this.getField('image')}} will return the image obj. str(Image) is the local src
        return """
        <div class="movie pull-left {{statusCssClass}}">
            <i class="icon-thumbs-up"></i>
            <i class="icon-download-alt"></i>
            <div class="door door-left">
                <img src="{{this.poster_image}}"/>
            </div>
            <div class="door door-right">
                <img src="{{this.poster_image}}"/>
            </div>
            <div class="inner">
                <h4>{{this.getName()}}</h4>
                <i class="icon-remove btn btn-mini"></i>
                <div class="buttons">
                    {{actionButtonsIcons}}
                    {{infoButtonsIcons}}
                    <div class="progressbar-container">
                        {{downloadProgressBar}}
                    </div>
                </div>
                {%if this.getField('tailer_count')%}
                <ul>
                {% for trailerIndex in range(this.getField('tailer_count'))%}
                    <li><a href="http://youtube.com/watch?v={{this.getField('youtube_trailer_id_'~trailerIndex)}}" class="trailer">
                        <i class="icon-film"></i>
                        {{this.getField('youtube_trailer_name_'~trailerIndex)}}
                    </a></li>
                {% endfor %}
                </ul>
                <span style="color:#fff;display:block;">{{released}}</span>
                {%endif%}
                {{statusSelect}}
                <a href="#" class="btn btn-mini btn-info pull-right overview" data-placement="bottom" data-toggle="popover" title="Overview for {{this.getName()}}" data-content="{{overview}}" data-container=".de-lad1337-movies">Overview</a>
            </div>
        </div>
        """

    def getSearchTerms(self):
        return [self.getName()]

    def getName(self):
        return '%s (%s)' % (self.name, self.year)

    def getReleaseDate(self):
        return self.release_date


class Movies(MediaTypeManager):
    version = "0.2"
    _config = {'enabled': True}
    config_meta = {'plugin_desc': 'Movies'}
    order = (Movie,)
    download = Movie
    # a unique identifier for this mediatype
    identifier = 'de.lad1337.movies'
    addConfig = {}
    addConfig[Indexer] = [{'type':'category', 'default': None, 'prefix': 'Category for', 'sufix': 'Movies'}]
    addConfig[Downloader] = [{'type':'category', 'default': None, 'prefix': 'Category for', 'sufix': 'Movies'}]

    def makeReal(self, movie):
        movie.parent = self.root
        movie.status = common.getStatusByID(self.c.default_new_status_select)
        movie.save()
        movie.downloadImages()
        return True

    def headInject(self):
        return """
        <link rel="stylesheet" href="{{webRoot}}/Movies/style.css">
        <script src="{{webRoot}}/Movies/script.js"></script>
        """


class Tmdb(Provider):
    version = "0.12"
    _tag = 'tmdb'
    screenName = 'TheMovieDB'
    single = True
    types = ['de.lad1337.movies']
    _config = {'enabled': True,
               'img_size_select': 'm'}

    def __init__(self, instance='Default'):
        tmdb.configure('5c235bb1b487932ebf0a9935c8b39b0a')
        Provider.__init__(self, instance=instance)

    @profileMeMaybe
    def searchForElement(self, term=''):
        self.progress.reset()
        mediaType = MediaType.get(MediaType.identifier == 'de.lad1337.movies')
        mtm = common.PM.getMediaTypeManager('de.lad1337.movies')[0]
        fakeRoot = mtm.getFakeRoot(term)

        movies = tmdb.Movies(term, limit=True)

        self.progress.total = movies.get_total_results()
        for tmdbMovie in movies:
            self.progress.addItem()
            self._createMovie(fakeRoot, mediaType, tmdbMovie)

        return fakeRoot

    def _img_size_select(self):
        return {'o': 'Orginal size (slow web page)',
                'l': 'Large 500px wide',
                'm': 'Medium 185px wide',
                's': 'Small 92px wide'}

    def _createMovie(self, fakeRoot, mediaType, tmdbMovie):
        movie = Element()
        movie.mediaType = mediaType
        movie.parent = fakeRoot
        movie.type = 'Movie'
        movie.setField('name', tmdbMovie.get_title(), self.tag)
        rl_date = tmdbMovie.get_release_date()
        if len(rl_date.split('-')) > 1:
            movie.setField('year', rl_date.split('-')[0], self.tag)
        else:
            movie.setField('year', 0, self.tag)
        movie.setField('poster_image', tmdbMovie.get_poster(img_size=self.c.img_size_select), self.tag)
        movie.setField('backdrop_image', tmdbMovie.get_backdrop('s'), self.tag)
        movie.setField('overview', tmdbMovie.get_overview(), self.tag)
        movie.setField('runtime', tmdbMovie.get_runtime(), self.tag)
        movie.setField('id', tmdbMovie.get_id(), self.tag)
        movie.setField('id', tmdbMovie.get_imdb_id(), 'imdb')
        releaseDate = tmdbMovie.get_release_date()
        releaseDateTime = parse(releaseDate)

        movie.setField('release_date', releaseDateTime, self.tag)
        index = 0
        for index, youtubeTrailer in enumerate(tmdbMovie.get_trailers()['youtube']):
            trailerIDFieldName = 'youtube_trailer_id_%s' % index
            trailerNameFieldName = 'youtube_trailer_name_%s' % index
            movie.setField(trailerIDFieldName, youtubeTrailer['source'], self.tag)
            movie.setField(trailerNameFieldName, youtubeTrailer['name'], self.tag)

        movie.setField('tailer_count', index + 1, self.tag)
        movie.saveTemp()

    def getElement(self, id, element=None):
        """we like tmdb ids"""
        mediaType = MediaType.get(MediaType.identifier == 'de.lad1337.movies')
        mtm = common.PM.getMediaTypeManager('de.lad1337.movies')[0]
        fakeRoot = mtm.getFakeRoot('tmdb ID: %s' % id)
        tmdbMovie = tmdb.Movie(id)
        self._createMovie(fakeRoot, mediaType, tmdbMovie)

        for ele in fakeRoot.decendants:
            #print ele, ele.getField('id', self.tag)
            if str(ele.getField('id', self.tag)) == str(id):
                return ele
        else:
            return False





