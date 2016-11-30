#!/usr/bin/python
'''track classes'''
from __future__ import absolute_import, print_function


class ITunesTrack(object):
    """Representation of an iTunes library music track."""

    def __init__(self, id, name, artist, album, year, genre):
        """Create a base music track.

        Sets the id, name, artist, album, year, and genre as given.
        Sets album_artist to artist, rating to None, and plays to 0.
    
        Args:
            id (str): unique track id
            name (str): track name
            artist (str): track artist
            album (str): track album
            year (str): track year
            genre (str): track genre

        """
        self.id = int(id)
        self.name = name.encode('utf-8')
        self.artist = artist.encode('utf-8')
        self.album = album.encode('utf-8')
        self.year = int(year)
        self.genre = genre.encode('utf-8')

        self.album_artist = artist.encode('utf-8')
        self.rating = None
        self.plays = 0

    def set_album_artist(self, album_artist):
        """Set the track album artist if given a truthy value.

        Args:
            album_artist (str): track album artist
        """
        if album_artist:
            self.album_artist = album_artist.encode('utf-8')

    def set_rating(self, rating=None):
        """Set the track rating if given a truthy value.

        Args:
            rating (str): track rating, defaults to None
        """
        self.rating = int(rating) if rating is not None else None

    def set_plays(self, plays=0):
        """Set the track play count.

        Args:
            plays (str): track play count, defualts to 0
        """
        self.plays = int(plays)

    def get_identifier(self):
        """Retrieves a track identifier in the form of concatenated name, artist, year.

        Intended to be used for identifying duplicate tracks.

        Returns:
            concatenated string of track name, artist, year
        """
        return '{name}_{artist}_{year}'.format(name=self.name, artist=self.artist, year=self.year)

    def print_verbose(self):
        """Creates a verbose string representation.
        
        Returns:
            a verbose string representation of the track attributes
        """
        rstr = 'Track ID:\t{id}\n'.format(id=self.id)
        rstr += 'Name:\t\t{name}\n'.format(name=self.name)
        rstr += 'Artist:\t\t{artist}\n'.format(artist=self.artist)
        rstr += 'Album Artist:\t{album_artist}\n'.format(album_artist=self.album_artist)
        rstr += 'Album:\t\t{album}\n'.format(album=self.album)
        rstr += 'Year:\t\t{year}\n'.format(year=self.year)
        rstr += 'Genre:\t\t{genre}\n'.format(genre=self.genre)
        rstr += 'Rating:\t\t{rating}\n'.format(rating=self.rating)
        rstr += 'Play Count:\t{plays}\n'.format(plays=self.plays)

        return rstr

    def __repr__(self):
        rstr = ('({id},{name},{artist},{album_artist},{album},{year},{genre},{rating},{plays})'
                .format(id=self.id, name=self.name, artist=self.artist,
                        album_artist=self.album_artist, album=self.album, year=self.year,
                        genre=self.genre, rating=self.rating, plays=self.plays))
        return rstr
