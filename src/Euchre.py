suits = 'HCSD'
ranks = '9TJQKA'

def card_list_to_string(cards):
    return ''.join(cards)

def card_string_to_list(card_string):
    return [card_string[i:i+2] for i in range(0, len(card_string), 2)]

def card_by_index(card_string, card_index):
    return card_string[2*card_index:2*card_index+2]

def move_card(card_string_1, card_string_2, card_index):
    card = card_by_index(card_string_1, card_index)
    return card_string_1.replace(card, ''), card_string_2 + card

def create_deck():
    from random import shuffle
    cards = [rank+suit for rank in ranks for suit in suits]
    shuffle(cards)
    return card_list_to_string(cards)

def deal_cards(deck, num_cards):
    dealt_cards = ''
    for _ in range(num_cards):
        deck, dealt_cards = move_card(deck, dealt_cards, 0)
    return deck, dealt_cards

def same_color(suit):
    return suits[::-1][suits.index(suit)]

def effective_suit(card, trump):
    rank, suit = card[0], card[1]
    if rank == 'J' and suit == same_color(trump): return trump
    else: return suit

def followed_suit(trick_string, player_card_string, card_index, trump):
    if trick_string == '':
        return True
    else:
        player_cards = card_string_to_list(player_card_string)
        card = player_cards[card_index]
        lead_suit = effective_suit(card_by_index(trick_string, 0), trump)
        has_followed_suit = effective_suit(card, trump) == lead_suit
        cannot_follow = all(effective_suit(card, trump) != lead_suit
                            for card in player_cards)
        return has_followed_suit or cannot_follow

def score_card(card, lead, trump):
    rank, suit = card[0], card[1]
    if rank == 'J' and suit == trump: return 13
    elif rank == 'J' and suit == same_color(trump): return 12
    elif suit == trump: return ranks.index(rank) + 6
    elif suit == lead: return ranks.index(rank)
    else: return -1

def evaluate_trick(card_string, trump):
    trick = card_string_to_list(card_string)
    lead = trick[0][1]
    scores = [score_card(card, lead, trump) for card in trick]
    max_score = max(scores)
    return scores.index(max_score)
