#!/usr/bin/python
'''parses itunes library xml'''
from __future__ import absolute_import, print_function

import argparse
import datetime
import logging
import os
import pickle

from lxml import etree

from muslytics.utils import ITunesTrack, Album

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('iTunes XML Parser')

TRACKS_XPATH = '/plist/dict/dict/dict'

VIDEO_KEY = 'Has Video'
ID_KEY = 'Track ID'
NAME_KEY = 'Name'
ARTIST_KEY = 'Artist'
ALBUM_KEY = 'Album'
YEAR_KEY = 'Year'
GENRE_KEY = 'Genre'
RATING_KEY = 'Rating'
PLAY_COUNT_KEY = 'Play Count'

REQUIRED_KEYS = [ID_KEY, NAME_KEY, ARTIST_KEY]


def pickle_albums(albums, filename=None):
    """Pickle iTunes albums to file.

    Args:
        albums (dict): iTunes albums to be pickled
        filename (str): filename to pickle to, defaults to {current datetime}-albums.p
    """
    if not filename:
        filename = '{date}-albums.p'.format(date=datetime.datetime.now()) 

    with open(filename, 'wb') as file:
        pickle.dump(albums, file)
    
    logger.info('Pickled {albums} albums ({tracks} tracks) to {filename}.'
                .format(albums=len(albums),
                    tracks=sum(len(album.tracks) for album in albums.itervalues()),
                    filename=filename))


def unpickle_albums(filename):
    """Unpickle iTunes albums/tracks from file.

    Args:
        filename (str): name of the pickled file

    Returns:
        a dict of Albums containing ITunesTrack data
    """
    with open(filename, 'rb') as file:
        albums = pickle.load(file)

    logger.info('Unpickled {albums} albums ({tracks} tracks) from {filename}.'
                .format(albums=len(albums),
                    tracks=sum(len(album.tracks) for album in albums.itervalues()),
                    filename=filename))
    return albums


def extract_albums(filepath):
    """Extract music tracks from iTunes library XML and splits into albums.

    Args:
        filepath (str): iTunes library XML filepath

    Returns:
        a dict representing the music tracks separated into albums
    """
    if not os.path.isfile(filepath):
        err = 'Invalid filepath {filepath}'.format(filepath=filepath)
        logger.error(err)
        raise Exception(err)

    albums = _get_albums(_get_xml_tree(filepath))
    for a in albums.values():
        a.merge_duplicates()

    return albums


def _get_albums(xml_tree):
    """Extracts all music tracks from the given XML tree and splits into albums.

    Skips any elements missing required id, name, artist, album, year, genre.

    Args:
        xml_tree (lxml.etree): etree extracted from the iTunes library XML file

    Returns:
        a dict representing the music tracks separated into albums
    """
    albums = {}
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
            albums = _add_track_to_albums(keys, values, albums)
            added_count += 1
        except Exception:
            skipped_count += 1
            continue
 
    logger.info('Parsed {added} tracks and skipped {skipped} tracks.'
                .format(added=added_count, skipped=skipped_count))

    return albums


def _add_track_to_albums(keys, values, albums):
    """Extract desired XML track data and insert into an album.

    Extracts the id, name, artist, album, year, genre, rating, and play counts from
    the given XML key and value lists. All attributes are required for parsing except for play
    count, genre, and rating, which default to 0, '', and None, respectively.

    Creates a track and inserts it into an existing album or creates a new one. Album membership
    is determined by album and year.

    Args:
        keys (list(Element)): list of key XML elements
        values (list(Element)): list of value XML elements

    Returns:
        a dict of albums with the new track added
    """
    track_dict = {k:v for (k,v) in zip(keys, values)}

    track = ITunesTrack(*[track_dict[key].strip().encode('utf-8') for key in REQUIRED_KEYS])
    track.set_rating(track_dict.get(RATING_KEY, None))
    track.set_plays(track_dict.get(PLAY_COUNT_KEY, 0))
    track.set_genre(track_dict.get(GENRE_KEY, '').strip().encode('utf-8'))

    album_name = Album.get_album_name(track_dict[ALBUM_KEY])
    album_year = int(track_dict[YEAR_KEY])
    album_key = (album_name, album_year)

    if album_key in albums:
        albums[album_key].add_track(track)
    else:
        album = Album(album_name, album_year)
        album.add_track(track)
        albums[album_key] = album

    return albums


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
    parser.add_argument('pickle', help='filepath to save/load pickled track data')
    parser.add_argument('-x', '--xml', required=False,
            help='path to iTunes library XML file')
    args = parser.parse_args()

    if args.xml:
        albums = extract_albums(args.xml)
        pickle_albums(albums, args.pickle)
    else:
        albums = unpickle_albums(args.pickle)

