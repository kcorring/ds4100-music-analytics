#!/usr/bin/python
'''itunes utility classes'''
from __future__ import absolute_import, print_function

import logging
import re

from muslytics.Utils import strip_featured_artists, AbstractTrack, MULT_ARTIST_PATTERN, UNKNOWN_GENRE

logger = logging.getLogger(__name__)

FEAT_GROUP_PATTERN = re.compile('.*\(feat\.(?P<artist>.*)\)\s*')


class ITunesLibrary(object):
    """A representation of an ITunes Library"""

    def __init__(self):
        """Initializes an empty ITunes Library."""
        self.albums = {}
        self.tracks = {}
        self.artists = {}
        self.genres = set()

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
        self._add_genre(track.genre)

    def _add_genre(self, genre):
        """Add the genre to the library

        Args:
            genre (str): genre to be added
        """
        self.genres.add(genre)

    def remove_duplicates(self):
        """Merge duplicate tracks into one and remove extraneous.

        Preference will be given to merge the duplicate track info onto the album
        with the most tracks, then the most recent.

        Updated track will have sum of play counts and average of ratings.
        If any of the duplicates are tagged loved, the merged will retain that.
        """
        # { track_identifier : [track_id] }
        identifier_to_index = {}
        # { track_identifier }
        duplicate_identifiers = set()
        # { track_identifier : (track_id, plays, rating, loved) }
        # the track we'll merge onto, and the merged plays/rating/loved
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
            loved = False
            album_preference = []
            for track in duplicate_tracks:

                # if ths is the first one, we'll start with a preference for this album
                if not album_preference:
                    album_preference = [track.id, track.album_id,
                            len(self.albums[track.album_id].tracks)]
                # else, first let's make sure the dup track is from a different album
                elif not track.album_id == album_preference[1]:
                    # preference is given to the greater year, so check the diff
                    year_diff = track.album_id[1] - album_preference[1][1]
                    # years are the same, so fallback to the number of tracks in the album
                    tracks_in_album = len(self.albums[track.album_id].tracks)
                    if year_diff == 0:
                        if tracks_in_album > album_preference[2]:
                            album_preference = [track.id, track.album_id, tracks_in_album]
                    # this track's year is more recent, so prefer this album
                    elif year_diff > 0:
                        album_preference = [track.id, track.album_id, tracks_in_album]

                loved = loved or track.loved
                plays += track.plays
                if track.rating is not None:
                    sum_rating += track.rating
                    dup_count += 1

            rating = sum_rating / dup_count if dup_count else None

            merged_tracks[duplicate_identifier] = (album_preference[0], plays, rating, loved)

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
            merged.set_loved(merged_info[3])

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

    def __len__(self):
        return len(self.tracks)


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


class ITunesTrack(AbstractTrack):
    """Representation of an iTunes library music track."""

    def __init__(self, id, name, artists, rating):
        """Create a base music track.

        Sets the id, name, artists, rating as given.
        If there are multiple or featured artists they will be combined in a set.
        Defaults plays to 0 and genre to UNKNOWN_GENRE.

        Args:
            id (str): unique track id
            name (str): track name
            artists (str): track artists
            rating (str): track rating

        """
        self.rating = int(rating)
        self.plays = 0

        feat_artists = FEAT_GROUP_PATTERN.match(name)
        artists = re.split(MULT_ARTIST_PATTERN, artists)

        main_artist = artists[0]
        artists = set(artists)

        if feat_artists:
            name = strip_featured_artists(name)
            feat_artists = re.split(MULT_ARTIST_PATTERN, feat_artists.group('artist').strip())
            artists.update(feat_artists)

        if len(artists) > 1:
            artists.remove(main_artist)
            self.artists = list(artists)
            self.artists.insert(0, main_artist)
        else:
            self.artists = [main_artist]

        self.genre = UNKNOWN_GENRE
        self.loved = False
        self.album_id = None

        super(ITunesTrack, self).__init__(int(id), name)

    def set_loved(self, is_loved):
        """Sets whether the track is 'loved' on iTunes.

        Args:
            is_loved (bool): whether the track is loved
        """
        self.loved = is_loved

    def set_genre(self, genre=UNKNOWN_GENRE):
        """Set the track genre.

        Args:
            genre (int): track genre, defaults to UNKNOWN_GENRE
        """
        self.genre = genre

    def set_rating(self, rating=0):
        """Set the track rating.

        Args:
            rating (int): track rating, defaults to 0
        """
        self.rating = rating

    def set_plays(self, plays=0):
        """Set the track play count.

        Args:
            plays (str): track play count, defaults to 0
        """
        self.plays = int(plays)

    def set_album_id(self, album_id):
        """Set the album id.

        Args:
            album_id (tuple): unique album identifier
        """
        self.album_id = album_id

    def get_track_identifier(self):
        """Retrieves a track identifier in the form of its name and artists.

        Intended to be used for identifying duplicate tracks within the same album.

        Returns:
            tuple of track name, artists
        """
        return (self.name, ','.join(self.artists))

    def print_verbose(self):
        """Creates a verbose string representation.
        
        Returns:
            a verbose string representation of the track attributes
        """
        rstr = 'Track ID:\t{id}\n'.format(id=self.id)
        rstr += 'Name:\t\t{name}\n'.format(name=self.name)
        rstr += 'Artists:\t\t{artist}\n'.format(artist=','.join(self.artists))
        rstr += 'Genre:\t\t{genre}\n'.format(genre=self.genre)
        rstr += 'Rating:\t\t{rating}\n'.format(rating=self.rating)
        rstr += 'Loved:\t\t{loved}\n'.format(loved=self.loved)
        rstr += 'Play Count:\t{plays}\n'.format(plays=self.plays)

        return rstr

    def __repr__(self):
        rstr = ('({id},{name},({artists}),{genre},{rating},{loved},{plays})'
                .format(id=self.id, name=self.name, artists=','.join(self.artists),
                        genre=self.genre, rating=self.rating, loved=self.loved, plays=self.plays))
        return rstr
