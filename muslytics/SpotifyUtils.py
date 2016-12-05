#!/usr/bin/python
'''spotify utility classes'''
from __future__ import absolute_import, print_function

import logging
import re

from muslytics.Utils import Track, AUDIO_FEATURES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpotifyTrack(Track):
    """Representation of an Spotify music track."""

    def __init__(self, spotify_id, itunes_id, name):
        """Create a base Spotify track.

        Initializes the following fields to None. Descriptions from Spotify API
        Endpoint Reference:
        - acousticness: confidence measure from 0.0-1.0 on whether track is acoustic (high
          confidence for acousticness is 1.0)
        - danceability: how suitable the track is for dancing (0.0-1.0, 1.0 is most danceable)
        - duration_ms: duration of track in milliseconds
        - energy: perceptual measure of intensity and activity (0.0-1.0, 1.0 is most energy)
        - instrumentalness: whether the track contains vocals (0.0-1.0, 1.0 is most instrumental)
        - key: key track is in, standard pitch class int mapping used
        - liveness: presence of an audience during the recording (0.0-1.0, 0.8+ is strong
          likelihood that track is live)
        - loudness: overall loudness of track in decibels (-60.0-0.0)
        - mode: modality of track; 1 for major, 0 for minor
        - speechiness: presence of spoken words in track (0.0-1.0, closer to 1.0 indicates more
          speech-like)
        - tempo: overall estimated tempo in bpm (float)
        - time_signature: estimated overall time signature, how many beats per measure
        - valence: musical positiveness conveyed by track (0.0-1.0, closer to 1.0 is more positive)

        Additionally, will set track popularity to None (an attribute that comes from the track
        itself rather than the track's audio features)

        Args:
            spotify_id (str): unique identifier for track on Spotify
            itunes_id (int): unique identifier for track in iTunes
                library.
            name (str): track name
        """
        self.i_id = itunes_id
        self.popularity = None

        self._features = {feature: None for feature in AUDIO_FEATURES}

        super(SpotifyTrack, self).__init__(spotify_id, name)

    def __getattr__(self, attr):
        if attr not in AUDIO_FEATURES:
            raise AttributeError('{cls} has no attribute {attr}'.format(cls=self.__class__,
                                                                        attr=attr))
        else:
            return self._features[attr]

    def __setattr__(self, attr_name, attr_value):
        if attr_name in ['id', 'i_id', 'name', 'popularity', '_features']:
            super(SpotifyTrack, self).__setattr__(attr_name, attr_value)
        else:
            if attr_name in self._features:
                self._features[attr_name] = attr_value
            else:
                raise AttributeError('{cls} has no attribute {attr}'.format(cls=self.__class__,
                                                                            attr=attr))

    def __repr__(self):
        return '({name}, ({s_id}, {i_id}), {features})'.format(name=self.name,
                                                               s_id=self.id,
                                                               i_id=self.i_id,
                                                               features=self._features.__repr__())

