#!/usr/bin/python
'''parses itunes library xml'''
from __future__ import absolute_import, print_function

import argparse
import datetime
import logging
import os
import pickle

from lxml import etree

from muslytics.utils import ITunesLibrary, ITunesTrack, Artist, Album

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
TRACK_NUMBER_KEY = 'Track Number'
RATING_KEY = 'Rating'
PLAY_COUNT_KEY = 'Play Count'

REQUIRED_TRACK_KEYS = [ID_KEY, NAME_KEY, ARTIST_KEY]


def pickle_library(library, filename=None):
    """Pickle iTunes library to file.

    Args:
        library (muslytics.utils.ITunesLibrary): iTunes library to be pickled
        filename (str): filename to pickle to, defaults to {current datetime}-library.p
    """
    if not filename:
        filename = '{date}-library.p'.format(date=datetime.datetime.now())

    with open(filename, 'wb') as file:
        pickle.dump(library, file)
    
    logger.info(('Pickled {tracks} tracks, {albums} albums, {artists} artists, ' +
                 '{genres} genres to {filename}.')
                 .format(albums=len(library.albums),
                     artists=len(library.artists),
                     tracks=len(library.tracks),
                     genres=len(library.get_genre_map()),
                     filename=filename))


def unpickle_library(filename):
    """Unpickle iTunes library from file.

    Args:
        filename (str): name of the pickled file

    Returns:
        an unpickled ITunesLibrary
    """
    with open(filename, 'rb') as file:
        library = pickle.load(file)

    logger.info(('Unpickled {tracks} tracks, {albums} albums, {artists} artists, ' +
                 '{genres} genres from {filename}.')
                 .format(albums=len(library.albums),
                     artists=len(library.artists),
                     tracks=len(library.tracks),
                     genres=len(library.get_genre_map()),
                     filename=filename))
    return library


def extract_library(filepath, remove_duplicates=False):
    """Extract data from iTunes library XML and split into artists, albums, and tracks.

    Args:
        filepath (str): iTunes library XML filepath
        remove_duplicates (bool): whether to merge duplicate track info, defaults to False

    Returns:
        an ITunesLibrary representing the XML data
    """
    if not os.path.isfile(filepath):
        err = 'Invalid filepath {filepath}'.format(filepath=filepath)
        logger.error(err)
        raise Exception(err)

    library = _get_library(_get_xml_tree(filepath))

    if remove_duplicates:
        library.remove_duplicates()

    return library


def _get_library(xml_tree):
    """Extracts relevant data from the given XML tree and splits into albums, tracks, and artists.

    Skips any elements missing required id, name, artist, album, year.

    Args:
        xml_tree (lxml.etree): etree extracted from the iTunes library XML file

    Returns:
        an ITunesLibrary representing the XML data
    """
    library = ITunesLibrary()
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
            _add_track_to_library(keys, values, library)
        except Exception:
            skipped_count += 1
            continue
 
    logger.info(('Skipped {skipped} tracks. Resulted in {track} tracks, {album} albums, ' +
                 '{artist} artists, and {genre} genres.')
                .format(skipped=skipped_count, track=len(library.tracks),
                        album=len(library.albums), artist=len(library.artists),
                        genre=len(library.get_genre_map())))

    return library


def _add_track_to_library(keys, values, library):
    """Extract desired XML track data and associate it with artist/album in library.

    Extracts the id, name, artist, album, year, genre, track_number, rating, and play counts from
    the given XML key and value lists. All attributes are required for parsing except for play
    count, genre, track_number, and rating, which default to 0, '', None, and None, respectively.

    The track is added to the library and associated with an album. The album is associated with
    the main artist.

    Args:
        keys (list(Element)): list of key XML elements
        values (list(Element)): list of value XML elements
    """
    track_dict = {k:v for (k,v) in zip(keys, values)}
    track_genre = library.get_genre_key(track_dict.get(GENRE_KEY, '').strip().encode('utf-8'))

    track = ITunesTrack(*[track_dict[key].strip().encode('utf-8') for key in REQUIRED_TRACK_KEYS])
    track.set_track_number(track_dict.get(TRACK_NUMBER_KEY, None))
    track.set_rating(track_dict.get(RATING_KEY, None))
    track.set_plays(track_dict.get(PLAY_COUNT_KEY, 0))
    track.set_genre(track_genre)

    library.add_track(track)

    album_name = Album.get_album_name(track_dict[ALBUM_KEY])
    album_year = int(track_dict[YEAR_KEY])
    album_key = (album_name, album_year)

    track.set_album_id(album_key)

    if album_key in library.albums.iterkeys():
        album = library.albums[album_key]
    else:
        album = Album(album_name, album_year)
        library.add_album(album_key, album)
        
    album.add_track(track.id)

    main_artist_name = track.artists[0]

    if main_artist_name in library.artists:
        artist = library.artists[main_artist_name]
    else:
        artist = Artist(main_artist_name)
        library.add_artist(artist)

    artist.add_album(album_key)
    artist.add_genre(track_genre)


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
        library = extract_library(args.xml, True)
        pickle_library(library, args.pickle)
    else:
        library = unpickle_library(args.pickle)

