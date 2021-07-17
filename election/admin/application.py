from flask import Flask, request, Response, jsonify, make_response;
from configuration import Configuration;
from models import database, Participant, Election, ElectionParticipant, Vote;
from adminDecorator import roleCheck;
from email.utils import parseaddr;
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, get_jwt_identity;
from sqlalchemy import or_, and_, func;
from flask_jwt_extended import JWTManager;
from datetime import datetime, timedelta;
from dateutil import parser;
import pytz;



application = Flask ( __name__ );
application.config.from_object ( Configuration );
jwt = JWTManager ( application );


@application.route("/", methods = ["GET"])
def index():
    return "Hello admin!"

@application.route("/createParticipant", methods = ["POST"])
@roleCheck( role = 1 )
def createParticipant():
    name = request.json.get("name", "");
    individual = request.json.get("individual", "");

    nameEmpty = len(name) == 0;
    individualEmpty = len( str ( individual ) ) == 0;

    if (nameEmpty):
        return make_response(jsonify(message="Field name is missing."), 400);
    if (individualEmpty):
        return make_response(jsonify(message="Field individual is missing."), 400);

    type = "individual";
    if(individual == False):
        type = "party";

    participant = Participant(name = name, type = type);
    database.session.add(participant);
    database.session.commit();

    return make_response( jsonify( id = participant.id ), 200);

@application.route("/getParticipants", methods = ["GET"])
@roleCheck( role = 1 )
def getParticipants():

    participants = Participant.query.all ( );

    newParticipants = []
    newParticipant = {}
    for participant in participants:
        newParticipant["id"] = participant.id;
        newParticipant["name"] = participant.name
        if(participant.type == "party"):
            newParticipant["individual"] = False;
        else:
            newParticipant["individual"] = True;
        newParticipants.append(newParticipant);
        newParticipant = {}

    return make_response( jsonify( participants = newParticipants ), 200);


@application.route("/createElection", methods = ["POST"])
@roleCheck ( role = 1 )
def createElection():
    start = request.json.get("start", "");
    end = request.json.get("end", "");
    individual = request.json.get("individual", "");
    participants = request.json.get("participants", "");

    startEmpty = len(start) == 0;
    endEmpty = len(end) == 0;
    individualEmpty = len( str ( individual ) ) == 0;
    participantsEmpty = len( str ( participants )  ) == 0;

    if (startEmpty):
        return make_response(jsonify(message="Field start is missing."), 400);
    if (endEmpty):
        return make_response(jsonify(message="Field end is missing."), 400);
    if (individualEmpty):
        return make_response(jsonify(message="Field individual is missing."), 400);
    if (participantsEmpty):
        return make_response(jsonify(message="Field participants is missing."), 400);

    #dateStart = datetime.strptime(start, "%Y-%m-%dT%H:%M:%S");
    #dateEnd = datetime.strptime(end, "%Y-%m-%dT%H:%M:%S");

    utc = pytz.UTC

    try:
        startDate = parser.isoparse(start);
        endDate = parser.isoparse(end);
    except:
        return make_response(jsonify(message="Invalid date and time."), 400);

    if startDate > endDate:
        return make_response(jsonify(message="Invalid date and time."), 400);

    elections = Election.query.all();
    startDate = parser.isoparse(start);
    endDate = parser.isoparse(end);

    startDate = startDate.replace(tzinfo=utc);
    endDate = endDate.replace(tzinfo=utc);


    for election in elections:
        electionStart = parser.isoparse(election.start);
        electionEnd = parser.isoparse(election.end);

        electionStart = electionStart.replace(tzinfo=utc);
        electionEnd = electionEnd.replace(tzinfo=utc);


        if((startDate > electionStart and startDate < electionEnd) or (endDate > electionStart and endDate < electionEnd)):
            return make_response(jsonify(message="Invalid date and time."), 400);

    if(len(participants) == 0):
        return make_response(jsonify(message="Invalid participants."), 400);

    if(len(participants) < 2):
        return make_response(jsonify(message="Invalid participants."), 400);

    existingParticipants = Participant.query.all();

    existingParticipantsId = [];
    for existingParticipant in existingParticipants:
        existingParticipantsId.append(existingParticipant.id);

    for participant in participants:
        if participant not in existingParticipantsId:
            return make_response(jsonify(message="Invalid participants."), 400);

    electionParticipants = Participant.query.filter(
        or_(
            *[Participant.id == participant for participant in participants]
        )
    )

    electionParticipantsArray = []

    for electionParticipant in electionParticipants:
        electionParticipantsArray.append(electionParticipant)

    for electionParticipant in electionParticipants:
        if (electionParticipant.type == "party" and individual == True) or (electionParticipant.type == "individual" and individual == False):
            return make_response(jsonify(message="Invalid participants."), 400);

    electionType = "individual";
    if(individual == False):
        electionType = "party"

    election = Election( start = start, end = end, type = electionType );

    database.session.add ( election );
    database.session.commit();

    pollNumbers = []

    for i in range(len(electionParticipantsArray)):
        elecPartic = ElectionParticipant( electionId = election.id , participantId = electionParticipantsArray[i].id, serialNumber = i + 1 )
        database.session.add(elecPartic);
        database.session.commit();
        pollNumbers.append(i + 1);


    return make_response( jsonify( pollNumbers = pollNumbers ), 200);


