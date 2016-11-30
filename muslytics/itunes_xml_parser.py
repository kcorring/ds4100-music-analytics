#!/usr/bin/python
'''parses itunes library xml'''
from __future__ import absolute_import, print_function

import argparse
import logging
import os

from lxml import etree

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('iTunes XML Parser')

TRACKS_XPATH = '/plist/dict/dict/dict'


VIDEO_KEY = 'Has Video'
ID_KEY = 'Track ID'
NAME_KEY = 'Name'
ARTIST_KEY = 'Artist'
ALBUM_ARTIST_KEY = 'Album Artist'
ALBUM_KEY = 'Album'
YEAR_KEY = 'Year'
GENRE_KEY = 'Genre'
RATING_KEY = 'Rating'
PLAY_COUNT_KEY = 'Play Count'

REQUIRED_KEYS = [ID_KEY, NAME_KEY, ARTIST_KEY, ALBUM_KEY, YEAR_KEY, GENRE_KEY]


class Track(object):
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
        self.name = name
        self.artist = artist
        self.album = album
        self.year = int(year)
        self.genre = genre

        self.album_artist = artist
        self.rating = None
        self.plays = 0

    def set_album_artist(self, album_artist):
        """Set the track album artist if given a truthy value.

        Args:
            album_artist (str): track album artist
        """
        if album_artist:
            self.album_artist = album_artist

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
        return '%s_%s_%s' % (self.name, self.artist, self.year)

    def print_verbose(self):
        """Creates a verbose string representation.
        
        Returns:
            a verbose string representation of the track attributes
        """
        rstr = '%s:\t%d\n' % (ID_KEY, self.id)
        rstr += '%s:\t\t%s\n' % (NAME_KEY, self.name)
        rstr += '%s:\t\t%s\n' % (ARTIST_KEY, self.artist)
        rstr += '%s:\t%s\n' % (ALBUM_ARTIST_KEY, self.album_artist)
        rstr += '%s:\t\t%s\n' % (ALBUM_KEY, self.album)
        rstr += '%s:\t\t%d\n' % (YEAR_KEY, self.year)
        rstr += '%s:\t\t%s\n' % (GENRE_KEY, self.genre)
        rstr += '%s:\t\t%s\n' % (RATING_KEY, self.rating)
        rstr += '%s:\t%d\n' % (PLAY_COUNT_KEY, self.plays)

        return rstr

    def __repr__(self):
        rstr = '(%d,%s,%s,%s,%s,%d,%s,%s,%d)' % \
                (self.id, self.name, self.artist, self.album_artist, self.album,
                        self.year, self.genre, self.rating, self.plays)
        return rstr


def merge_duplicates(tracks):
    """Merge duplicate track rating and play count info.

    Tracks are marked duplicates by equal get_identifier() results. The sum of the plays and
    average of the ratings is used.

    Args:
        tracks (list(Track)): tracks to be scanned for duplicates and merged where necessary

    Returns:
        a list of Tracks with duplicates merged and extraneous tracks removed
    """
    identifier_to_index = {}
    duplicate_identifiers = set()
    removable = []
    removed_count = 0

    # here, track_ids are the string identifiers not the unique int ids
    for i, track in enumerate(tracks):
        track_id = track.get_identifier()
        if track_id in identifier_to_index:
            duplicate_identifiers.add(track_id)
            identifier_to_index[track_id].append(i)
            removable.append(i)
        else:
            identifier_to_index[track_id] = [i]

    for duplicate_identifier in duplicate_identifiers:
        logger.info('Identified duplicate track (%s).' % duplicate_identifier)
        duplicate_indexes = identifier_to_index[duplicate_identifier]
        duplicate_tracks = [tracks[i] for i in duplicate_indexes]
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
        del tracks[i]
        removed_count += 1
    
    logger.info('Removed %d duplicate tracks, %d tracks remain.' % (removed_count, len(tracks)))
    return tracks


def extract_tracks(filepath):
    """Extract music tracks from iTunes library XML.

    Args:
        filepath (str): iTunes library XML filepath

    Returns:
        a list of dict representing the tracks
    """
    if not os.path.isfile(filepath):
        err = 'Invalid filepath %s' % (filepath)
        logger.error(err)
        raise Exception(err)

    tracks = _get_tracks(_get_xml_tree(filepath))
    return merge_duplicates(tracks)


def _get_tracks(xml_tree):
    """Extracts all music tracks containing the required info from the given XML tree.

    Args:
        xml_tree (lxml.etree): etree extracted from the iTunes library XML file

    Returns:
        a list of dict representing music tracks
    """
    tracks = []
    added_count = 0
    skipped_count = 0
    # track_elems = [ Element ], representing individual track info
    track_elems = xml_tree.xpath(TRACKS_XPATH)

    for elem in track_elems:
        # get the key and value names from the Elements
        track_kv = [x.text for x in elem.getchildren()]
        keys, values = track_kv[::2], track_kv[1::2]
        # we don't care about music videos/tv shows/movies and this is one
        if VIDEO_KEY in keys:
            skipped_count += 1
            continue

        try:
            track = _build_track(keys, values)
            tracks.append(track)
            added_count += 1
        except Exception:
            skipped_count += 1
            continue
 
    logger.info('Parsed %d tracks and skipped %d tracks.' % (added_count, skipped_count))

    return tracks


def _build_track(keys, values):
    """Extract desired XML track data.

    Extracts the id, name, artist, album artist, album, year, genre, rating, and play counts from
    the given XML key and value lists. All attributes are required for parsing except for album
    artist, play count, and  rating, which default to artist, 0, and None, respectively.

    Args:
        keys (list(Element)): list of key XML elements
        values (list(Element)): list of value XML elements

    Returns:
        a dict containing the desired track attributes
    """
    track_dict = {k:v for (k,v) in zip(keys, values)}

    track = Track(*[track_dict[key].strip() for key in REQUIRED_KEYS])
    track.set_album_artist(track_dict.get(ALBUM_ARTIST_KEY, None))
    track.set_rating(track_dict.get(RATING_KEY, None))
    track.set_plays(track_dict.get(PLAY_COUNT_KEY, 0))

    return track


def _get_xml_tree(filepath):
    """Extract an XML tree from a file.
    
    Args:
        filepath (str): iTunes library XML filepath

    Returns:
        an lxml etree representing the document with tag-external blankspace removed
    """
    parser = etree.XMLParser(remove_blank_text=True)
    return etree.parse(filepath, parser=parser)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("ilib", help="path to iTunes library XML file")
    args = parser.parse_args()
    tracks = extract_tracks(args.ilib)
