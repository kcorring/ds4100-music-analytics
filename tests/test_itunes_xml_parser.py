#!/usr/bin/python
'''tests itunes library xml parser'''
from __future__ import absolute_import, print_function

import unittest

from muslytics import ITunesXMLParser as ixml

class TestITunesXMLParser(unittest.TestCase):

    def setUp(self):
        self.tracks = ixml.extract_tracks('sample_lib.xml')
        pass

    def test_extracted_tracks(self):
        self.assertEqual(len(self.tracks), 8)

        ootws = filter(lambda track: track.name == 'Out of the Woods', self.tracks)
        self.assertEqual(len(ootws), 2)

        ootw = ootws[0]
        self.assertEqual(ootw.artist, 'Taylor Swift')
        self.assertEqual(ootw.album, '1989')
        self.assertEqual(ootw.album_artist, 'Taylor Swift')
        self.assertEqual(ootw.year, 2014)
        self.assertEqual(ootw.genre, 'Pop')

        play_counts = map(lambda track: track.plays, ootws)
        self.assertIn(2906, play_counts)
        self.assertIn(94, play_counts)

        ratings = map(lambda track: track.rating, ootws)
        self.assertIn(60, ratings)
        self.assertIn(100, ratings)

        ids = map(lambda track: track.id, ootws)
        self.assertIn(5888, ids)
        self.assertIn(7830, ids)


    def test_merged_tracks(self):
        ixml.merge_duplicates(self.tracks)

        self.assertEqual(len(self.tracks), 7)

        ootws = filter(lambda track: track.name == 'Out of the Woods', self.tracks)
        self.assertEqual(len(ootws), 1)

        ootw = ootws[0]
        self.assertEqual(ootw.artist, 'Taylor Swift')
        self.assertEqual(ootw.album, '1989')
        self.assertEqual(ootw.album_artist, 'Taylor Swift')
        self.assertEqual(ootw.year, 2014)
        self.assertEqual(ootw.genre, 'Pop')
        self.assertEqual(ootw.plays, 3000)
        self.assertEqual(ootw.rating, 80)


if __name__ == '__main__':
    unittest.main()
