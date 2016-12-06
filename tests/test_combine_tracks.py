#!/usr/bin/python
'''tests track merging'''
from __future__ import absolute_import, print_function

import logging
import os
import unittest

from muslytics.ITunesXMLParser import unpickle_library
from muslytics.SpotifyTrackFinder import unpickle_spotify
from muslytics.Utils import combine_spotify_itunes_tracks

logging.disable(logging.CRITICAL)


class TestCombineTracks(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        i_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                              'sample_itunes_tracks.p')
        s_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                              'sample_spotify_tracks.p')
        i_tracks = unpickle_library(i_path).tracks
        s_tracks = unpickle_spotify(s_path)
        cls.tracks = combine_spotify_itunes_tracks(s_tracks, i_tracks)

    def test_merge(self):
        """Test that merged Spotify/ITunes tracks retained correct info from each."""
        # 1mrtws7od1a1q2j2diejhL, 6031: Love Me Like You Do by Madilyn Bailey & MAX
        for track in self.tracks:
            if track.id == 6031:
                break

        self.assertEqual(track.spotify_id, '1MRtWS7od1A1Q2j2DiEjhL')
        self.assertEqual(track.name, 'Love Me Like You Do')
        self.assertEqual(track.rating, 100)
        self.assertFalse(track.loved)
        self.assertEqual(track.acousticness, 0.821)
        self.assertEqual(track.duration_ms, 191250)


if __name__ == '__main__':
    unittest.main()
