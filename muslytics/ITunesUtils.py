#!/usr/bin/python
'''itunes utility classes'''
from __future__ import absolute_import, print_function

import logging
import re

from muslytics.Utils import Track, UNKNOWN_GENRE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUB_FEAT_PAT = re.compile('\s*\(feat\.(?P<artist>.*)\)\s*')
FEAT_PATTERN = re.compile('.*\(feat\.(?P<artist>.*)\)\s*')
MULT_PATTERN = re.compile('\s*[,&]\s*')


# TODO: WILL NEED TO CONVERT GENRES TO BINARY LATER

class ITunesLibrary(object):
    """A representation of an ITunes Library"""

    def __init__(self):
        """Initializes an empty ITunes Library."""
        self.albums = {}
        self.tracks = {}
        self.artists = {}
        self.genres = [None]

    def add_artist(self, artist):
        """Add an artist to this library.

        Args:
            artist (Artist): an ITunes artist
        """
        self.artists[artist.name] = artist

    def add_album(self, album_key, album):
        """Add an album to this library.

        Args:
            album_key (tuple): album identifier of name, year
            album (Album): an ITunes album
        """
        self.albums[album_key] = album

    def add_track(self, track):
        """Add a track to this library.

        Args:
            track (ITunesTrack): an ITunes track
        """
        self.tracks[track.id] = track

    def get_genre(self, genre_key):
        """Retrieve the genre name by its key.

        Args:
            genre (int): genre key

        Returns:
            the genre represented by the key
        """
        return self.genres[genre_key]


    def get_genre_key(self, genre):
        """Retrieve the genre key, adding the genre if there is none.

        Args:
            genre (str): genre string to be translated to an enum key

        Returns:
            an int representing the genre in the library
        """
        if genre in self.genres:
            return self.genres.index(genre)
        else:
            genre_key = len(self.genres)
            self.genres.append(genre)
            return genre_key

    def remove_duplicates(self):
        """Merge duplicate tracks into one and remove extraneous.

        Preference will be given to merge the duplicate track info onto the album
        with the most tracks, then the most recent.

        Updated track will have sum of play counts and average of ratings.
        """
        # { track_identifier : [track_id] }
        identifier_to_index = {}
        # { track_identifier }
        duplicate_identifiers = set()
        # { track_identifier : (track_id, plays, rating) }
        # the track we'll merge onto, and the merged plays/rating
        merged_tracks = {}

        for track_id, track in self.tracks.iteritems():
            track_ident = track.get_track_identifier()
            if track_ident in identifier_to_index:
                duplicate_identifiers.add(track_ident)
                identifier_to_index[track_ident].append(track_id)
            else:
                identifier_to_index[track_ident] = [track_id]

        for duplicate_identifier in duplicate_identifiers:
            logger.info('Identified duplicate track {dup}.'.format(dup=duplicate_identifier))
            duplicate_indexes = identifier_to_index[duplicate_identifier]
            duplicate_tracks = [self.tracks[track_id] for track_id in duplicate_indexes]
            plays = 0
            sum_rating = 0
            dup_count = 0.
            album_preference = []
            for track in duplicate_tracks:

                # if ths is the first one, we'll start with a preference for this album
                if not album_preference:
                    album_preference = [track.id, track.album_id,
                            len(self.albums[track.album_id].tracks)]
                # else, first let's make sure the dup track is from a different album
                elif not track.album_id == album_preference[1]:
                    # preference is given to the greater year, so check the diff
                    try:
                        year_diff = track.album_id[1] - album_preference[1][1]
                    except TypeError:
                        import ipdb; ipdb.set_trace()
                    # years are the same, so fallback to the number of tracks in the album
                    if year_diff == 0:
                        tracks_in_album = len(self.albums[track.album_id].tracks)
                        if tracks_in_album > album_preference[2]:
                            album_preference = [track.id, track.album_id, tracks_in_album]
                    # this track's year is more recent, so prefer this album
                    elif year_diff > 0:
                        album_preference = [track.id, track.album_id, tracks_in_album]

                plays += track.plays
                if track.rating is not None:
                    sum_rating += track.rating
                    dup_count += 1

            rating = sum_rating / dup_count if dup_count else None

            merged_tracks[duplicate_identifier] = (album_preference[0], plays, rating)

        removed_track_count = 0
        removed_album_count = 0
        removed_artist_count = 0

        # remove the tracks whose info we merged
        for duplicate_identifier, merged_info in merged_tracks.iteritems():
            duplicates = identifier_to_index[duplicate_identifier]
            duplicates.remove(merged_info[0])

            # merge the dup info onto the desired track
            merged = self.tracks[merged_info[0]]
            merged.set_plays(merged_info[1])
            merged.set_rating(merged_info[2])

            for duplicate_id in duplicates:
                # remove the duplicate tracks from their albums
                album_id = self.tracks[duplicate_id].album_id
                del self.tracks[duplicate_id]
                removed_track_count += 1

                album = self.albums[album_id]
                album.tracks.remove(duplicate_id)
                # if removing a track from an album leaves it empty, delete the album
                if not album.tracks:
                    for artist_name in album.artists:
                        if artist_name in self.artists:
                            albums = self.artists[artist_name].albums
                            if album_id in albums:
                                albums.remove(album_id)
                                # if deleting an album leaves an artist empty, delete the artist
                                if not albums:
                                    del self.artists[artist_name]
                                    removed_artist_count += 1

                    del self.albums[album_id]
                    removed_album_count += 1

        if removed_track_count > 0:
            logger.info(('Removed {lost_track} duplicate tracks, which resulted in removing ' +
                         '{lost_album} albums and {lost_artist} artists. {kept_track} tracks, ' +
                         '{kept_album} albums, and {kept_artist} artists remain.')
                         .format(lost_track=removed_track_count,
                                 lost_album=removed_album_count,
                                 lost_artist=removed_artist_count,
                                 kept_track=len(self.tracks),
                                 kept_album=len(self.albums),
                                 kept_artist=len(self.artists)))


