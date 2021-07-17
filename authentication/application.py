from flask import Flask, request, Response, jsonify, json, make_response;
from configuration import Configuration;
from models import database, User;
from email.utils import parseaddr;
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, get_jwt_identity;
from sqlalchemy import and_;
import re;


application = Flask ( __name__ );
application.config.from_object ( Configuration );

def checkJmbg(jmbg):

    if (len(str(jmbg)) != 13 or int(jmbg[0] + jmbg[1]) < 1 or int(jmbg[0] + jmbg[1]) > 31 or
            int(jmbg[2] + jmbg[3]) < 1 or int(jmbg[2] + jmbg[3]) > 12 or
            int(jmbg[7] + jmbg[8]) < 70):
        return False;

    a = int(jmbg[0]); b = int(jmbg[1]);
    c = int(jmbg[2]); d = int(jmbg[3]);
    e = int(jmbg[4]); f = int(jmbg[5]);
    g = int(jmbg[6]); h = int(jmbg[7]);
    i = int(jmbg[8]); j = int(jmbg[9]);
    k = int(jmbg[10]); l = int(jmbg[11]);

    m = 11 - ((7*(a + g) + 6*(b + h) + 5*(c + i) + 4*(d + j) + 3*(e + k) + 2*(f + l) ) % 11)

    if( m == 10 or m == 11):
        m = 0;

    if( m != int(jmbg[12]) ):
        return False;

    return True;

def checkPassword(password):
    if(len(password) < 8):
        return False;

    numberPresent = False;
    smallCharacterPresent = False;
    bigCharacterPresent = False;

    for i in range(len(password)):
        if(password[i] >= "0" and password[i] <= "9"):
            numberPresent = True;

        if(password[i] >= "a" and password[i] <= "z"):
            smallCharacterPresent = True;

        if(password[i] >= "A" and password[i] <= "Z"):
            bigCharacterPresent = True;

    if (numberPresent == False or smallCharacterPresent == False or bigCharacterPresent == False):
        return False;

    return True;

#Ne zaboravi da u postmanu mora u header delu da se izabere content-type za key i application/json za value

def checkMail(email):

    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b';

    if (re.match(regex, email)):
        return True;
    else:
        return False;


@application.route ( "/register", methods = ["POST"] )
def register ( ):
    email = request.json.get ( "email", "" );
    password = request.json.get ( "password", "" );
    forename = request.json.get ( "forename", "" );
    surname = request.json.get ( "surname", "" );
    jmbg = request.json.get ( "jmbg", "");

    emailEmpty = len ( email ) == 0;
    passwordEmpty = len ( password ) == 0;
    forenameEmpty = len ( forename ) == 0;
    surnameEmpty = len ( surname ) == 0;
    jmbgEmpty = len ( jmbg ) == 0;

    if(jmbgEmpty):
        return make_response( jsonify( message = "Field jmbg is missing."), 400);
    if(forenameEmpty):
        return make_response( jsonify( message = "Field forename is missing."), 400);
    if(surnameEmpty):
        return make_response( jsonify( message = "Field surname is missing."), 400);
    if (emailEmpty):
        return make_response( jsonify( message = "Field email is missing."), 400);
    if(passwordEmpty):
        return make_response( jsonify( message = "Field password is missing."), 400);


    if(checkJmbg(jmbg) == False):
        return make_response( jsonify( message = "Invalid jmbg."), 400);

    result = checkMail(email)
    if(result == False):
        return make_response(jsonify(message="Invalid email."), 400);

    if (checkPassword(password) == False):
        return make_response( jsonify( message = "Invalid password."), 400);

    checkUser = User.query.filter( User.email == email ).first();
    if(checkUser):
        return make_response( jsonify( message = "Email already exists."), 400);

    user = User ( email = email, password = password, forename = forename, surname = surname, jmbg = jmbg, roleId = 2 );
    database.session.add ( user );
    database.session.commit ( );

    return Response ( "Registration successful!", status = 200 );

jwt = JWTManager ( application );

@application.route ( "/login", methods = ["POST"] )
def login ( ):
    email = request.json.get ( "email", "" );
    password = request.json.get ( "password", "" );

    emailEmpty = len ( email ) == 0;
    passwordEmpty = len ( password ) == 0;

    if(emailEmpty):
        return make_response( jsonify( message = "Field email is missing."), 400);
    if(passwordEmpty):
        return make_response( jsonify( message = "Field password is missing."), 400);

    result = checkMail(email)
    if(result == False):
        return make_response(jsonify(message="Invalid email."), 400);

    user = User.query.filter ( and_ ( User.email == email, User.password == password ) ).first ( );

    if ( not user ):
        return make_response( jsonify( message = "Invalid credentials."), 400);

    additionalClaims = {
            "forename": user.forename,
            "surname": user.surname,
            "jmbg": user.jmbg,
            "role": user.roleId
    }

    accessToken = create_access_token ( identity = user.email, additional_claims = additionalClaims );
    refreshToken = create_refresh_token ( identity = user.email, additional_claims = additionalClaims );

    # return Response ( accessToken, status = 200 );
    #return jsonify ( accessToken = accessToken, refreshToken = refreshToken );

    return make_response(jsonify(accessToken = accessToken, refreshToken = refreshToken), 200);

@application.route ( "/check", methods = ["POST"] )
@jwt_required ( )
def check ( ):
    return "Token is valid!";

@application.route ( "/refresh", methods = ["POST"] )
@jwt_required ( refresh = True )
def refresh ( ):
    identity = get_jwt_identity ( );
    refreshClaims = get_jwt ( );

    additionalClaims = {
            "forename": refreshClaims["forename"],
            "surname": refreshClaims["surname"],
            "jmbg": refreshClaims["jmbg"],
            "role": refreshClaims["role"]
    };

    return jsonify( accessToken = create_access_token (  identity = identity, additional_claims = additionalClaims ));
    #return Response ( create_access_token ( identity = identity, additional_claims = additionalClaims ), status = 200 );

@application.route ( "/", methods = ["GET"] )
def index ( ):
    return "Hello world!";

@application.route ( "/delete", methods = ["POST"] )
@jwt_required ( )
def delete ( ):
    email = request.json.get("email", "");

    emailEmpty = len(email) == 0;

    if (emailEmpty):
        return make_response( jsonify( message = "Field email is missing."), 400);

    result = checkMail(email)
    if(result == False):
        return make_response(jsonify(message="Invalid email."), 400);

    checkUser = User.query.filter( User.email == email).first();

    if not checkUser:
        return make_response( jsonify( message = "Unknown user."), 400);

    database.session.delete( checkUser );
    database.session.commit();

    return Response( status = 200);

if ( __name__ == "__main__" ):
    database.init_app ( application );
    application.run ( debug = True, host = "0.0.0.0", port = 5005);