#!/usr/bin/python
'''track classes'''
from __future__ import absolute_import, print_function

import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Library Objects')

UNKNOWN_GENRE = 0

VARIOUS_THRESHOLD = 3
VARIOUS = 'Various Artists'

SUB_FEAT_PAT = re.compile('\s*\(feat\.(?P<artist>.*)\)\s*')
FEAT_PATTERN = re.compile('.*\(feat\.(?P<artist>.*)\)\s*')
MULT_PATTERN = re.compile('\s*[,&]\s*')

ALBUM_NAME_PATTERN = re.compile('\s*((\-\s*(Single|EP))|(\(.*Deluxe.*\))|(\[.*Deluxe.*\]))\s*')

# TODO: WILL NEED TO CONVERT GENRES TO BINARY LATER

class ITunesLibrary(object):
    """A representation of an ITunes Library"""

    def __init__(self):
        """Initializes an empty ITunes Library."""
        self.albums = {}
        self.tracks = {}
        self.artists = {}
        self._genre_map = {None: UNKNOWN_GENRE}

    def add_artist(self, artist):
        """Add an artist to this library.

        Args:
            artist (Artist): an ITunes artist
        """
        self.artists[artist.name] = artist

    def add_album(self, album_key, album):
        """Add an album to this library.

        Args:
            album_key (tuple): album identifier of name, year
            album (Album): an ITunes album
        """
        self.albums[album_key] = album

    def add_track(self, track):
        """Add a track to this library.

        Args:
            track (ITunesTrack): an ITunes track
        """
        self.tracks[track.id] = track

    def get_genre_key(self, genre):
        """Retrieve the genre key, adding it if there is none.

        Args:
            genre (str): genre string to be translated to an enum key

        Returns:
            an int representing the genre in the library
        """
        if genre in self._genre_map:
            return self._genre_map[genre]
        else:
            genre_value = len(self._genre_map)
            self._genre_map[genre] = genre_value
            return genre_value

    def get_genre_map(self):
        """Retrieve the map of genre names to enums.

        Returns:
            a dict of genre name to enum key (int)
        """
        return self._genre_map

    def remove_duplicates(self):
        """Merge duplicate tracks into one and remove extraneous.

        Updated track will have sum of play counts and average of ratings.
        """
        identifier_to_index = {}
        duplicate_identifiers = set()
        removable = []
        removed_track_count = 0
        removed_album_count = 0
        removed_artist_count = 0

        for track_id, track in self.tracks.iteritems():
            track_ident = track.get_track_identifier()
            if track_ident in identifier_to_index:
                duplicate_identifiers.add(track_ident)
                identifier_to_index[track_ident].append(track_id)
                removable.append(track_id)
            else:
                identifier_to_index[track_ident] = [track_id]

        for duplicate_identifier in duplicate_identifiers:
            logger.info('Identified duplicate track {dup}.'.format(dup=duplicate_identifier))
            duplicate_indexes = identifier_to_index[duplicate_identifier]
            duplicate_tracks = [self.tracks[track_id] for track_id in duplicate_indexes]
            plays = 0
            sum_rating = 0
            dup_count = 0.
            for track in duplicate_tracks:
                plays += track.plays
                if track.rating is not None:
                    sum_rating += track.rating
                    dup_count += 1

            rating = sum_rating / dup_count if dup_count else None

            # merge sum play counts and avg rating onto the first track and we'll
            # remove the rest
            merged_track = duplicate_tracks[0]
            merged_track.set_plays(plays)
            merged_track.set_rating(rating)

        # remove the tracks whose info we merged
        removable.reverse()
        for i in removable:
            track = self.tracks[i]
            track_id = track.id
            album_id = track.album_id
            del self.tracks[i]
            removed_track_count += 1

            album = self.albums[album_id]
            album.tracks.remove(track.id)
            if not album.tracks:
                for artist_name in album.artists:
                    albums = self.artists[artist_name].albums
                    albums.remove(album_id)
                    removed_album_count += 1

                    if not albums:
                        del self.artists[artist_name]
                        removed_artist_count += 1
                    

        if removed_track_count > 0:
            logger.info(('Removed {lost_track} duplicate tracks, which resulted in removing ' +
                         '{lost_album} albums and {lost_artist} artists. {kept_track} tracks, ' +
                         '{kept_album} albums, and {kept_artist} artists remain.')
                         .format(lost_track=removed_track_count,
                                 lost_album=removed_album_count,
                                 lost_artist=removed_artist_count,
                                 kept_track=len(self.tracks),
                                 kept_album=len(self.albums),
                                 kept_artist=len(self.artists)))


class Artist(object):
    """A representation of an artist."""

    def __init__(self, name):
        """Initialize an artist by name.
        
        Args:
            name (str): artist name
        """
        self.name = name
        self.genres = set()
        self.album_ids = set()

    def add_album(self, album_id):
        """Associate an album with this artist.

        Args:
            album_id (tuple): album id
        """
        self.album_ids.add(album_id)

    def add_genre(self, genre):
        """Associate a genre with this artist.

        Args:
            genre (int): genre key
        """
        self.genres.add(genre)

    def __repr__(self):
        return ('({name},{genres},{albums})'
                .format(name=self.name, genres=self.genres, albums=self.album_ids))


