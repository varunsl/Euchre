from app import db

class Players(db.Model):
    __tablename__ = 'players'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))             #player name
    cards = db.Column(db.String(10))            #player's cards in plaintext
    gid = db.Column(db.String(8))               #gameID
    team = db.Column(db.Integer)                #player's team
    turn = db.Column(db.Boolean, default=False) #true if it is player's turn

class Game_Data(db.Model):
    __tablename__ = 'game_data'

    id = db.Column(db.Integer, primary_key=True)
    gid = db.Column(db.String(8))
    deck = db.Column(db.String(48))                  #kitty in plaintext
    trick = db.Column(db.String(8))                  #cards played in current trick
    total_turns = db.Column(db.Integer, default=0)
    current_turn = db.Column(db.Integer, default=1)
    dealer = db.Column(db.Integer, default=0)        #index of dealer
    bidding_round = db.Column(db.Integer, default=1)
    trump = db.Column(db.String(1), default='')
    loner = db.Column(db.Integer, default=-1)
    player_to_skip = db.Column(db.Integer)
    won_bid = db.Column(db.Integer)
    team1_score_round = db.Column(db.Integer, default=0)
    team1_score_overall = db.Column(db.Integer, default=0)
    team2_score_round = db.Column(db.Integer, default=0)
    team2_score_overall = db.Column(db.Integer, default=0)
