#!/usr/bin/python
'''tests itunes library xml parser'''
from __future__ import absolute_import, print_function

import os
import unittest

from muslytics import ITunesXMLParser as ixml

class TestITunesXMLParser(unittest.TestCase):

    def setUp(self):
        sample_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   'sample_lib.xml')
        self.albums = ixml.extract_albums(sample_path)

    def test_extracted_albums(self):
        self.assertEqual(len(self.albums), 10)

    def test_merged_tracks(self):
        self.assertEqual(sum(len(album.tracks) for album in self.albums.values()), 12)

        album_key = ('1989', 2014)
        self.assertIn(album_key, self.albums)
        album = self.albums[album_key]
        self.assertEqual(len(album.tracks), 2)

        ootws = filter(lambda track: track.name == 'Out of the Woods', album.tracks)
        self.assertEqual(len(ootws), 1)

        ootw = ootws[0]
        self.assertIn('Taylor Swift', ootw.artists)
        self.assertIn('Taylor Swift', album.artists)
        self.assertEqual(ootw.genre, 'Pop')
        self.assertEqual(ootw.plays, 3000)
        self.assertEqual(ootw.rating, 80)

    def test_artists(self):
        album_key = ('The Hamilton Mixtape', 2016)
        self.assertIn(album_key, self.albums)
        album = self.albums[album_key]
        self.assertEqual(len(album.tracks), 2)
        self.assertEqual(len(album.artists), 7)

        album_artists = set()
        for track in album.tracks:
            album_artists.update(track.artists)

        self.assertEqual(len(album_artists - album.artists), 0)
        self.assertEqual(len(album.artists - album_artists), 0)

        album_key = ('Love Me Like You Do', 2015)
        self.assertIn(album_key, self.albums)
        album = self.albums[album_key]
        self.assertEqual(len(album.artists), 2)
        self.assertEqual(len(album.tracks), 1)
        self.assertEqual(len(album.tracks[0].artists), 2)


    def test_album_name(self):
        self.assertIn(('Love Me Like You Do', 2015), self.albums)
        self.assertIn(('Hamilton', 2015), self.albums)
        self.assertIn(('747', 2014), self.albums)
        self.assertIn(('Moana', 2016), self.albums)
        self.assertIn(('Wild Card', 2014), self.albums)


if __name__ == '__main__':
    unittest.main()
