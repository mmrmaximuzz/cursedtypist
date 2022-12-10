"""Testing the typing game."""

import pytest

from cursedtypist import game
from cursedtypist import params


__TEST_TEXT = "TEXT"


@pytest.fixture
def model(mocker) -> game.GameModel:
    """Return the game model with mocked view."""
    return game.GameModel(mocker.Mock(), __TEST_TEXT)


def test_game_model_init(model):
    """The model initializes view correctly."""
    model.view.init_screen.assert_called()
    model.view.game_screen.assert_not_called()
    model.view.death_screen.assert_not_called()
    model.view.win_screen.assert_not_called()
    model.view.print_message.assert_not_called()
    model.view.drop_floor.assert_not_called()
    model.view.move_player.assert_not_called()


def test_game_model_start(model):
    """The model start sets view to a game screen."""
    model.start()
    model.view.game_screen.assert_called_with(__TEST_TEXT)


def test_game_player_move_ok(model):
    """The model moves player on right keystroke."""
    # get the right key
    key, *_ = __TEST_TEXT

    # save the previous positions
    old_player, old_tracer = model.player, model.tracer

    model.start()
    model.player_move(key)

    # player is moved
    assert model.player == old_player + 1
    model.view.move_player.assert_called()
    model.view.print_message.assert_called_with("")

    # floor is not dropped
    assert model.tracer == old_tracer
    model.view.drop_floor.assert_not_called()

    # game is not over
    model.view.win_screen.assert_not_called()
    model.view.death_screen.assert_not_called()
    assert not model.finished.done()


def test_game_player_move_nok(model):
    """The model drops floor on wrong keystroke."""
    # get the wrong key
    key = chr(0)

    # save the previous positions
    old_player, old_tracer = model.player, model.tracer

    model.start()
    model.player_move(key)

    # player is not moved
    assert model.player == old_player
    model.view.move_player.assert_not_called()
    model.view.print_message.assert_called_with("WRONG KEY")

    # floor is dropped
    assert model.tracer == old_tracer + 1
    model.view.drop_floor.assert_called()

    # game is not over
    model.view.win_screen.assert_not_called()
    model.view.death_screen.assert_not_called()
    assert not model.finished.done()


def test_game_player_move_ok_win(model):
    """The model set the win state if the text is gone."""
    model.start()
    for key in __TEST_TEXT:
        model.player_move(key)

    # player moved, no wrong keys printed
    model.view.move_player.assert_called()
    model.view.print_message.assert_called_with("")

    # floor is not droped
    model.view.drop_floor.assert_not_called()

    # game is over, player wins
    model.view.win_screen.assert_called()
    model.view.death_screen.assert_not_called()
    assert model.finished.done()
    assert model.finished.result()


def test_game_player_move_nok_lose(model):
    """The model set the lose state if too many errors."""
    # get the wrong key
    badkey = chr(0)

    model.start()
    for _ in range(params.PLAYER_INIT_OFFSET):
        model.player_move(badkey)

    # player is not moved, wrong key is printed
    model.view.move_player.assert_not_called()
    model.view.print_message.assert_called_with("WRONG KEY")

    # floor is dropped
    model.view.drop_floor.assert_called()

    # game is over, player loses
    model.view.death_screen.assert_called()
    model.view.win_screen.assert_not_called()
    assert model.finished.done()
    assert not model.finished.result()


def test_game_timer_fired(model):
    """The model drops the floor after the timer event."""
    model.start()

    # save the previous positions
    old_player, old_tracer = model.player, model.tracer

    # fire the timer
    model.timer_fired()

    # player is not moved
    assert model.player == old_player
    model.view.move_player.assert_not_called()

    # floor is dropped
    assert model.tracer == old_tracer + 1
    model.view.drop_floor.assert_called()

    # no messages emitted
    model.view.print_mesasge.assert_not_called()

    # game is not over
    model.view.win_screen.assert_not_called()
    model.view.death_screen.assert_not_called()
    assert not model.finished.done()


def test_game_timer_fired_lose(model):
    """The model set the lose state after many timer events."""
    model.start()

    # wait until the floor reaches the player
    for _ in range(params.PLAYER_INIT_OFFSET):
        model.timer_fired()

    # player is not moved
    model.view.move_player.assert_not_called()

    # floor is dropped
    model.view.drop_floor.assert_called()

    # no messages emitted
    model.view.print_mesasge.assert_not_called()

    # game is over, player loses
    model.view.death_screen.assert_called()
    model.view.win_screen.assert_not_called()
    assert model.finished.done()
    assert not model.finished.result()