class Album(object):
    """A collection of tracks in an album."""

    def __init__(self, name, year):
        """Create a music album with no tracks.

        Args:
            name (str): album name
            year (int): album year
        """
        self.name = name
        self.year = year

        self.tracks = set()

    def add_track(self, track_id):
        """Add a track_id to the music album

        Args:
            track_id (int): iTunes track id from library XML
        """
        self.tracks.add(track_id)

    @staticmethod
    def get_album_name(name):
        """Strip extraneous info from album name.

        This includes:
            - Strip " - Single" suffix
            - Strip " - EP" suffix
            - Strip any parenthetical suffixes containing "Deluxe"

        Args:
            name (str): album name

        Returns:
            the album name with extraneous info removed
        """
        name = name.strip().encode('utf-8')
        return re.sub(ALBUM_NAME_PATTERN, '', name)

    def __repr__(self):
        return ('({name},{year},{track_count})'
                .format(name=self.name, year=self.year, track_count=len(self.tracks)))

class Track(object):
    """Abstract representation of a track."""

    def __init__(self, id, name, artists, genre=UNKNOWN_GENRE,
            track_number=None, rating=None, plays=0):
        """Base track representation.

        Args:
            id (int): track id
            name (str): track name
            artists (list[str]): track artists
            genre (str): track genre, defaults to UNKNOWN_GENRE
            track_number (int): track number, defaults to None
            rating (float): track rating, defaults to None
            plays (int): track play count, defaults to 0
        """
        self.id = id
        self.name = name
        self.artists = artists
        self.genre = genre
        self.track_number = track_number
        self.rating = rating
        self.plays = plays
        self.album_id = None

    def set_genre(self, genre=UNKNOWN_GENRE):
        """Set the track genre.

        Args:
            genre (int): track genre, defaults to UNKNOWN_GENRE
        """
        self.genre = genre

    def set_rating(self, rating=None):
        """Set the track rating if given a truthy value.

        Args:
            rating (str): track rating, defaults to None
        """
        self.rating = int(rating) if rating is not None else None

    def set_plays(self, plays=0):
        """Set the track play count.

        Args:
            plays (str): track play count, defaults to 0
        """
        self.plays = int(plays)

    def set_track_number(self, track_number=None):
        """Set the track number.

        Args:
            track_number (int): track number, defaults to None
        """
        self.track_number = int(track_number) if track_number is not None else None

    def set_album_id(self, album_id):
        """Set the album id.

        Args:
            album_id (tuple): unique album identifier
        """
        self.album_id = album_id

    def get_track_identifier(self):
        """Retrieves a track identifier in the form of its name and artists.

        Intended to be used for identifying duplicate tracks within the same album.

        Returns:
            tuple of track name, artists
        """
        return (self.name, ','.join(self.artists))


class ITunesTrack(Track):
    """Representation of an iTunes library music track."""

    def __init__(self, id, name, artists):
        """Create a base music track.

        Sets the id, name, and artist as given.
        If there are multiple or featured artists they will be combined in a set.
        Defaults rating to None and plays to 0.

        Args:
            id (str): unique track id
            name (str): track name
            artists (str): track artists

        """
        feat_artists = FEAT_PATTERN.match(name)
        name = SUB_FEAT_PAT.sub('', name)
        artists = re.split(MULT_PATTERN, artists)

        self.main_artist = artists[0]
        artists = set(artists)

        if feat_artists:
            feat_artists = re.split(MULT_PATTERN, feat_artists.group('artist').strip())
            artists.update(feat_artists)

        super(ITunesTrack, self).__init__(int(id), name, list(artists))

    def print_verbose(self):
        """Creates a verbose string representation.
        
        Returns:
            a verbose string representation of the track attributes
        """
        rstr = 'Track ID:\t{id}\n'.format(id=self.id)
        rstr += 'Name:\t\t{name}\n'.format(name=self.name)
        rstr += 'Artists:\t\t{artist}\n'.format(artist=','.join(self.artists))
        rstr += 'Genre:\t\t{genre}\n'.format(genre=self.genre)
        rstr += 'Track Number:\t{track_number}\n'.format(track_number=self.track_number)
        rstr += 'Rating:\t\t{rating}\n'.format(rating=self.rating)
        rstr += 'Play Count:\t{plays}\n'.format(plays=self.plays)

        return rstr

    def __repr__(self):
        rstr = ('({id},{name},({artists}),{track_number},{genre},{rating},{plays})'
                .format(id=self.id, name=self.name, artists=','.join(self.artists),
                        track_number=self.track_number, genre=self.genre,
                        rating=self.rating, plays=self.plays))
        return rstr