class ITunesArtist(object):
    """A representation of an artist."""

    def __init__(self, name):
        """Initialize an artist by name.
        
        Args:
            name (str): artist name
        """
        self.name = name
        self.genres = set()
        self.albums = set()

    def add_album(self, album_id):
        """Associate an album with this artist.

        Args:
            album_id (tuple): album id
        """
        self.albums.add(album_id)

    def add_genre(self, genre):
        """Associate a genre with this artist.

        Args:
            genre (int): genre key
        """
        self.genres.add(genre)

    def __repr__(self):
        return ('({name},{genres},{albums})'
                .format(name=self.name, genres=self.genres, albums=self.albums))


class ITunesAlbum(object):
    """A collection of tracks in an album."""

    def __init__(self, name, year):
        """Create a music album with no tracks.

        Args:
            name (str): album name
            year (int): album year
        """
        self.name = name
        self.year = year

        self.tracks = set()
        self.artists = set()

    def add_track(self, track):
        """Add a track to the music album, updating album artists as necessary.

        Args:
            track (ITunesTrack): iTunes track parsed from library XML
        """
        self.tracks.add(track.id)
        self.artists.update(track.artists)

    def __repr__(self):
        return ('({name},{year},{track_count})'
                .format(name=self.name, year=self.year, track_count=len(self.tracks)))


class ITunesTrack(Track):
    """Representation of an iTunes library music track."""

    def __init__(self, id, name, artists):
        """Create a base music track.

        Sets the id, name, and artist as given.
        If there are multiple or featured artists they will be combined in a set.
        Defaults rating to None and plays to 0.

        Args:
            id (str): unique track id
            name (str): track name
            artists (str): track artists

        """
        feat_artists = FEAT_PATTERN.match(name)
        name = SUB_FEAT_PAT.sub('', name)
        artists = re.split(MULT_PATTERN, artists)

        self.main_artist = artists[0]
        artists = set(artists)

        if feat_artists:
            feat_artists = re.split(MULT_PATTERN, feat_artists.group('artist').strip())
            artists.update(feat_artists)

        super(ITunesTrack, self).__init__(int(id), name, list(artists))

    def print_verbose(self):
        """Creates a verbose string representation.
        
        Returns:
            a verbose string representation of the track attributes
        """
        rstr = 'Track ID:\t{id}\n'.format(id=self.id)
        rstr += 'Name:\t\t{name}\n'.format(name=self.name)
        rstr += 'Artists:\t\t{artist}\n'.format(artist=','.join(self.artists))
        rstr += 'Genre:\t\t{genre}\n'.format(genre=self.genre)
        rstr += 'Track Number:\t{track_number}\n'.format(track_number=self.track_number)
        rstr += 'Rating:\t\t{rating}\n'.format(rating=self.rating)
        rstr += 'Play Count:\t{plays}\n'.format(plays=self.plays)

        return rstr

    def __repr__(self):
        rstr = ('({id},{name},({artists}),{track_number},{genre},{rating},{plays})'
                .format(id=self.id, name=self.name, artists=','.join(self.artists),
                        track_number=self.track_number, genre=self.genre,
                        rating=self.rating, plays=self.plays))
        return rstr
