from flask import Flask, request, Response, jsonify, make_response;
from configuration import Configuration;
from models import database, Participant, Election, ElectionParticipant, Vote;
from email.utils import parseaddr;
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, get_jwt_identity;
from sqlalchemy import or_, and_, func;
from flask_jwt_extended import JWTManager;
from datetime import datetime, timedelta;
from dateutil import parser;
from datetime import timezone;
import io;
import csv;
from redis import Redis;
import pytz;


application = Flask ( __name__ );
application.config.from_object ( Configuration );
jwt = JWTManager ( application );


@application.route("/", methods = ["GET"])
def index():
    return "Hello dameon!"

def main(vote):
    splitData = vote.split(",");
    utc = pytz.UTC;

    elections = Election.query.all();
    dateNow = parser.isoparse(datetime.now().isoformat())
    hours_to_add = timedelta(hours=2);
    dateNow = dateNow + hours_to_add;


    electionsOngoing = False;
    electionId = -1;

    for election in elections:
        startDate = parser.isoparse(election.start);
        endDate = parser.isoparse(election.end);

        if( dateNow > startDate and dateNow < endDate):
            electionsOngoing = True;
            electionId = election.id
            break;

    if(electionsOngoing == False):
        print("No elections")
        return;

    votee = Vote.query.filter( Vote.guid == splitData[0] ).first()

    if votee:
        newVote = Vote(guid = splitData[0], jmbg = splitData[2], electionId = electionId, candidate = int(splitData[1]), valid = False,
                       reason = "Duplicate ballot.");

        database.session.add( newVote );
        database.session.commit();

    else:
        numOfParticipants = 0;
        election = Election.query.filter( Election.id == electionId ).first();

        for participant in election.participants:
            numOfParticipants += 1;

        candidate = int(splitData[1]);
        if candidate > numOfParticipants:
            newVote = Vote(guid=splitData[0], jmbg=splitData[2], electionId=electionId, candidate=candidate,
                           valid=False,
                           reason="Invalid poll number.");

            database.session.add(newVote);
            database.session.commit();

        else:
            newVote = Vote(guid=splitData[0], jmbg=splitData[2], electionId=electionId, candidate=candidate, valid=True);

            database.session.add(newVote);
            database.session.commit();


if ( __name__ == "__main__" ):
    database.init_app ( application );

    with application.app_context():
        while True:
            with Redis( host = "redis") as redis:
                _, message = redis.blpop("votes")
                message = message.decode("utf-8")
                main(message)