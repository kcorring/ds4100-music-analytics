#!/usr/bin/python
'''database utility classes'''
from __future__ import absolute_import, print_function

import argparse
import getpass
import logging

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from muslytics import configure_logging
from muslytics.SpotifyTrackFinder import unpickle_spotify
from muslytics.Utils import Base, Track

logger = logging.getLogger(__name__)

Session = sessionmaker()


def connect(user, password, host, database):
    """Connect to a database.

    Args:
        user (str): username
        password (str): password
        host (str): host
        database (str): database name

    Returns:
        a sqlalchemy engine for database processing
    """
    engine = create_engine('mysql://{user}:{password}@{host}/{database}'
                           .format(user=user, password=password, host=host, database=database))
    Session.configure(bind=engine)
    logger.info('Successfully connected to {host}/{database} as {user}'
                .format(host=host, database=database, user=user))
    return engine


def insert_tracks_into_table(db, tracks):
    """Insert the given tracks into a database table.

    Args:
        db (sqlalchemy engine): database engine
        tracks (list(muslytics.Utils.Track)): tracks to be entered into the database

    Returns:
        the database session in which the tracks were committed
    """
    Track.__table__.drop(db, checkfirst=True)
    Base.metadata.create_all(db)
    session = Session()
    session.add_all(tracks)
    session.commit()

    logger.info('Successfully inserted {num} tracks to tracks table in database.'
                .format(num=session.query(Track).count()))
    return session


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', required=True, help='username for connecting to database')
    parser.add_argument('-o', '--host', required=True, help='host for connecting to database')
    parser.add_argument('-d', '--database', required=True, help='database name')
    parser.add_argument('-v', '--verbose', action='store_true', help='increase output verbosity')
    parser.add_argument('-l', '--log', required=False, help='log to the given file')
    parser.add_argument('tracks', help='path to pickled tracks file')
    args = parser.parse_args()

    configure_logging(args.verbose, args.log)
    
    password = getpass.getpass()

    tracks = unpickle_spotify(args.tracks)

    db = connect(args.user, password, args.host, args.database)
    insert_tracks_into_table(db, tracks)
