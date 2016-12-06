#!/usr/bin/python
'''tests spotify track finder'''
from __future__ import absolute_import, print_function

import logging
import os
import unittest
from sqlalchemy.sql import func

from muslytics.muslytics_pipeline import unpickler
from muslytics.Utils import Track
from muslytics.DatabaseUtils import connect, insert_tracks_into_table

logging.disable(logging.CRITICAL)

'''
CREATE DATABASE test_muslytics;
CREATE USER 'test_user'@'localhost' IDENTIFIED BY 'test_password';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP
    ON test_muslytics.tracks
    TO 'test_user'@'localhost';
'''

USER = 'test_user'
PASSWORD = 'test_password'
HOST = 'localhost'
DATABASE = 'test_muslytics'


class TestDatabaseUtils(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        sample_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                   'sample_merged_tracks.p')
        cls.db = connect(USER, PASSWORD, HOST, DATABASE)
        Track.__table__.drop(cls.db, checkfirst=True)
        cls.session = insert_tracks_into_table(cls.db, unpickler(sample_path))

    def test_table_created(self):
        """Test that the table was created."""
        self.assertIn('tracks', self.db.table_names())

    def test_rows_created(self):
        """Test that the correct number of rows were added."""
        self.assertEqual(self.session.query(Track).count(), 15)

    def test_row_content(self):
        """Test that miscellaneous attributes and aggregates are as expected."""
        self.assertAlmostEqual(self.session.query(func.max(Track.loudness)).first()[0],
                               -2.964, places=3)
        self.assertEqual(self.session.query(func.min(Track.duration_ms)).first()[0], 175507)
        self.assertAlmostEqual(self.session.query(Track.rating).filter_by(id=6031).first()[0],
                               100, places=0)
        self.assertEqual(self.session.query(Track.plays).filter_by(id=5219).first()[0],
                         12012)
        self.assertEqual(self.session.query(Track.name).filter_by(id=8755).first()[0],
                         'Satisfied')


if __name__ == '__main__':
    unittest.main()
