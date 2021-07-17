from flask_sqlalchemy import SQLAlchemy;

database = SQLAlchemy ( );

class ElectionParticipant( database.Model ):
    __tablename__ = "electionparticipant";

    id = database.Column(database.Integer, primary_key= True);
    electionId = database.Column(database.Integer, database.ForeignKey( "elections.id"), nullable= False);
    participantId = database.Column(database.Integer, database.ForeignKey( "participants.id"), nullable= False);
    serialNumber = database.Column(database.Integer, nullable=False);


class Participant( database.Model ):
    __tablename__ = "participants";

    id = database.Column(database.Integer, primary_key= True);
    name = database.Column(database.String(256), nullable= False);
    type = database.Column(database.String(256), nullable= False);

    elections = database.relationship( "Election", secondary = ElectionParticipant.__table__, back_populates = "participants")

    def __repr__(self):
        return "({}, {}, {})".format ( self.id, self.name, self.type == "individual" );


class Election( database.Model ):
    __tablename__ = "elections";

    id = database.Column(database.Integer, primary_key= True);
    start = database.Column(database.String(256), nullable= False);
    end = database.Column(database.String(256), nullable= False);
    type = database.Column(database.String(256), nullable= False);

    participants = database.relationship( "Participant", secondary = ElectionParticipant.__table__, back_populates = "elections");
    votes = database.relationship("Vote", back_populates="election");

    def __repr__(self):
        return "{}: {} - {} : {} ::: {}".format( self.id, self.start, self.end, self.type, self.participants);

class Vote( database.Model ):
    __tablename__ = "votes"

    id = database.Column(database.Integer, primary_key= True);
    guid = database.Column(database.String(36), nullable= False);
    jmbg = database.Column(database.String(13), nullable= False);
    electionId = database.Column(database.Integer, database.ForeignKey( "elections.id" ), nullable= False);
    candidate = database.Column(database.Integer, nullable= False);
    valid = database.Column(database.Boolean, nullable= False);
    reason = database.Column(database.String(256));

    election = database.relationship( "Election", back_populates = "votes");

    def __repr__(self):
        return "voteId: {}, Election: {}, Candidate: {}".format( self.id, self.electionId, self.candidate);



