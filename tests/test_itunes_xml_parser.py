#!/usr/bin/python
'''tests itunes library xml parser'''
from __future__ import absolute_import, print_function

import logging
import os
import unittest

from muslytics import ITunesXMLParser as ixml

logging.disable(logging.CRITICAL)


class TestITunesXMLParser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sample_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                        'sample_lib.xml')
        cls.library = ixml.extract_library(cls.sample_path)

    def test_extracted_library(self):
        """Verify that extraction works."""
        library = ixml.extract_library(self.sample_path, remove_duplicates=False)
        self.assertEqual(len(library.albums), 14)
        self.assertEqual(len(library.tracks), 19)
        self.assertEqual(len(library.artists), 14)
        self.assertEqual(len(library.genres), 7)

    def _test_merged_track(self, album_key, tracks_in_album, track_name, artist,
            genre, plays, rating, loved):
        """Helper to verify an individual track."""
        self.assertIn(album_key, self.library.albums)
        album = self.library.albums[album_key]
        self.assertEqual(len(album.tracks), tracks_in_album)

        tracks = [self.library.tracks[track_id]
                  for track_id in album.tracks
                  if self.library.tracks[track_id].name == track_name]
        self.assertEqual(len(tracks), 1)

        track = tracks[0]
        self.assertIn(artist, track.artists)
        self.assertIn(artist, album.artists)
        self.assertEqual(track.genre, genre)
        self.assertEqual(track.plays, plays)
        self.assertEqual(track.rating, rating)
        self.assertEqual(track.loved, loved)

    def test_merged_tracks(self):
        """Verify that duplicates are merged/removed properly."""
        self.assertEqual(len(self.library.albums), 13)
        self.assertEqual(len(self.library.tracks), 17)

        self._test_merged_track(('1989', 2014), 2, 'Out of the Woods', 'Taylor Swift',
                'pop', 3000, 5, True)
        self._test_merged_track(('Meat and Candy', 2015), 2, 'Break Up with Him', 'Old Dominion',
                'country', 100, 4, True)

    def test_artists(self):
        """Verify that multiple artists are split correctly."""
        album_key = ('The Hamilton Mixtape', 2016)
        self.assertIn(album_key, self.library.albums)
        album = self.library.albums[album_key]
        self.assertEqual(len(album.tracks), 2)
        self.assertEqual(len(album.artists), 7)

        album_artists = set()
        for track_id in album.tracks:
            album_artists.update(self.library.tracks[track_id].artists)

        self.assertTrue(album_artists.issuperset(album.artists) and
                album_artists.issubset(album.artists))

        album_key = ('Love Me Like You Do', 2015)
        self.assertIn(album_key, self.library.albums)
        album = self.library.albums[album_key]
        self.assertEqual(len(album.artists), 2)
        self.assertEqual(len(album.tracks), 1)
        self.assertEqual(sum(len(self.library.tracks[track_id].artists)
                              for track_id in album.tracks), 2)

    def test_album_name(self):
        """Verify that regex for stripping parenthetical Deluxe, - Single, and - EP works."""
        self.assertIn(('Love Me Like You Do', 2015), self.library.albums)
        self.assertIn(('Hamilton (Original Broadway Cast Recording)', 2015), self.library.albums)
        self.assertIn(('747', 2014), self.library.albums)
        self.assertIn(('Moana (Original Motion Picture Soundtrack)', 2016), self.library.albums)
        self.assertIn(('Wild Card', 2014), self.library.albums)

        self.assertIn('Halsey', self.library.artists)
        self.assertEqual(len(self.library.artists['Halsey'].albums), 1)
        self.assertIn(('BADLANDS', 2015), self.library.artists['Halsey'].albums)


if __name__ == '__main__':
    unittest.main()
