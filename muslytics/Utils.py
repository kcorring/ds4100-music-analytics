#!/usr/bin/python
'''general utility classes'''
from __future__ import absolute_import, print_function

import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UNKNOWN_GENRE = 0

ALBUM_NAME_PATTERN = re.compile('\s*((\-\s*(Single|EP))|(\(.*Deluxe.*\))|(\[.*Deluxe.*\]))\s*')
MULT_ARTIST_PATTERN = re.compile('\s*[,&]\s*')
FEAT_ARTIST_PATTERN = re.compile('\s*(\(feat\..*\)|\-\s*feat\..*)\s*')

ACOUSTICNESS = 'acousticness'
DANCEABILITY = 'danceability'
DURATION = 'duration_ms'
ENERGY = 'energy'
INSTRUMENTALNESS = 'instrumentalness'
KEY = 'key'
LIVENESS = 'liveness'
LOUDNESS = 'loudness'
MODE = 'mode'
SPEECHINESS = 'speechiness'
TEMPO = 'tempo'
TIME_SIGNATURE = 'time_signature'
VALENCE = 'valence'

AUDIO_FEATURES = [ACOUSTICNESS,
                  DANCEABILITY,
                  DURATION,  # int
                  ENERGY,
                  INSTRUMENTALNESS,
                  KEY,  # int
                  LIVENESS,
                  LOUDNESS,
                  MODE,  # int
                  SPEECHINESS,
                  TEMPO,
                  TIME_SIGNATURE,  # int
                  VALENCE,
                  ]

POPULARITY = 'popularity'

GENRE = 'genre'
LOVED = 'loved'
PLAYS = 'plays'
RATING = 'rating'

OTHER_FEATURES = [GENRE,
                  LOVED,
                  PLAYS,
                  RATING,
                  ]


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
    name = name.strip()
    return re.sub(ALBUM_NAME_PATTERN, '', name)


def strip_featured_artists(name):
    """Strip '(feat. X)' artist info from a song title.

    Args:
        name (str): song title

    Returns:
        the song title without any featured artists
    """
    return FEAT_ARTIST_PATTERN.sub(' ', name).strip()


class Track(object):
    """Abstract representation of a track."""

    def __init__(self, id, name):
        """Base track representation.

        Args:
            id (int/str): track id
            name (str): track name
        """
        self.id = id
        self.name = name

class SuperTrack(Track):
    """Representation of a track with audio features and other information."""

    def __init__(self, id, name):
        """Base super track representation.

        Args:
            id (str): track id
            name (str): track name
        """
        self._inner = {feature: None for feature in AUDIO_FEATURES + OTHER_FEATURES}
        self.artists = []
        self.popularity=None
        self.other_id = None
        super(SuperTrack, self).__init__(id, name)

    def __getattr__(self, attr):
        if attr not in AUDIO_FEATURES + OTHER_FEATURES:
            raise AttributeError('{cls} has no attribute {attr}'.format(cls=self.__class__,
                                                                        attr=attr))
        else:
            return self._inner[attr]

    def __setattr__(self, attr_name, attr_value):
        if attr_name in ['id', 'other_id', 'name', 'artists', 'popularity', '_inner']:
            super(SuperTrack, self).__setattr__(attr_name, attr_value)
        else:
            if attr_name in self._inner:
                self._inner[attr_name] = attr_value
            else:
                raise AttributeError('{cls} has no attribute {attr}'.format(cls=self.__class__,
                                                                            attr=attr))

    def __repr__(self):
        return ('({name} by {artists}, ({id}, {other_id}), {features})'
                .format(name=self.name,
                        artists=self.artists,
                        id=self.id,
                        other_id=self.other_id,
                        features=self._inner.__repr__()))
