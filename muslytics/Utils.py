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
            id (int): track id
            name (str): track name
        """
        self.id = id
        self.name = name

