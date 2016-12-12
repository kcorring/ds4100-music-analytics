#!/usr/bin/python
'''general utility classes'''
from __future__ import absolute_import, print_function

import logging
import re

from sqlalchemy import Column, Integer, String, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
logger = logging.getLogger(__name__)

UNKNOWN_GENRE = 0

ALBUM_NAME_PATTERN = re.compile('\s*((\-\s*(Single|EP))|(\(.*Deluxe.*\))|(\[.*Deluxe.*\]))\s*')
MULT_ARTIST_PATTERN = re.compile('\s*[,&]\s*')
FEAT_ARTIST_PATTERN = re.compile('\s*(\(feat\..*\)|\-\s*feat\..*)\s*')

ACOUSTICNESS = 'acousticness'
DANCEABILITY = 'danceability'
DURATION = 'duration_ms'
ENERGY = 'energy'
INSTRUMENTALNESS = 'instrumentalness'
KEY = 'key'
LIVENESS = 'liveness'
LOUDNESS = 'loudness'
MODE = 'mode'
SPEECHINESS = 'speechiness'
TEMPO = 'tempo'
TIME_SIGNATURE = 'time_signature'
VALENCE = 'valence'

AUDIO_FEATURES = [ACOUSTICNESS,
                  DANCEABILITY,
                  DURATION,  # int
                  ENERGY,
                  INSTRUMENTALNESS,
                  KEY,  # int
                  LIVENESS,
                  LOUDNESS,
                  MODE,  # int
                  SPEECHINESS,
                  TEMPO,
                  TIME_SIGNATURE,  # int
                  VALENCE,
                  ]

POPULARITY = 'popularity'

GENRE = 'genre'
LOVED = 'loved'
PLAYS = 'plays'
RATING = 'rating'

OTHER_FEATURES = [GENRE,
                  LOVED,
                  PLAYS,
                  RATING,
                  ]


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


def combine_spotify_itunes_tracks(s_tracks, i_tracks):
    """Combine iTunes and Spotify tracks into tracks that retain info from both.

    Args:
        s_tracks (list(muslytics.SpotifyUtils.SpotifyTrack)): Spotify tracks
        i_tracks (dict(int, muslytics.ITunesUtils.ITunesTrack)): dict of iTunes track ids to their
            tracks

    Returns:
        a list of Track that merges the iTunes and Spotify info
    """
    combined = {}

    for s_track in s_tracks:
        i_track = i_tracks[s_track.i_id]

        track = Track(id=i_track.id,
                      spotify_id=s_track.id,
                      name=s_track.name,
                      artists=','.join(i_track.artists),
                      genre=i_track.genre,
                      plays=i_track.plays,
                      rating=i_track.rating,
                      loved=i_track.loved,
                      popularity=s_track.popularity,
                      acousticness=s_track.acousticness,
                      danceability=s_track.danceability,
                      duration_ms=s_track.duration_ms,
                      energy=s_track.energy,
                      instrumentalness=s_track.instrumentalness,
                      key=s_track.key,
                      liveness=s_track.liveness,
                      loudness=s_track.loudness,
                      mode=s_track.mode,
                      speechiness=s_track.speechiness,
                      tempo=s_track.tempo,
                      time_signature=s_track.time_signature,
                      valence=s_track.valence,
                      year=i_track.year)

        combined[i_track.id] = track

    logger.info('Combined {tracks} tracks.'.format(tracks=len(combined)))

    return combined.values()


class AbstractTrack(object):
    """Abstract representation of a track."""

    def __init__(self, id, name):
        """Base track representation.

        Args:
            id (int/str): track id
            name (str): track name
        """
        self.id = id
        self.name = name


class Track(Base):
    """ORM representation of a track."""
    __tablename__ = 'tracks'

    id = Column(Integer, primary_key=True)
    spotify_id = Column(String(255))
    name = Column(String(255))
    artists = Column(String(255))
    genre = Column(String(255))
    plays = Column(Integer)
    rating = Column(Float)
    loved = Column(Boolean)
    popularity = Column(Integer)
    acousticness = Column(Float)
    danceability = Column(Float)
    duration_ms = Column(Integer)
    energy = Column(Float)
    instrumentalness = Column(Float)
    key = Column(Integer)
    liveness = Column(Float)
    loudness = Column(Float)
    mode = Column(Integer)
    speechiness = Column(Float)
    tempo = Column(Float)
    time_signature = Column(Integer)
    valence = Column(Float)
    year = Column(Integer)

    def __repr__(self):
        return ('<Track(id={id}, spotify_id={s_id}, name={name}, plays={plays}, loved={loved}, ' +
                'artists={artists}, genre={genre}, popularity={popularity}, ' +
                'acousticness={acousticness}, danceability={danceability}, ' +
                'year={year}, duration_ms={duration_ms}, energy={energy}, ' +
                'instrumentalness={instrumentalness}, key={key}, liveness={liveness}, ' +
                'mode={mode}, speechiness={speechiness}, tempo={tempo}, ' +
                'time_signature={time_signature}, valence={valence})>'
                .format(id=self.id, s_id=self.spotify_id, name=self.name, plays=self.plays,
                        loved=self.loved, popularity=self.played, acousticness=self.acousticness,
                        danceability=self.danceability, duration_ms=self.duration_ms,
                        energy=self.energy, instrumentalness=self.instrumentalness, key=self.key,
                        year=self.year, genre=self.genre, liveness=self.liveness, mode=self.mode,
                        artists=self.artists, speechiness=self.speechiness, tempo=self.tempo,
                        time_signature=self.time_signature, valence=self.valence))
