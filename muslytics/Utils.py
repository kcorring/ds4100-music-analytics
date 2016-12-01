#!/usr/bin/python
'''general utility classes'''
from __future__ import absolute_import, print_function

import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UNKNOWN_GENRE = 0

ALBUM_NAME_PATTERN = re.compile('\s*((\-\s*(Single|EP))|(\(.*Deluxe.*\))|(\[.*Deluxe.*\]))\s*')

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
