#!/usr/bin/python
'''parses itunes library xml'''
from __future__ import absolute_import, print_function

import argparse
import datetime
import logging
import os
import pickle

from lxml import etree

from muslytics.tracks import ITunesTrack

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


def merge_duplicates(tracks):
    """Merge duplicate track rating and play count info.

    Tracks are marked duplicates by equal get_identifier() results. The sum of the plays and
    average of the ratings is used.

    Args:
        tracks (list(ITunesTrack)): tracks to be scanned for duplicates and merged where necessary
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
        logger.info('Identified duplicate track ({dup}).'.format(dup=duplicate_identifier))
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
    
    logger.info('Removed {removed} duplicate tracks, {remained} tracks remain.'
            .format(removed=removed_count, remained=len(tracks)))


def pickle_tracks(tracklist, filename=None):
    """Pickle iTunes track list to file.

    Args:
        tracklist (list(ITunesTrack)): iTunes tracks to be pickled
        filename (str): filename to pickle to, defaults to {current datetime}-tracklist.p
    """
    if not filename:
        filename = '{date}-tracklist.p'.format(date=datetime.datetime.now()) 

    with open(filename, 'wb') as file:
        pickle.dump(tracklist, file)
    
    logger.info('Pickled {tracks} tracks to {filename}.'
                .format(tracks=len(tracklist), filename=filename))


def unpickle_tracks(filename):
    """Unpickle an iTunes track list from file.

    Args:
        filename (str): name of the pickled file

    Returns:
        a list of ITunesTrack data
    """
    with open(filename, 'rb') as file:
        tracklist = pickle.load(file)

    logger.info('Unpickled {tracks} tracks from {filename}.'
                .format(tracks=len(tracklist), filename=filename))
    return tracklist


def extract_tracks(filepath):
    """Extract music tracks from iTunes library XML.

    Args:
        filepath (str): iTunes library XML filepath

    Returns:
        a list of dict representing the tracks
    """
    if not os.path.isfile(filepath):
        err = 'Invalid filepath {filepath}'.format(filepath=filepath)
        logger.error(err)
        raise Exception(err)

    return _get_tracks(_get_xml_tree(filepath))


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
 
    logger.info('Parsed {added} tracks and skipped {skipped} tracks.'
                .format(added=added_count, skipped=skipped_count))

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

    track = ITunesTrack(*[track_dict[key].strip() for key in REQUIRED_KEYS])
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
    parser.add_argument('pickle', help='filepath to save/load pickled track data')
    parser.add_argument('-x', '--xml', required=False,
            help='path to iTunes library XML file')
    args = parser.parse_args()

    if args.xml:
        tracks = extract_tracks(args.xml)
        merge_duplicates(tracks)
        pickle_tracks(tracks, args.pickle)
    else:
        tracks = unpickle_tracks(args.pickle)

