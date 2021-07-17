from flask import Flask, request, Response, jsonify, make_response;
from configuration import Configuration;
from models import database, Participant, Election, ElectionParticipant, Vote;
from userDecorator import roleCheck;
from email.utils import parseaddr;
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, get_jwt_identity;
from sqlalchemy import or_, and_, func;
from flask_jwt_extended import JWTManager, get_jwt;
from datetime import datetime;
from dateutil import parser;
import io;
import csv;
from redis import Redis;


application = Flask ( __name__ );
application.config.from_object ( Configuration );
jwt = JWTManager ( application );


@application.route("/", methods = ["GET"])
def index():
    return "Hello user!"

@application.route("/vote", methods = ["POST"])
@roleCheck( role = 2 )
def vote():
    content = request.files.get("file", "")
    if content == "":
        return make_response(jsonify(message="Field file is missing."), 400);
    content = content.stream.read().decode("utf-8");
    stream = io.StringIO(content);
    reader = csv.reader(stream);

    votes = [];
    i = 0;

    for row in reader:

        if( len( row ) != 2):
            return make_response(jsonify(message="Incorrect number of values on line " + str(i) + "." ), 400);
        try:
            vote = int(row[1]);
        except:
            return make_response(jsonify(message="Incorrect poll number on line " + str(i) + "."), 400);

        if( int( row[1] ) <= 0):
            return make_response(jsonify(message="Incorrect poll number on line " + str(i) + "."), 400);

        i = i + 1
        votes.append( (row[0], row[1]) )

    claims = get_jwt();
    jmbg = claims["jmbg"];

    with Redis ( host = "redis" ) as redis:
        for vote in votes:
            redis.rpush ( "votes", str(vote[0]) + "," + str(vote[1]) + "," + str(jmbg) );

    return Response( status = 200);


if ( __name__ == "__main__" ):
    database.init_app ( application );
    application.run ( debug = True, host = "0.0.0.0", port = 5002);