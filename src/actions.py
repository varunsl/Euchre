from app import db
from models import Players, Game_Data
from flask_socketio import emit
import Euchre

def create_game(gameID):
    deck = Euchre.create_deck()
    new_game = Game_Data(gid=gameID, deck=deck, trick='')
    db.session.add(new_game)
    db.session.commit()

def add_player(gameID, name):
    team = (number_of_players(gameID) + 1) % 2
    db_game = Game_Data.query.filter_by(gid=gameID).first()
    db_game.deck, player_cards = Euchre.deal_cards(db_game.deck, 5)
    new_player = Players(name=name, cards=player_cards, gid=gameID, team=team)
    db.session.add(new_player)
    db.session.commit()

def number_of_players(gameID):
    all_players = Players.query.filter_by(gid=gameID).all()
    return len(all_players)

def generate_gameID():
    import random, string
    return ''.join(random.choice(string.ascii_uppercase +
    string.ascii_lowercase + string.digits) for _ in range(8))

def start_bidding(gameID, username): #combine with next_bidder function
    db_game = Game_Data.query.filter_by(gid=gameID).first()
    if db_game.bidding_round > 0:
        player = Players.query.filter_by(gid=gameID,name=username).first()
        all_players = Players.query.filter_by(gid=gameID).all()
        all_players[db_game.current_turn].turn = True
        db.session.commit()
        return all_players[db_game.current_turn].name == player.name

def next_bidder(gameID):
    db_game = Game_Data.query.filter_by(gid=gameID).first()
    if db_game.bidding_round > 0:
        all_players = Players.query.filter_by(gid=gameID).all()
        db_game.current_turn = (db_game.current_turn + 1) % 4
        all_players[db_game.current_turn-1].turn = False
        all_players[db_game.current_turn].turn = True
        db.session.commit()
        return all_players[db_game.current_turn].name

def submit_bid(gameID, username, bid):
    print(bid)
    player = Players.query.filter_by(gid=gameID,name=username).first()
    db_game = Game_Data.query.filter_by(gid=gameID).first()
    if player.turn == True:
        player.turn = False
        all_players = Players.query.filter_by(gid=gameID).all()
        if bid['loner'] == True and bid['bid'] != 'Pass':
            db_game.loner = all_players.index(player)
            db_game.player_to_skip = (db_game.loner + 2) % 4
            print('loner: ', db_game.loner, 'player_to_skip: ', db_game.player_to_skip)
            print(username+' will play alone')
        if bid['bid'] == 'Pick it up':
            db_game.trump = db_game.deck[1]
            db_game.won_bid = db_game.current_turn % 2
            print(db_game.won_bid)
            dealer = all_players[db_game.dealer]
            db_game.deck, dealer.cards = Euchre.move_card(db_game.deck, dealer.cards, 0)
            db_game.current_turn = db_game.dealer
            all_players[db_game.current_turn].turn = True
            db_game.bidding_round = -1
            db.session.commit()
            game_room = 'Room:'+gameID
            emit('trump_chosen', {'trump':db_game.trump},room=game_room)
            next_bidder_room = gameID+':'+dealer.name
            card=player=Players.query.filter_by(
            gid=gameID,
            name=dealer.name
            ).first().cards[10:12] #last card
            emit('card_to_dealer', {'card': card}, room=next_bidder_room)
            emit('log_entry', {'text': dealer.name+' will pick it up.'},
            room=game_room)
        elif bid['bid'] == 'Pass':
            if db_game.current_turn == db_game.dealer:
                db_game.bidding_round += 1
            next_bidder_room = gameID+':'+next_bidder(gameID)
            ineligible_suit, is_dealer = '', False
            if db_game.bidding_round == 2:
                ineligible_suit = db_game.deck[1]
                if db_game.current_turn == db_game.dealer:
                    is_dealer = True
            emit('show_bidding_window', {'show': True,
            'round': db_game.bidding_round, 'ineligible_suit': ineligible_suit,
            'is_dealer': is_dealer}, room=next_bidder_room)
        elif bid['bid'] in 'HCSD':
            db_game.bidding_round = 0
            db_game.trump = bid['bid']
            db_game.won_bid = db_game.current_turn % 2
            print(db_game.won_bid)
            db_game.current_turn = (db_game.dealer + 1) % 4
            all_players[db_game.current_turn].turn = True
            db.session.commit()
            game_room = 'Room:'+gameID
            emit('trump_chosen', {'trump':db_game.trump},room=game_room)

def can_play(player, db_game, card_index):
    return player.turn and Euchre.followed_suit(db_game.trick, player.cards, card_index, db_game.trump) and db_game.bidding_round == 0

def score_trick(winner, db_game):
    if winner % 2 == 0:
        db_game.team1_score_round += 1
    elif winner % 2 == 1:
        db_game.team2_score_round += 1
    db.session.commit()
    game_room = 'Room:'+db_game.gid
    emit('update_scores',
    {'round': [db_game.team1_score_round,db_game.team2_score_round],
    'overall': [db_game.team1_score_overall,db_game.team2_score_overall]},
    room=game_room)

