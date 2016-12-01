#!/usr/bin/python
'''track classes'''
from __future__ import absolute_import, print_function

import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Library Objects')

SUB_FEAT_PAT = re.compile('\s*\(feat\.(?P<artist>.*)\)\s*')
FEAT_PATTERN = re.compile('.*\(feat\.(?P<artist>.*)\)\s*')
MULT_PATTERN = re.compile('\s*[,&]\s*')

ALBUM_NAME_PATTERN = re.compile('\s*((\-\s*(Single|EP))|(\(.*\))|(\[.*\]))\s*')



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

        self.tracks = []
        self.artists = set()

    def add_track(self, track):
        """Add a track to the music album, updating album artists as necessary.

        Args:
            track (ITunesTrack): iTunes track from library XML
        """
        self.tracks.append(track)
        self.artists.update(track.artists)

    def merge_duplicates(self):
        """Merge duplicate tracks into one and remove extraneous.

        Updated track will have sum of play counts and average of ratings.
        """
        identifier_to_index = {}
        duplicate_identifiers = set()
        removable = []
        removed_count = 0

        for i, track in enumerate(self.tracks):
            track_id = track.get_track_identifier()
            if track_id in identifier_to_index:
                duplicate_identifiers.add(track_id)
                identifier_to_index[track_id].append(i)
                removable.append(i)
            else:
                identifier_to_index[track_id] = [i]

        for duplicate_identifier in duplicate_identifiers:
            logger.info('Identified duplicate track {dup}.'.format(dup=duplicate_identifier))
            duplicate_indexes = identifier_to_index[duplicate_identifier]
            duplicate_tracks = [self.tracks[i] for i in duplicate_indexes]
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
            del self.tracks[i]
            removed_count += 1

        if removed_count > 0:
            logger.info(('Removed {removed} duplicate tracks from album {album}.' +
                         ' {remained} tracks remain.')
                         .format(removed=removed_count,
                                 album=self.name,
                                 remained=len(self.tracks)))
    @staticmethod
    def get_album_name(name):
        """Strip extraneous info from album name.

        This includes:
            - Strip " - Single" suffix
            - Strip " - EP" suffix
            - Strip any parenthetical suffixes

        Args:
            name (str): album name

        Returns:
            the album name with extraneous info removed
        """
        name = name.strip().encode('utf-8')
        return re.sub(ALBUM_NAME_PATTERN, '', name)

    def __repr__(self):
        return ('({name},{artists},{year},{track_count})'
                .format(name=self.name, artists=self.artists, year=self.year,
                        track_count=len(self.tracks)))

class Track(object):
    """Abstract representation of a track."""

    def __init__(self, id, name, artists, genre='', rating=None, plays=0):
        """Base track representation.

        Args:
            id (int): track id
            name (str): track name
            artists (list[str]): track artists
            genre (str): track genre, defaults to ''
            rating (float): track rating, defaults to None
            plays (int): track play count, defaults to 0
        """
        self.id = id
        self.name = name
        self.artists = artists
        self.genre = genre
        self.rating = rating
        self.plays = plays


    def set_genre(self, genre=''):
        """Set the track genre if given a truthy value.

        Args:
            genre (str): track genre, defaults to ''
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
        artists = set(re.split(MULT_PATTERN, artists))

        if feat_artists:
            feat_artists = re.split(MULT_PATTERN, feat_artists.group('artist').strip())
            artists.update(feat_artists)

        super(ITunesTrack, self).__init__(int(id), name, artists, None, 0)

    def print_verbose(self):
        """Creates a verbose string representation.
        
        Returns:
            a verbose string representation of the track attributes
        """
        rstr = 'Track ID:\t{id}\n'.format(id=self.id)
        rstr += 'Name:\t\t{name}\n'.format(name=self.name)
        rstr += 'Artists:\t\t{artist}\n'.format(artist=','.join(self.artists))
        rstr += 'Genre:\t\t{genre}\n'.format(genre=self.genre)
        rstr += 'Rating:\t\t{rating}\n'.format(rating=self.rating)
        rstr += 'Play Count:\t{plays}\n'.format(plays=self.plays)

        return rstr

    def __repr__(self):
        rstr = ('({id},{name},({artists}),{genre},{rating},{plays})'
                .format(id=self.id, name=self.name, artists=','.join(self.artists),
                        genre=self.genre, rating=self.rating, plays=self.plays))
        return rstr
