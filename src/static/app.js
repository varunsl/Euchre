var socket = io.connect('http://' + document.domain + ':' + location.port);
socket.on('connect', function() {
  socket.emit('new_connection', 'Let\'s start!');
});

socket.on('show_bidding_window', function(data) {
  console.log(data);
  if (data.show == true && data.round == 1) {
    bidding1();
  } else if (data.show == true && data.round == 2) {
    bidding2(data.ineligible_suit, data.is_dealer);
  }
});

var card_suits = {'H' : '♥', 'S' : '♠', 'C' : '♣', 'D' : '♦'};

socket.on('log_entry', function(data) {
  $('#log').append(data.text+'\n');
  $('#log').scrollTop( $('#log')[0].scrollHeight - $('#log').height());
});

socket.on('trump_chosen', function(data) {
  $("#trump-info").text('Trump: '+card_suits[data.trump]);
});

socket.on('card_to_dealer', function(data) {
  card = data.card;
  if (card[0] == 'T') {
    $('#your-cards').append('<div class="card suit'+card_suits[card[1]]+'"> <p class="card-top">'+'10'+'</p><p class="card-center">'+card_suits[card[1]]+'</p><p class="card-bottom">'+'10'+'</p></div>');
  } else {
    $('#your-cards').append('<div class="card suit'+card_suits[card[1]]+'"> <p class="card-top">'+card[0]+'</p><p class="card-center">'+card_suits[card[1]]+'</p><p class="card-bottom">'+card[0]+'</p></div>');
  }
});

socket.on('update_event', function(data) {
  console.log(data);
  card = data.card;
  if ($('#played-cards .card').length == data.num_cards_in_trick) {
    $('#played-cards').empty();
    $('#played-cards').append('<h2>Played Cards</h2>')
  }
  if (card[0] == 'T') {
    $('#played-cards').append('<div class="card suit'+card_suits[card[1]]+'"> <p class="card-top">'+'10'+'</p><p class="card-center">'+card_suits[card[1]]+'</p><p class="card-bottom">'+'10'+'</p></div>');
  } else {
    $('#played-cards').append('<div class="card suit'+card_suits[card[1]]+'"> <p class="card-top">'+card[0]+'</p><p class="card-center">'+card_suits[card[1]]+'</p><p class="card-bottom">'+card[0]+'</p></div>');
  }
});

socket.on('move_accepted', function(data) {
  if (data.accepted == true) {
    $("#"+String(data.card_to_remove)).remove();
    $('#your-cards .card').each(function(i, obj){
      $(this).attr("id",i);
    });
  }
});

socket.on('update_scores', function(data) {
  console.log(data);
  $('#team1_overall').text(data.overall[0]);
  $('#team2_overall').text(data.overall[1]);
  $('#team1_round').text(data.round[0]);
  $('#team2_round').text(data.round[1]);
});

socket.on('new_round', function(data) {
  window.location.reload(true);
});

function bidding1() {
  $('.bidding').show();
  $('#suits').hide();
 }

function bidding2(suit, dealer) {
  if (dealer == true) {
    $('#pass').hide();
  }
  $('.bidding').show();
  $('#suits').show();
  $('#upturned-card').hide();
  $('#pick-it-up').hide();
  $('#'+suit).hide();
}

$(document).ready(function(){
  $('.bidding').hide();

  if (typeof current_bidder !== 'undefined') {
    if (bidding_round == 1) {
      bidding1();
    } else if (bidding_round == 2) {
      bidding2();
    }
  }

	$('#your-cards .card').click(function () {
    socket.emit('submit_move', this.id);
	});

  $('#pick-it-up').click(function () {
    var loner =  $("#loner").is(":checked");
    socket.emit('submit_bid', {'bid': 'Pick it up', 'loner': loner});
    $('.bidding').hide();
	});

  $('#pass').click(function () {
    socket.emit('submit_bid', {'bid': 'Pass', 'loner': false});
    $('.bidding').hide();
	});

  $('.choice').click(function () {
    var loner =  $("#loner").is(":checked");
    socket.emit('submit_bid', {'bid': this.id, 'loner': loner});
    $('.bidding').hide();
	});
});
