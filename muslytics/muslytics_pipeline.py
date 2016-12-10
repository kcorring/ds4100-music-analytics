#!/usr/bin/python
import argparse
import datetime
import logging
import pickle

from muslytics import configure_logging
from muslytics import ITunesXMLParser as ixml
from muslytics import SpotifyTrackFinder as stf 
from muslytics.Utils import combine_spotify_itunes_tracks

logger = logging.getLogger(__name__)


def pickler(data, filebase, datatype):
    """Pickle data to file.

    Args:
        data (any): data to be pickled to a file
        filebase (str): the base of the filename
        type (str): the type of what is being pickled (to be inserted in filename)
        filename (str): filename to pickle to
    """
    filename = '{base}-{type}.p'.format(base=filebase, type=datatype)

    with open(filename, 'wb') as file:
        pickle.dump(data, file)

    logger.info('Pickled {items} items to {filename}.'.format(items=len(data),
                                                              filename=filename))


def unpickler(filename):
    """Unpickle data from file.

    Args:
        filename (str): name of the pickled file

    Returns:
        the unpickled data
    """
    with open(filename, 'rb') as file:
        data = pickle.load(file)

    logger.info('Unpickled {items} items from {filename}.'.format(items=len(data),
                                                                   filename=filename))

    return data


def get_tracks_from_itunes_xml(i_xml, pickle, merge_duplicates=True, trace=False):
    """Parse an iTunes XML file and match to Spotify songs with audio features.

    Runs through the muslytics pipeline by parsing songs out of an iTunes XML file, matching them
    to songs on Spotify, and combining iTunes rating/play count/genre information to Spotify audio
    features and popularity info.

    Args:
        i_xml (str): path to the iTunes library XML file
        pickle (str): base of filename for pickled iTunes library and Spotify tracks
        merge_duplicates (bool): whether iTunes library parsing should combine data for songs with
            the same name and artist, defaults to False
        trace (bool): whether Spotify API tracing should be turned on, defaults to False

    Returns:
        a list of Tracks that contain iTunes and Spotify data
    """
    library = ixml.extract_library(i_xml, merge_duplicates)
    pickler(library, pickle, 'itunes')

    s_tracks = stf.get_spotify_tracks(library, trace)
    pickler(s_tracks, pickle, 'spotify')
    return combine_spotify_itunes_tracks(s_tracks, library.tracks)


def get_tracks_from_itunes_pickle(ipickle, pickle, trace=False):
    """Match tracks from pickled iTunes file to Spotify songs with audio features.

    Runs through the muslytics pipeline by unpickling parsed iTunes tracks, matching them to songs
    on Spotify, and combining iTunes rating/play count/genre information to Spotify audio features
    and popularity info.

    Args:
        ipickle (str): path to the pickled iTunes data file
        pickle (str): base of filename for pickled Spotify tracks
        trace (bool): whether Spotify API tracing should be turned on, defaults to False

    Returns:
        a list of Tracks that contain iTunes and Spotify data
    """
    library = unpickler(ipickle)
    s_tracks = stf.get_spotify_tracks(library, trace)
    pickler(s_tracks, pickle, 'spotify')
    return combine_spotify_itunes_tracks(s_tracks, library.tracks)


def get_tracks_from_pickles(ipickle, spickle):
    """Merge tracks from pickled iTunes and Spotify track files.

    Combining iTunes rating/play count/genre information to Spotify audio features and popularity
    info for the tracks in the given pickle files.

    Args:
        ipickle (str): path to the pickled iTunes data file
        spickle (str): path to the pickled Spotify data file

    Returns:
        a list of Tracks that contain iTunes and Spotify data
    """
    i_tracks = unpickler(ipickle).tracks
    s_tracks = unpickler(spickle)
    return combine_spotify_itunes_tracks(s_tracks, i_tracks)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-v', '--verbose', action='store_true', help='increase output verbosity')
    parser.add_argument('-l', '--log', required=False, help='log to the given file')

    subparsers = parser.add_subparsers(dest='subcommand', help='sub-command help')

    parser_full = subparsers.add_parser('full', help='get tracks starting from iTunes XML')
    parser_full.add_argument('xml', help='path to iTunes library XML file')
    parser_full.add_argument('pickle', help='path for base output pickle file')

    parser_spotify = subparsers.add_parser('spotify',
                                           help='get tracks starting from pickled iTunes tracks')
    parser_spotify.add_argument('ipickle', help='path to pickled iTunes track file')
    parser_spotify.add_argument('pickle', help='path base for output pickle file')

    parser_merge = subparsers.add_parser('merge', help='merge pickled iTunes and Spotify tracks')
    parser_merge.add_argument('ipickle', help='path to pickled iTunes track file')
    parser_merge.add_argument('spickle', help='path to pickled Spotify track file')
    parser_merge.add_argument('pickle', help='path base for output pickle file')


    parser_load = subparsers.add_parser('load',
                                        help='load from pickled track (already merged) file')
    parser_load.add_argument('pickle', help='path for input pickled track file')

    args = parser.parse_args()

    configure_logging(args.verbose, args.log)

    if args.subcommand != 'load':
        if args.subcommand == 'full':
            tracks = get_tracks_from_itunes_xml(args.xml, args.pickle)
        elif args.subcommand == 'spotify':
            tracks = get_tracks_from_itunes_pickle(args.ipickle, args.pickle)
        else:
            tracks = get_tracks_from_pickles(args.ipickle, args.spickle)

        pickler(tracks, args.pickle, 'merged')
    else:
        unpickle(args.pickle)

