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

    def setUp(self):
        sample_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                   'sample_lib.p')
        self.ilibrary = unpickle_library(sample_path)

    def test_get_tracks(self):
        """Test track retrieval from Spotify."""

        results = spf.get_spotify_tracks(self.ilibrary)

        # Taylor Swift doesn't have her albums on Spotify
        expected_missing = [track_id for track_id, track in self.ilibrary.tracks.iteritems()
                            if track.artists[0] == 'Taylor Swift']

        for missing_id in expected_missing:
            self.assertNotIn(missing_id, results)

        # 5037: Pop 101 (feat. Anami Vice) by Marianas Trench
        self.assertEqual(results[5037][0], '2fGFaTDbE8aS4f31fM0XE4')

        # 8755 : Satisfied (feat. Miguel & Queen Latifah) by Sia
        self.assertEqual(results[8755][0], '1ybJ2itxCxPCPkcA9sOgTO')

        # 6699 : Un Besito Mas (feat. Juan Luis Guerra) by Jesse & Joy
        self.assertEqual(results[6699][0], '1182pxG4uNxr3QqIH8b8k0')


if __name__ == '__main__':
    unittest.main()
