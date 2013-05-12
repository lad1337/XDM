from xdm.plugins import *
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
        # me is the object !!
        # each field can be accesed directly
        # special stiff like {{actions}} will be explained defined later
        # {{image}} will return the field value
        # {{this.image}} will return the local src
        # {{this.getField('image')}} will return the image obj. str(Image) is the local src
        return """
        <div class="movie pull-left {{statusCssClass}}">
            <i class="icon-thumbs-up"></i>
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
                    {{actionButtons}}<br/>
                    {{infoButtons}}
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
                {%endif%}
                <a href="#" class="btn btn-mini btn-info overview" data-placement="bottom" data-toggle="popover" title="Overview for {{this.getName()}}" data-content="{{overview}}" data-container=".de-lad1337-movies">Overview</a>
                {{statusSelect}}
            </div>
        
            <span class="v-name">{{this.name}}</span>
            <!--
            <img src="{{this.poster_image}}" class="pull-left"/>
            <div class="content well">
                {{statusSelect}}
                <p class="overview">
                {{this.overview}}
                </p>
                {%if this.getField('tailer_count')%}
                {% for trailerIndex in range(this.getField('tailer_count'))%}
                    <a href="http://youtube.com/watch?v={{this.getField('youtube_trailer_id_'~trailerIndex)}}" class="trailer">
                        <i class="icon-film"></i>
                        {{this.getField('youtube_trailer_name_'~trailerIndex)}}
                    </a>
                {% endfor %}
                {%endif%}
                <div class="actions-container">{{actionButtons}}{{infoButtons}}</div>
            </div>
            -->
        </div>
        """

    def getSearchTerms(self):
        return [self.getName()]

    def getName(self):
        return '%s (%s)' % (self.name, self.year)


class Movies(MediaTypeManager):
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
        <link rel="stylesheet" href="/Movies/style.css">
        <script src="/Movies/script.js"></script>
        """


class Tmdb(Provider):
    version = "0.11"
    _tag = 'tmdb'
    screenName = 'TheMovieDB'
    single = True
    types = ['de.lad1337.movies']
    _config = {'enabled': True}

    def __init__(self, instance='Default'):
        tmdb.configure('5c235bb1b487932ebf0a9935c8b39b0a')
        Provider.__init__(self, instance=instance)

    def searchForElement(self, term=''):
        self.progress.reset()
        mediaType = MediaType.get(MediaType.identifier == 'de.lad1337.movies')
        mtm = common.PM.getMediaTypeManager('de.lad1337.movies')
        fakeRoot = mtm.getFakeRoot(term)

        movies = tmdb.Movies(term, limit=True)

        self.progress.total = movies.get_total_results()
        for tmdbMovie in movies:
            self.progress.addItem()
            self._createMovie(fakeRoot, mediaType, tmdbMovie)

        return fakeRoot

    def _createMovie(self, fakeRoot, mediaType, tmdbMovie):
        movie = Element()
        movie.mediaType = mediaType
        movie.parent = fakeRoot
        movie.type = 'Movie'
        movie.setField('name', tmdbMovie.get_title(), self.tag)
        rl_date = tmdbMovie.get_release_date()
        movie.setField('release_date', tmdbMovie.get_release_date(), self.tag)
        if len(rl_date.split('-')) > 1:
            movie.setField('year', rl_date.split('-')[0], self.tag)
        else:
            movie.setField('year', 0, self.tag)
        movie.setField('poster_image', tmdbMovie.get_poster(), self.tag)
        movie.setField('overview', tmdbMovie.get_overview(), self.tag)
        movie.setField('runtime', tmdbMovie.get_runtime(), self.tag)
        movie.setField('id', tmdbMovie.get_id(), self.tag)
        movie.setField('id', tmdbMovie.get_imdb_id(), 'imdb')
        index = 0
        for index, youtubeTrailer in enumerate(tmdbMovie.get_trailers()['youtube']):

            print youtubeTrailer['source']
            trailerIDFieldName = 'youtube_trailer_id_%s' % index
            trailerNameFieldName = 'youtube_trailer_name_%s' % index
            movie.setField(trailerIDFieldName, youtubeTrailer['source'], self.tag)
            movie.setField(trailerNameFieldName, youtubeTrailer['name'], self.tag)

        movie.setField('tailer_count', index + 1, self.tag)
        movie.saveTemp()

    def getElement(self, id):
        mediaType = MediaType.get(MediaType.identifier == 'de.lad1337.movies')
        mtm = common.PM.getMediaTypeManager('de.lad1337.movies')
        fakeRoot = mtm.getFakeRoot('tmdb ID: %s' % id)
        tmdbMovie = tmdb.Movie(id)
        self._createMovie(fakeRoot, mediaType, tmdbMovie)

        for ele in fakeRoot.decendants:
            print ele, ele.getField('id', self.tag)
            if ele.getField('id', self.tag) == id:
                return ele
        else:
            return False





