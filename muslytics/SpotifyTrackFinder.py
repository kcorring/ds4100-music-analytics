#!/usr/bin/python
'''retrieves spotify tracks and their features'''
from __future__ import absolute_import, print_function

import argparse
import logging
import pickle
import re
import requests

from gevent import sleep
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from unidecode import unidecode

from muslytics import ITunesXMLParser as ixml 
from muslytics.Utils import strip_featured_artists, MULT_ARTIST_PATTERN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SPOTIFY_CLIENT_ID = '914476c8336d4641b49905bc5fbd96f1'
RETRY_CODES = [requests.codes.server_error,
               requests.codes.bad_gateway,
               requests.codes.service_unavailable]
WAIT_CODE = requests.codes.too_many_requests

TRACK = 'track'
SPECIAL_CHAR_MATCH = re.compile('[^\s\w]+')


def pickle_spotify(spotify_tracks, filename=None):
    """Pickle Spotify tracks to file.

    Args:
        spotify_tracks (dict): a dict of Spotify tracks
        filename (str): filename to pickle to, defaults to {current datetime}-spotify.p
    """
    if not filename:
        filename = '{date}-spotify.p'.format(date=datetime.datetime.now())

    with open(filename, 'wb') as file:
        pickle.dump(spotify_tracks, file)
    
    logger.info(('Pickled {tracks} tracks to {filename}.')
                 .format(tracks=len(spotify_tracks.keys()),
                         filename=filename))


def unpickle_spotify(filename):
    """Unpickle Spotify tracks from file.

    Args:
        filename (str): name of the pickled file

    Returns:
        an unpickled dict of Spotify tracks
    """
    with open(filename, 'rb') as file:
        spotify_tracks = pickle.load(file)

    logger.info(('Unpickled {tracks} tracks from {filename}.')
                 .format(tracks=len(spotify_tracks.keys()),
                         filename=filename))
    return spotify_tracks


def _make_spotify_instance(trace=False):
    """Create a spotipy instance for use.

    Requires on SPOTIPY_CLIENT_SECRET env variable.

    Args:
        trace (bool): turns on tracing
    
    Returns:
        a spotipy.Spotify instance
    """
    client_credentials_manager = SpotifyClientCredentials()
    spotify = Spotify(client_credentials_manager=client_credentials_manager)
    spotify.trace = trace

    return spotify


def _make_spotify_request(deferred_request, retried=0):
    """Make a Spotify request and catch any errors.

    Args:
        deferred_request (func): lambda wrapped spotify request
        retried (int): how many times the request has been tried unsuccessfully

    Returns:
        dict of results from the request
    """
    # TODO: spotipy does its own retry; if that's sufficient, just do logging here
    try:
        return deferred_request()
    except SpotifyException as s_err:
        error_status = s_err.http_status
        if error_status in RETRY_CODES and retried < MAX_RETRY:
            _make_spotify_request(deferred_request, retried + 1)
        elif error_status == WAIT_CODE:
            # TODO: figure out where to pull X from 'retry in X seconds' from
            sleep(5)
            make_spotify_request(deferred_request, retried + 1)


def _make_search_request(spotify, search_query, type):
    """Make a Spotify API search request.

    Args:
        spotify (Spotify): Spotify instance
        search_query (str): terms to be searched
        type (str): the type of results to search (e.g. track, artist, album)

    Returns:
        dict of results from the request
    """
    logger.debug('Search query:\'{q}\' ({type})'.format(q=search_query, type=type))
    return _make_spotify_request(lambda: spotify.search(q=search_query, type=type))


def get_spotify_tracks(library, trace=False):
    """Retrieve Spotify IDs of tracks that match to the library.

    Args:
        library (muslytics.ITunesUtils.ITunesLibrary): iTunes library data
        trace (bool): whether Spotify API trace should be turned on, defaults to False
    Returns:
        a dict of iTunes track ids to Spotify track ids and the track popularities
    """
    spotify = _make_spotify_instance(trace)

    # { itunes track id : ( spotify track id, spotify track popularity ) }
    matched_tracks = {}

    for track_id, track in library.tracks.iteritems():
        search_terms = _make_search_terms(track)
        results = _make_search_request(spotify, search_terms, type=TRACK)['tracks']['items']
        for result in results:
            if _is_track_match(track, result):
                spotify_id = result['id']
                logger.debug('\tMatch found for {track} by {artists} (i_id={i_id}, s_id={s_id})'
                              .format(track=track.name, artists=','.join(track.artists),
                                      i_id=track_id, s_id=spotify_id))
                matched_tracks[track_id] = (spotify_id, result['popularity'])
                break
        else:
            logger.debug('\tNo match found for {track} by {artists} (i_id={id})'
                          .format(track=track.name, artists=','.join(track.artists), id=track_id))

    # TODO: GET AUDIO FEATURES AND CREATE A NEW TRACK OBJECT TO STORE THEM IN
    return matched_tracks