@application.route("/getElections", methods = ["GET"])
@roleCheck ( role = 1 )
def getElections():

    electionQuery = Election.query.all();

    election = {}
    elections = []
    participant = {}
    participants = []

    for row in electionQuery:
        election["id"] = row.id;
        election["start"] = row.start;
        election["end"] = row.end;
        election["individual"] = row.type == "individual";

        participantsArray = []
        for innerRow in row.participants:
            participantsArray.append(innerRow);

        for i in range(len(participantsArray)):
            participant["id"] = participantsArray[i].id;
            participant["name"] = participantsArray[i].name;
            participants.append(participant);
            participant = {}

        election["participants"] = participants
        participants = []

        elections.append(election);
        election = {}

    return make_response( jsonify ( elections = elections ), 200);


@application.route("/getResults", methods = ["GET"])
@roleCheck ( role = 1 )
def getResults():

    electionId = ( request.args.get("id", ""))

    if(len (str (electionId) ) == 0):
        return make_response( jsonify( message = "Field id is missing."), 400);

    election = Election.query.filter( Election.id == electionId ).first();

    if( not election):
        return make_response(jsonify(message="Election does not exist."), 400);

    today = parser.isoparse(datetime.now().isoformat())
    hours_to_add = timedelta(hours=2);
    today = today + hours_to_add;
    seconds_to_add = timedelta(seconds=2);
    today = today + seconds_to_add;
    start = parser.isoparse(election.start);
    end = parser.isoparse(election.end)

    if( today > start and today < end):
        return make_response(jsonify(message="Election is ongoing."), 400);

    if election.type == "individual":
        count = func.count(Vote.candidate);

        query = Vote.query\
            .filter( and_ (Vote.electionId == election.id, Vote.valid == True))\
            .group_by (Vote.candidate).with_entities(Vote.candidate, count);

        votes = query.all();

        allVotes = 0;
        for vote in votes:
            allVotes += vote[1];

        participants = Participant.query.join(ElectionParticipant).filter(ElectionParticipant.electionId == electionId)

        newParticipants = [];
        newParticipant = {}


        for vote, participant in zip(votes, participants):
            newParticipant["pollNumber"] = vote.candidate;
            newParticipant["name"] = participant.name;
            newParticipant["result"] = round(1.0 * int(str(vote[1])) / allVotes, 2);
            newParticipants.append(newParticipant);
            newParticipant = {}


        invalidVotes = Vote.query.filter(and_ (Vote.electionId == election.id, Vote.valid == False)).all();

        newInvalidVotes = [];
        newInvalidVote = {};

        for invalidVote in invalidVotes:
            newInvalidVote["electionOfficialJmbg"] = invalidVote.jmbg;
            newInvalidVote["ballotGuid"] = invalidVote.guid;
            newInvalidVote["pollNumber"] = invalidVote.candidate;
            newInvalidVote["reason"] = invalidVote.reason;
            newInvalidVotes.append(newInvalidVote);
            newInvalidVote = {}

        dictionary = {}
        dictionary["participants"] = newParticipants;
        dictionary["invalidVotes"] = newInvalidVotes;

        return make_response(jsonify(dictionary), 200);

    else:
        count = func.count(Vote.candidate);

        query = Vote.query \
            .filter(and_(Vote.electionId == election.id, Vote.valid == True)) \
            .group_by(Vote.candidate).with_entities(Vote.candidate, count);

        votes = query.all();

        allVotes = 0;
        for vote in votes:
            allVotes += vote[1];

        newVotes = []
        mandates = []
        divisions = [];
        votesToDivide = []
        candidates = []

        for vote in votes:
            if(vote[1] >= 0.05 * allVotes):
                newVotes.append( float( vote[1]) )
                divisions.append( 1 )
                candidates.append( int( vote[0] ));
                votesToDivide.append( float( vote[1] ) )
                mandates.append( 0 )

        maxIndex = 0;
        maxVotes = 0;

        for i in range(250):
            for j in range(len(newVotes)):
                votesToDivide[j] = newVotes[j] / divisions[j]

            for k in range(len(newVotes)):
                if votesToDivide[k] > maxVotes:
                    maxVotes = votesToDivide[k]
                    maxIndex = k

            mandates[maxIndex] = mandates[maxIndex] + 1
            divisions[maxIndex] = divisions[maxIndex] + 1
            maxVotes = 0
            maxIndex = 0

        results = []
        for i in range(len(newVotes)):
            results.append( (candidates[i], mandates[i]))

        participants = Participant.query.join(ElectionParticipant).filter(ElectionParticipant.electionId == electionId)

        newParticipants = [];
        newParticipant = {}

        for result, participant in zip(results, participants):
            newParticipant["pollNumber"] = result[0];
            newParticipant["name"] = participant.name;
            newParticipant["result"] = result[1];
            newParticipants.append(newParticipant);
            newParticipant = {}


        invalidVotes = Vote.query.filter(and_ (Vote.electionId == election.id, Vote.valid == False)).all();

        newInvalidVotes = [];
        newInvalidVote = {};

        for invalidVote in invalidVotes:
            newInvalidVote["electionOfficialJmbg"] = invalidVote.jmbg;
            newInvalidVote["ballotGuid"] = invalidVote.guid;
            newInvalidVote["pollNumber"] = invalidVote.candidate;
            newInvalidVote["reason"] = invalidVote.reason;
            newInvalidVotes.append(newInvalidVote);
            newInvalidVote = {}

        dictionary = {}
        dictionary["participants"] = newParticipants;
        dictionary["invalidVotes"] = newInvalidVotes;

        return make_response(jsonify(dictionary), 200);


if ( __name__ == "__main__" ):
    database.init_app ( application );
    application.run ( debug = True, host = "0.0.0.0", port = 5001);