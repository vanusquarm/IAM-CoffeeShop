import os
from webbrowser import get
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
db_drop_and_create_all()

# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route("/drinks",methods=["GET"])
def get_drinks():
    try: 
        drinks = [drink.short() for drink in Drink.query.order_by(Drink.id).all()]

        return jsonify({
            'success': True,
            'drinks': drinks
        })
    except:
        abort(404)


'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route("/drinks-detail",methods=["GET"])
@requires_auth('get:drinks-detail')
def get_drinks_detail():
    try:
        drinks = [drink.long() for drink in Drink.query.order_by(Drink.id).all()]
        
        return jsonify({
            'success': True,
            'drinks': drinks
        })
    except:
        abort(422)

'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route("/drinks",methods=["POST"])
@requires_auth('post:drinks')
def create_drink():
    body = request.get_json()
    title = body.get('title', None)
    recipe = body.get('recipe', None)

    if title is None or recipe is None:
        abort(422)

    try:
        new_drink = Drink(title=title, recipe=json.dumps(recipe))
        new_drink.insert()

        return jsonify({
            'success': True,
            'drinks': [new_drink.long()]
        })
    except:
        new_drink.rollback()
        raise AuthError({
            'code': 'duplicate titles',
            'description': 'title must be unique'
        }, 422)
    finally:
        new_drink.discard()

'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route("/drinks/<int:drink_id>",methods=["PATCH"])
@requires_auth('patch:drinks')
def update_drink(drink_id):
    body = request.get_json()
    title = body.get('title', None)
    recipe = body.get('recipe', None)
    try:
        drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
        
        if drink is None:
            abort(404)

        if title:
            drink.title = title
        
        if recipe:
            recipe_array = json.loads(drink.recipe)
            recipe_array.extend(recipe)
            drink.recipe = json.dumps(recipe_array)
            
        drink.update()

        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        })
    except:
        drink.rollback()
        abort(422)
    finally:
        drink.discard()

'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route("/drinks/<int:drink_id>",methods=["DELETE"])
@requires_auth('delete:drinks')
def delete_drinks(drink_id):
    try:
        drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
        
        if not drink:
            abort(404)

        drink.delete()

        return jsonify({
            'success': True,
            'delete': drink.id
        })
    except:
        drink.rollback()
        abort(404)
    finally:
        drink.discard()

# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''
@app.errorhandler(404)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "not found"
    }), 404

@app.errorhandler(405)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 405,
        "message": "method not allowed"
    }), 405

@app.errorhandler(500)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": "internal server error"
    }), 500


'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''

@app.errorhandler(AuthError)
def handle_auth_error(auth_error):
    return jsonify({
        "success": False,
        "error": auth_error.status_code,
        "message": auth_error.error['description']
    }), auth_error.status_code