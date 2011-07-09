 #!/usr/bin/env python

import os
from operator import itemgetter, attrgetter

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template


import gdata.youtube
import gdata.youtube.service


_DEBUG = True
yt_service = gdata.youtube.service.YouTubeService()


#Db models

class Video(db.Model):
      video_id = db.TextProperty(required=True)
      band = db.StringProperty(required=True)
      song = db.StringProperty(required=True)
      tags = db.StringListProperty()
      categories = db.StringListProperty()
      added = db.DateTimeProperty(auto_now_add=True)

#handlers

class SubmitCoverHandler(webapp.RequestHandler):
    def get(self):
	values = {}
        directory = os.path.dirname(__file__)
        path = os.path.join(directory, os.path.join('templates', 'submit_cover_video.html'))
        self.response.out.write(template.render(path, values, debug=_DEBUG))

class SubmitHandler(webapp.RequestHandler):
    def get(self):
	values = {}
        directory = os.path.dirname(__file__)
        path = os.path.join(directory, os.path.join('templates', 'submit_video.html'))
        self.response.out.write(template.render(path, values, debug=_DEBUG))

class SearchBandSongsHandler(webapp.RequestHandler):
    def get(self):
        #request params
	band = self.request.get('band_name')

        #query
        q = Video.all()
        q.filter("band =", band)
 	results = q.fetch(100)

        if results is not None:
 	   songs = unique_songs(results)

        #rendering values
        values = { 'songs': songs, 'band_name' : band}
        directory = os.path.dirname(__file__)
        path = os.path.join(directory, os.path.join('templates', 'band_songs_search.html'))
        self.response.out.write(template.render(path, values, debug=_DEBUG))

class SearchSongsVideosHandler(webapp.RequestHandler):
    def get(self):
	#utub data
        yt_service = gdata.youtube.service.YouTubeService()
        entries = []
        sorting = []
        videos = []

        #request params
	song_name = self.request.get('song_name')

        #query
        q = Video.all()
	q.filter('song =', song_name)
 	results = q.fetch(100)
        
        #sorting stuffs
        for video in results:
            entries.append(yt_service.GetYouTubeVideoEntry(video_id=video.video_id))

        #old algorithm
        '''for entry in entries:
            sorting.append((entry, float(entry.rating.average), int(entry.rating.num_raters)))
        sorted_entries = sorted(sorting, key=itemgetter(2))
        sorted_entries = sorted(sorting, key=itemgetter(1))'''
        #improved algorithm
        for entry in entries:
            sorting.append((entry, float(entry.rating.average) * int(entry.rating.num_raters)))
        sorted_entries = sorted(sorting, key=itemgetter(1))

        sorted_entries.reverse()

        #for entry, avg, num_raters in sorted_entries:#for old algorithm
        for entry, value in sorted_entries:#for improved algorithm
            videos.append(entry)

        #rendering values
        values = { 'entries' : videos, 'song_name' : song_name}
        directory = os.path.dirname(__file__)
        path = os.path.join(directory, os.path.join('templates', 'songs_video_search.html'))
        self.response.out.write(template.render(path, values, debug=_DEBUG))


#Listing

class ListBandsHandler(webapp.RequestHandler):
    def get(self):
        #query
        q = Video.all()
 	results = q.fetch(100)
        if results is not None:
 	   bands = unique_bands(results)
        bands.sort()
        #rendering values
        values = { 'bands' : bands }
        directory = os.path.dirname(__file__)
        path = os.path.join(directory, os.path.join('templates', 'list_bands.html'))
        self.response.out.write(template.render(path, values, debug=_DEBUG))

class ListSongsHandler(webapp.RequestHandler):
    def get(self):
        data = []
        counter = []
        #query
        q = Video.all()
 	results = q.fetch(100)
        if results is not None:
 	   songs = unique_songs(results)
        for d in results:
            counter.append(d.song)
        songs.sort()
        for song in songs:
            data.append([song,counter.count(song)])
        #rendering values
        values = { 'songs' : data}
        directory = os.path.dirname(__file__)
        path = os.path.join(directory, os.path.join('templates', 'list_songs.html'))
        self.response.out.write(template.render(path, values, debug=_DEBUG))


class SaveVidUrlHandler(webapp.RequestHandler):
    def get(self):
        url = self.request.get('video_url')
        vid_band = self.request.get('band_name')
        vid_song = self.request.get('song_name')
        vid_cats = []
	vid_tags = []

        if url.find('&') > 0:
           vid_id = url.split('&')[0].split('=')[1]
        else:
           vid_id = url.split('=')[1]

        entry = yt_service.GetYouTubeVideoEntry(video_id=vid_id)

	if entry is not None:
           if entry.media.keywords.text is not None:
              if entry.media.keywords.text.find(',') > 0:
                 vid_tags = entry.media.keywords.text.split(',')
              else:
                 vid_tags = entry.media.keywords.text
           for cat in entry.media.category:
	       vid_cats.append(cat.text)

        video = Video(video_id=vid_id, tags=vid_tags, categories=vid_cats, band=vid_band, song=vid_song)
        video.put()
        self.redirect('/submit')

class MainHandler(webapp.RequestHandler):
    def get(self):
	#utub data
        yt_service = gdata.youtube.service.YouTubeService()
        entries = []
        songs = []

        #query
        q = Video.all()
        q.order('-added')
        #   TODO: add ordering by last added vid
 	results = q.fetch(10)
        
        for video in results:
            entries.append(yt_service.GetYouTubeVideoEntry(video_id=video.video_id))
            songs.append(video.song)
        songs.reverse()
	values = { 'entries' : entries, 'results' : results, 'songs' : songs}
        directory = os.path.dirname(__file__)
        path = os.path.join(directory, os.path.join('templates', 'index.html'))
        self.response.out.write(template.render(path, values, debug=_DEBUG))

class TestHandler(webapp.RequestHandler):
    def get(self):
        yt_service = gdata.youtube.service.YouTubeService()
        entries = []
        entry1 = yt_service.GetYouTubeVideoEntry(video_id='CCbpoHBa10o')
        entry2 = yt_service.GetYouTubeVideoEntry(video_id='2WHEgRdPc3c')
        entry3 = yt_service.GetYouTubeVideoEntry(video_id='WfEhJLhtiic')
        entries.append(entry1)
        entries.append(entry2)
        entries.append(entry3)

	values = { 'entries' : entries}
        directory = os.path.dirname(__file__)
        path = os.path.join(directory, os.path.join('templates', 'test.html'))
        self.response.out.write(template.render(path, values, debug=_DEBUG))


#custom functions
def unique_songs(song_list):
    unique_results = []
    for obj in song_list:
        if obj.song not in unique_results:
            unique_results.append(obj.song)
    return unique_results

def unique_bands(band_list):
    unique_results = []
    for obj in band_list:
        if obj.band not in unique_results:
            unique_results.append(obj.band)
    return unique_results

def main():
    application = webapp.WSGIApplication([
       ('/', MainHandler),
       ('/test', TestHandler),
       ('/submitcover', SubmitCoverHandler),
       ('/submit', SubmitHandler),
       ('/search', SearchBandSongsHandler),
       ('/songsvids',SearchSongsVideosHandler),
       ('/songs',ListSongsHandler),       
       ('/bands',ListBandsHandler),
       ('/save', SaveVidUrlHandler)],debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
