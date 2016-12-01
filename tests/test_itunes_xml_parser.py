#!/usr/bin/python
'''tests itunes library xml parser'''
from __future__ import absolute_import, print_function

import unittest

from muslytics import ITunesXMLParser as ixml

class TestITunesXMLParser(unittest.TestCase):

    def setUp(self):
        pass

    def test_extracted_and_merged_albums(self):
        albums = ixml.extract_albums('sample_lib.xml')

        self.assertEqual(len(albums), 6)
        self.assertEqual(sum(len(album.tracks) for album in albums.values()), 8)

        album_key = ('1989', 2014, 'Pop')
        self.assertIn(album_key, albums)
        album = albums[album_key]
        self.assertEqual(len(album.tracks), 3)

        ootws = filter(lambda track: track.name == 'Out of the Woods', album.tracks)
        self.assertEqual(len(ootws), 2)

        ootw = ootws[0]
        self.assertEqual(ootw.artist, 'Taylor Swift')

        play_counts = map(lambda track: track.plays, ootws)
        self.assertIn(2906, play_counts)
        self.assertIn(94, play_counts)

        ratings = map(lambda track: track.rating, ootws)
        self.assertIn(60, ratings)
        self.assertIn(100, ratings)

        ids = map(lambda track: track.id, ootws)
        self.assertIn(5888, ids)
        self.assertIn(7830, ids)

        for a in albums.values():
            a.merge_duplicates()

        self.assertEqual(sum(len(a.tracks) for a in albums.values()), 7)
        self.assertEqual(len(album.tracks), 2)

        ootws = filter(lambda track: track.name == 'Out of the Woods', album.tracks)
        self.assertEqual(len(ootws), 1)

        ootw = ootws[0]
        self.assertEqual(ootw.artist, 'Taylor Swift')
        self.assertEqual(ootw.plays, 3000)
        self.assertEqual(ootw.rating, 80)


if __name__ == '__main__':
    unittest.main()
