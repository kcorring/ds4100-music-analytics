#!/usr/bin/python
'''tests spotify track finder'''
from __future__ import absolute_import, print_function

import logging
import os
import unittest

from muslytics.ITunesXMLParser import unpickle_library
from muslytics import SpotifyTrackFinder as spf

logging.disable(logging.CRITICAL)


class TestSpotifyTrackFinder(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        sample_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                   'sample_lib.p')
        cls.ilibrary = unpickle_library(sample_path)
        cls.tracks = spf.get_spotify_tracks(cls.ilibrary)

    def test_missing_tracks(self):
        """Test tracks that had no match on Spotify."""

        # Taylor Swift doesn't have her albums on Spotify
        expected_missing = [track_id for track_id, track in self.ilibrary.tracks.iteritems()
                            if track.artists[0] == 'Taylor Swift']

        for missing_id in expected_missing:
            self.assertNotIn(missing_id, [track.other_id for track in self.tracks])

    def test_matching_tracks(self):
        """Test tracks that had a match on Spotify."""

        # 5037: Pop 101 (feat. Anami Vice) by Marianas Trench
        # 8755 : Satisfied (feat. Miguel & Queen Latifah) by Sia
        # 6699 : Un Besito Mas (feat. Juan Luis Guerra) by Jesse & Joy
        targets = {5037: '2fGFaTDbE8aS4f31fM0XE4',
                   8755: '1ybJ2itxCxPCPkcA9sOgTO',
                   6699: '1182pxG4uNxr3QqIH8b8k0',
                   }

        matches = {track.other_id: track.id
                   for track in self.tracks
                   if track.other_id in targets}

        for i_id, s_id in targets.iteritems():
            self.assertEqual(s_id, matches[i_id])

    def test_audio_features(self):
        """Verify correct audio features were retrieved from Spotify."""

        # 1ehPJRt49h6N0LoryqKZXq, 8737: How Far I'll Go (Alessia Cara Version) by Alessia Cara
        # 2fGFaTDbE8aS4f31fM0XE4, 5037: Pop 101 (feat. Anami Vice) by Marianas Trench
        targets = {8737: {'danceability': 0.317,
                          'energy': 0.562,
                          'key': 9,
                          'loudness': -9.609,
                          'mode': 1,
                          'speechiness': 0.395,
                          'acousticness': 0.124,
                          'instrumentalness': 0.000144,
                          'liveness': 0.0667,
                          'valence': 0.127,
                          'tempo': 181.100,
                          'duration_ms': 175507,
                          'time_signature': 4,
                          },
                   5037: {'danceability': 0.756,
                          'energy': 0.658,
                          'key': 11,
                          'loudness': -6.128,
                          'mode': 0,
                          'speechiness': 0.202,
                          'acousticness': 0.0581,
                          'instrumentalness': 0,
                          'liveness': 0.0674,
                          'valence': 0.640,
                          'tempo': 120.018,
                          'duration_ms': 247829,
                          'time_signature': 4,
                          },
                   }

        results = {track.other_id: track for track in self.tracks if track.other_id in targets}

        for target, expecteds in targets.iteritems():
            result = results[target]
            for key, expected in expecteds.iteritems():
                self.assertEqual(result.__getattr__(key), expected)

    def test_merge(self):
        """Test that merged Spotify/ITunes tracks retained correct info from each."""
        # 1MRtWS7od1A1Q2j2DiEjhL, 6031: Love Me Like You Do by Madilyn Bailey & MAX
        for track in self.tracks:
            if track.other_id == 6031:
                break

        self.assertEqual(track.name, 'Love Me Like You Do')
        self.assertEqual(len(track.artists), 2)
        self.assertEqual(track.rating, 100)
        self.assertFalse(track.loved)
        self.assertEqual(track.acousticness, 0.821)
        self.assertEqual(track.duration_ms, 191250)


if __name__ == '__main__':
    unittest.main()
