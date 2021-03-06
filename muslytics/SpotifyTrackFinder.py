#!/usr/bin/python
'''retrieves spotify tracks and their features'''
from __future__ import absolute_import, print_function

import argparse
import datetime
import logging
import pickle
import re
import requests

from gevent import sleep
from spotipy import Spotify, SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials
from unidecode import unidecode

from muslytics import configure_logging
from muslytics import ITunesXMLParser as ixml 
from muslytics.SpotifyUtils import SpotifyTrack
from muslytics.Utils import strip_featured_artists, MULT_ARTIST_PATTERN, AUDIO_FEATURES

logger = logging.getLogger(__name__)

SPOTIFY_CLIENT_ID = '914476c8336d4641b49905bc5fbd96f1'

MAX_RETRY = 3
RETRY_CODES = [requests.codes.server_error,
               requests.codes.bad_gateway,
               requests.codes.service_unavailable]
WAIT_CODE = requests.codes.too_many_requests

TRACK = 'track'
SPECIAL_CHAR_MATCH = re.compile('[^\s\w]+')
MAX_REQUEST_TRACKS = 100


def pickle_spotify(spotify_tracks, filename=None):
    """Pickle Spotify tracks to file.

    Args:
        spotify_tracks (list(muslytics.SpotifyUtils.SpotifyTrack): a list of Spotify tracks
        filename (str): filename to pickle to, defaults to {current datetime}-spotify.p
    """
    if not filename:
        filename = '{date}-spotify.p'.format(date=datetime.datetime.now())

    with open(filename, 'wb') as file:
        pickle.dump(spotify_tracks, file)
    
    logger.info('Pickled {tracks} tracks to {filename}.'.format(tracks=len(spotify_tracks),
                                                                filename=filename))


def unpickle_spotify(filename):
    """Unpickle Spotify tracks from file.

    Args:
        filename (str): name of the pickled file

    Returns:
        an unpickled list of Spotify tracks
    """
    with open(filename, 'rb') as file:
        spotify_tracks = pickle.load(file)

    logger.info(('Unpickled {tracks} tracks from {filename}.')
                 .format(tracks=len(spotify_tracks), filename=filename))

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
    try:
        return deferred_request()
    except SpotifyException as s_err:
        error_status = s_err.http_status
        if error_status in RETRY_CODES and retried < MAX_RETRY:
            return _make_spotify_request(deferred_request, retried + 1)
        elif error_status == WAIT_CODE:
            # TODO: figure out where to pull X from 'retry in X seconds' from
            # import ipdb; ipdb.set_trace()
            sleep(5)
            return _make_spotify_request(deferred_request, retried + 1)


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
    """Retrieve Spotify track info of tracks that match to the library.

    Args:
        library (muslytics.ITunesUtils.ITunesLibrary): iTunes library data
        trace (bool): whether Spotify API trace should be turned on, defaults to False

    Returns:
        a list of SpotifyTracks that correspond to iTunes library tracks
    """
    spotify = _make_spotify_instance(trace)
    return _get_audio_features(spotify, _get_spotify_track_ids(spotify, library))


def _get_spotify_track_ids(spotify, library):
    """Retrieve Spotify IDs of tracks that match to the library.

    Args:
        spotify (spotipy.Spotify): a Spotify instance
        library (muslytics.ITunesUtils.ITunesLibrary): iTunes library data

    Returns:
        a list of SpotifyTracks representing the matched tracks
    """
    # { SpotifyTrack }
    matched_tracks = []

    for track_id, i_track in library.tracks.iteritems():
        search_terms = _make_search_terms(i_track)
        try:
            results = _make_search_request(spotify, search_terms, type=TRACK)['tracks']['items']
        except Exception as err:
            logger.error(err.message, exc_info=True)
            logger.debug('Skipping {track} due to error.'.format(track=i_track))
            continue

        for result in results:
            if _is_track_match(i_track, result):
                spotify_id = result['id']
                logger.debug('\tMatch found for {track} by {artists} (i_id={i_id}, s_id={s_id})'
                              .format(track=i_track.name, artists=','.join(i_track.artists),
                                      i_id=track_id, s_id=spotify_id))
                s_track = SpotifyTrack(spotify_id, track_id, i_track.name)
                s_track.popularity = result['popularity']
                matched_tracks.append(s_track)
                break
        else:
            logger.debug('\tNo match found for {track} by {artists} (i_id={id})'
                          .format(track=i_track.name, artists=','.join(i_track.artists),
                                  id=track_id))

    logger.info('Matched {added} tracks in Spotify. Skipped {skipped} tracks.'
                .format(added=len(matched_tracks),
                        skipped=len(library.tracks)-len(matched_tracks)))

    return matched_tracks


def _get_audio_features(spotify, tracks):
    """Retrieve audio features for the Spotify tracks.

    Args:
        spotify (spotipy.Spotify): a Spotify instance
        tracks (list(muslytics.SpotifyUtils.SpotifyTrack)): spotify tracks to retrieve audio
        features for

    Returns:
        a list of SpotifyTracks with the audio features attached
    """
    track_dict = {track.id: track for track in tracks}
    r_tracks = []

    num_tracks = len(tracks)
    lower_index = 0

    while lower_index < num_tracks:
        upper_index = min(lower_index + MAX_REQUEST_TRACKS, num_tracks)
        request_ids = [track.id for track in tracks[lower_index:upper_index]]

        try:
            audio_features = _make_spotify_request(lambda: spotify.audio_features(request_ids))
        except Exception as err:
            logger.error(err.message, exc_info=True)
            logger.debug('Skipping tracks {i}-{j} due to error.'.format(i=lower_index,
                                                                        j=upper_index))
            lower_index = upper_index
            continue

        for id, features in zip(request_ids, audio_features):
            track = track_dict[id]
            try: 
                for feature in AUDIO_FEATURES:
                    track.__setattr__(feature, features[feature])
                r_tracks.append(track)
                logger.debug('Added features for {name} (s_id={s_id}, i_id={i_id})'
                             .format(name=track.name, s_id=track.id, i_id=track.i_id))
            except Exception as err:
                logger.error(err.message, exc_info=True)
                logger.debug('Skipping {name} (s_id={s_id}, i_id={i_id})'.format(name=track.name,
                                                                                 s_id=track.id,
                                                                                 i_id=track.i_id))

        lower_index = upper_index

    logger.info('Determined the audio features for {added} tracks. Skipped {skipped} tracks.'
                .format(added=len(r_tracks), skipped=num_tracks-len(r_tracks)))


    return r_tracks


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
    parser.add_argument('-v', '--verbose', action='store_true',
            help='increase output verbosity, defaults to False')
    parser.add_argument('-l', '--logging', required=False,
            help='log to the given filename')
    args = parser.parse_args()

    configure_logging(args.verbose, args.logging)

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