def _make_search_terms(track):
    """Converts an iTunes track into a Spotify search query.

    Args:
        track (muslytics.Utils.Track): track to search on Spotify

    Returns:
        a str representing the search query for this track
    """
    return '{name} {artist}'.format(name=track.name, artist=track.artists[0])


def _is_track_match(i_track, s_track):
    """Check if an iTunes track matches a Spotify track search result.

    All words will be converted to lowercase, parenthetical content stripped out,
    and non-alphanumeric/non-whitespace characters stripped out of the song title
    and artist names. Extra whitespace is removed. The resulting song title must
    be an exact match, and at least one iTunes track artist must match a Spotify
    track artist for the tracks to be determined matching.

    Args:
        i_track (muslytics.ITunesUtils.ITunesTrack): the ITunesTrack
        s_track (dict): the Spotify API track search result

    Returns:
        a bool denoting whether the tracks match
    """
    i_name = i_track.name.lower()
    i_artists = {artist.lower() for artist in i_track.artists}
    s_name = unidecode(strip_featured_artists(s_track['name'])).lower()
    s_artists = {unidecode(artist_name).lower()
                 for artist in s_track['artists']
                 for artist_name in re.split(MULT_ARTIST_PATTERN, artist['name'])}

    name_matched, artist_matched = _check_name_artist_matches(i_name, s_name,
                                                              i_artists, s_artists)

    if name_matched and artist_matched:
        return True

    if not name_matched:
        i_name = _remove_chars(i_name)
        s_name = _remove_chars(s_name)
    if not artist_matched:
        i_artists = {_remove_chars(artist) for artist in i_artists}
        s_artists = {_remove_chars(artist) for artist in s_artists}

    name_matched, artist_matched = _check_name_artist_matches(i_name, s_name,
                                                              i_artists, s_artists)

    return name_matched and artist_matched


def _remove_chars(string):
    """Strip occurrences of non-alphanumeric/non-whitespace and remove extra whitespace.

    Args:
        string (str): string to strip from

    Returns:
        the string with no occurrences of the non-alphanumeric/whitespace characters or extra
        whitespace
    """
    return ' '.join((re.sub(SPECIAL_CHAR_MATCH, '', string)).split())


def _check_name_artist_matches(i_name, s_name, i_artists, s_artists):
    """Check if track details are a match.

    Track names must be an exact match. At least one artist in i_artists must be
    an exact match to an artist in s_artists.

    Args:
        i_name (str): iTunes track name
        s_name (str): Spotify track name
        i_artists (set(str)): iTunes artists
        s_artists (set(str)): Spotify artists

    Returns:
        a bool denoting whether the tracks are a match
    """
    return (i_name == s_name, len(i_artists - s_artists) < len(i_artists))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('spickle', help='filepath to save/load pickled spotify track data')
    parser.add_argument('-f', '--full', required=False,
            help='path to iTunes library XML file for full run')
    parser.add_argument('-i', '--ipickle', required=False,
            help='path to iTunes album pickle')
    parser.add_argument('-t', '--trace', action='store_true',
            help='turn on Spotify API tracing, defaults to False')
    parser.add_argument('-d', '--debug', action='store_true',
            help='turn on debug logging, defaults to False')
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    if args.full or args.ipickle:
        if args.full:
            if 'ipickle' not in args:
                parser.error('--full requires --ipickle to save parsed albums to')

            library = ixml.extract_library(args.full)
            ixml.pickle_library(library, args.ipickle)
        elif args.ipickle:
            library = ixml.unpickle_library(args.ipickle)

        spotify_tracks = get_spotify_tracks(library, args.trace)
        pickle_spotify(spotify_tracks, args.spickle)
    else:
        spotify_tracks = unpickle_spotify(args.spickle)


