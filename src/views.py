from flask import render_template, request, session, redirect
from flask_socketio import emit, join_room
from app import app, db, socketio
from models import Players, Game_Data
from actions import *

@socketio.on('new_connection')
def handle_new_connection(data):
    if data == 'Let\'s start!':
        user, gameID = session['user'], session['gameID']
        user_room, game_room = gameID+':'+user, 'Room:'+gameID
        join_room(user_room)
        join_room(game_room)
        emit('enough_players', {'enough': True, 'gameID': gameID},
        broadcast=True)

@socketio.on('submit_bid')
def handle_bid(data):
    print(session['user'])
    print('received bid: ' + str(data))
    submit_bid(session['gameID'], session['user'], data)

@socketio.on('submit_move')
def handle_submit(data):
    print(session['user'])
    print('received move: ' + str(data))
    submit_move(session['gameID'], session['user'], int(data))

def create_session(gameID, name, first=False):
    session['user'] = name
    session['gameID'] = gameID
    if first:
        create_game(gameID)
    add_player(gameID, name)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if not request.form['nickname']:
            return render_template('index.html', message='Please pick a name.')
        if not request.form['gameID']:
            create_session(generate_gameID(), request.form['nickname'],
            first=True)
            return redirect('/play/'+session['gameID'])
        data=Game_Data.query.filter_by(gid=request.form['gameID']).first()
        if data and number_of_players(request.form['gameID']) < 4:
            if db.session.query(Players).filter_by(
            gid=request.form['gameID'],
            name=request.form['nickname']
            ).scalar() is None:
                create_session(request.form['gameID'], request.form['nickname'])
                return redirect('/play/'+session['gameID'])
            else:
                return render_template('index.html', message='Name is taken!')
        else:
            return render_template('index.html', message='Cannot join game!')
    return render_template('index.html')

@app.route('/play/<gameID>')
def play(gameID):
    if number_of_players(gameID) < 4:
        return render_template('waiting.html', gameID=gameID)
    db_game = Game_Data.query.filter_by(gid=gameID).first()
    player=Players.query.filter_by(gid=gameID,name=session['user']).first()
    player_cards = Euchre.card_string_to_list(player.cards)
    played_cards = Euchre.card_string_to_list(db_game.trick)
    current_bidder = start_bidding(gameID, session['user'])
    return render_template('play.html', db_game=db_game, player=player,
    player_cards=player_cards, played_cards=played_cards,
    current_bidder=current_bidder, gameID=gameID)