def score_round(db_game):
    attacker = {'score_round': db_game.team1_score_round,
                'score_overall': db_game.team1_score_overall}
    defender = {'score_round': db_game.team2_score_round,
                'score_overall': db_game.team2_score_overall}
    if db_game.won_bid == 1:
        attacker, defender = defender, attacker
    if attacker['score_round'] == 5:
        if db_game.loner > -1:
            attacker['score_overall'] += 4
        else:
            attacker['score_overall'] += 2
    elif attacker['score_round'] >= 3:
        attacker['score_overall'] += 1
    elif defender['score_round'] == 5:
        defender['score_overall'] += 4
    elif defender['score_round'] >= 3:
        defender['score_overall'] += 2
    db_game.team1_score_round, db_game.team2_score_round = 0, 0
    if db_game.won_bid == 0:
        db_game.team1_score_overall = attacker['score_overall']
        db_game.team2_score_overall = defender['score_overall']
    elif db_game.won_bid == 1:
        db_game.team2_score_overall = attacker['score_overall']
        db_game.team1_score_overall = defender['score_overall']
    db.session.commit()
    game_room = 'Room:'+db_game.gid
    emit('update_scores', {'round': [db_game.team1_score_round,db_game.team2_score_round],
    'overall': [db_game.team1_score_overall,db_game.team2_score_overall]},room=game_room)

def new_round(db_game):
    gameID = db_game.gid
    all_players = Players.query.filter_by(gid=gameID).all()
    db_game.deck = Euchre.create_deck()
    for player in all_players:
        db_game.deck, player.cards = Euchre.deal_cards(db_game.deck, 5)
    db_game.bidding_round = 1
    starting_bidder = all_players[db_game.current_turn]
    starting_bidder.turn = True
    db_game.loner = -1
    db_game.player_to_skip = -1
    db.session.commit()
    starting_bidder_room = gameID+':'+starting_bidder.name
    emit('show_bidding_window', {'show': True, 'round':db_game.bidding_round}, room=starting_bidder_room)
    game_room = 'Room:'+db_game.gid
    emit('new_round', {'new': True}, room=game_room)

def skipped_player_check(db_game):
    if db_game.loner > -1 and db_game.current_turn == db_game.player_to_skip:
        db_game.current_turn = (db_game.current_turn + 1) % 4
        return True

def next_player(player, db_game): #don't need player parameter?
    db_game.total_turns += 1
    db_game.current_turn = (db_game.current_turn + 1) % 4
    print('total turn', db_game.total_turns)
    if skipped_player_check(db_game):
        db_game.total_turns += 1
        db_game.trick += '--'
        print('skipped, total turns:', db_game.total_turns, 'current turn: ',
        db_game.current_turn)
    if db_game.total_turns % 4 == 0:
        print('Completed one trick')
        print(db_game.trick)
        print(db_game.current_turn)
        winner = (Euchre.evaluate_trick(db_game.trick, db_game.trump) +
        db_game.current_turn) % 4
        db_game.current_turn = winner
        score_trick(winner, db_game)
        db_game.trick = ''
        print('current turn: ', db_game.current_turn)
    if db_game.total_turns % 20 == 0:
        print('Completed one round')
        db_game.dealer = (db_game.dealer + 1) % 4
        db_game.current_turn = (db_game.dealer + 1) % 4
        score_round(db_game)
        new_round(db_game)
        print('current turn: ', db_game.current_turn)
    if db_game.total_turns % 4 != 0:
        print('In the middle of a trick')
        print('current turn: ', db_game.current_turn)
    db.session.commit()
    print('total turns',db_game.total_turns,'current turn',db_game.current_turn,
    'trick',db_game.trick)
    game_room = 'Room:'+db_game.gid
    emit('log_entry', {'text': 'next turn'}, room=game_room)

def submit_move(gameID, username, card_index):
    player = Players.query.filter_by(gid=gameID,name=username).first()
    db_game = Game_Data.query.filter_by(gid=gameID).first()
    game_room = 'Room:'+gameID
    if db_game.bidding_round == -1 and player.turn == True:
        print('bid discard')
        db_game.bidding_round = 0
        player.turn = False
        card = Euchre.card_by_index(player.cards, card_index)
        player.cards, db_game.deck = Euchre.move_card(player.cards, db_game.deck, card_index)
        db_game.current_turn = (db_game.dealer + 1) % 4
        skipped_player_check(db_game)
        all_players = Players.query.filter_by(gid=gameID).all()
        all_players[db_game.current_turn].turn = True
        print('total turns: ',db_game.total_turns)
        print(all_players[db_game.current_turn].name+"'s lead", db_game.current_turn)
        db.session.commit()
        emit('move_accepted', {'accepted': True, 'card_to_remove': card_index})
        emit('log_entry', {'text': all_players[db_game.current_turn].name+"'s lead"},
        room=game_room)
    elif can_play(player, db_game, card_index):
        player.turn = False
        card = Euchre.card_by_index(player.cards, card_index)
        player.cards, db_game.trick = Euchre.move_card(player.cards, db_game.trick, card_index)
        print(player.name + '(Team'+ ') plays their ' + card)
        next_player(player, db_game)
        all_players = Players.query.filter_by(gid=gameID).all()
        all_players[db_game.current_turn].turn = True
        db.session.commit()
        emit('log_entry', {'text': player.name+' plays their '+card},
        room=game_room)
        emit('move_accepted', {'accepted': True, 'card_to_remove': card_index})
        num_cards_in_trick = 4
        if db_game.loner > -1:
            num_cards_in_trick = 3
        emit('update_event', {'card': card, 'num_cards_in_trick':
        num_cards_in_trick}, room=game_room)
