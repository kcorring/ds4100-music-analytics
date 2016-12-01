#!/usr/bin/python
'''track classes'''
from __future__ import absolute_import, print_function

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Library Objects')


class Album(object):
    """A collection of tracks in an album."""

    def __init__(self, name, year, genre):
        self.name = name
        self.year = year
        self.genre = genre

        self.tracks = []

    def add_track(self, track):
        self.tracks.append(track)

    def merge_duplicates(self):
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

    def __repr__(self):
        return ('({name},{year},{genre},{track_count})'
                .format(name=self.name, year=self.year,
                        genre=self.genre, track_count=len(self.tracks)))


class ITunesTrack(object):
    """Representation of an iTunes library music track."""

    def __init__(self, id, name, artist):
        """Create a base music track.

        Sets the id, name, and artist as given.
        Defaults rating to None and plays to 0.
    
        Args:
            id (str): unique track id
            name (str): track name
            artist (str): track artist

        """
        self.id = int(id)
        self.name = name
        self.artist = artist
        self.rating = None
        self.plays = 0

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
        """Retrieves a track identifier in the form of its name and artist.

        Intended to be used for identifying duplicate tracks within the same album.

        Returns:
            tuple of track name, artist
        """
        return (self.name, self.artist)

    def print_verbose(self):
        """Creates a verbose string representation.
        
        Returns:
            a verbose string representation of the track attributes
        """
        rstr = 'Track ID:\t{id}\n'.format(id=self.id)
        rstr += 'Name:\t\t{name}\n'.format(name=self.name)
        rstr += 'Artist:\t\t{artist}\n'.format(artist=self.artist)
        rstr += 'Rating:\t\t{rating}\n'.format(rating=self.rating)
        rstr += 'Play Count:\t{plays}\n'.format(plays=self.plays)

        return rstr

    def __repr__(self):
        rstr = ('({id},{name},{artist},{rating},{plays})'
                .format(id=self.id, name=self.name, artist=self.artist,
                        rating=self.rating, plays=self.plays))
        return rstr
