#!/usr/bin/python
'''database utility classes'''
from __future__ import absolute_import, print_function

import argparse
import getpass
import logging

from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from muslytics.SpotifyTrackFinder import unpickle_spotify

Base = declarative_base()
Session = sessionmaker()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def connect(user, password, host, database):
    engine = create_engine('mysql://{user}:{password}@{host}/{database}'
                           .format(user=user, password=password, host=host, database=database))
    Session.configure(bind=engine)
    return engine


def insert_tracks_into_table(db, track_file):
    Base.metadata.create_all(db)
    session = Session()

    orm_tracks = [Track(id=track.other_id,
                        spotify_id=track.id,
                        name=track.name,
                        plays=track.plays,
                        rating=track.rating,
                        loved=track.loved,
                        genre=track.genre,
                        popularity=track.popularity,
                        acousticness=track.acousticness,
                        danceability=track.danceability,
                        duration=track.duration_ms,
                        energy=track.energy,
                        instrumentalness=track.instrumentalness,
                        key=track.key,
                        liveness=track.liveness,
                        loudness=track.loudness,
                        mode=track.mode,
                        speechiness=track.speechiness,
                        tempo=track.tempo,
                        time_signature=track.time_signature,
                        valence=track.valence,
                        )
                 for track in unpickle_spotify(track_file)]

    session.add_all(orm_tracks)
    session.commit()

    return session


class Track(Base):
    __tablename__ = 'tracks'

    id = Column(Integer, primary_key=True)
    spotify_id = Column(String(255))
    name = Column(String(255))
    genre = Column(String(255))
    plays = Column(Integer)
    rating = Column(Float)
    loved = Column(Boolean)
    popularity = Column(Integer)
    acousticness = Column(Float)
    danceability = Column(Float)
    duration = Column(Integer)
    energy = Column(Float)
    instrumentalness = Column(Float)
    key = Column(Integer)
    liveness = Column(Float)
    loudness = Column(Float)
    mode = Column(Integer)
    speechiness = Column(Float)
    tempo = Column(Float)
    time_signature = Column(Integer)
    valence = Column(Float)

    def __repr__(self):
        return ('<Track(id={id}, spotify_id={s_id}, name={name}, plays={plays}, loved={loved}, ' +
                'genre={genre}, popularity={popularity}, acousticness={acousticness}, ' +
                'danceability={danceability}, duration={duration}, energy={energy}, ' +
                'instrumentalness={instrumentalness}, key={key}, liveness={liveness}, ' +
                'mode={mode}, speechiness={speechiness}, tempo={tempo}, ' +
                'time_signature={time_signature}, valence={valence})>'
                .format(id=self.id, s_id=self.spotify_id, name=self.name, plays=self.plays,
                        loved=self.loved, popularity=self.played, acousticness=self.acousticness,
                        danceability=self.danceability, duration=self.duration, energy=self.energy,
                        instrumentalness=self.instrumentalness, key=self.key, genre=self.genre,
                        liveness=self.liveness, mode=self.mode, speechiness=self.speechiness,
                        tempo=self.tempo, time_signature=self.time_signature,
                        valence=self.valence))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', required=True, help='username for connecting to database')
    parser.add_argument('-o', '--host', required=True, help='host for connecting to database')
    parser.add_argument('-d', '--database', required=True, help='database name')
    parser.add_argument('tracks', help='path to pickled tracks file')
    args = parser.parse_args()
    
    password = getpass.getpass()

    db = connect(args.user, password, args.host, args.database)
    insert_tracks_into_table(db, args.tracks)
