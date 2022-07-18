"""Parameters for game configuration."""

TIMER_PERIOD_SEC = 0.45

TITLE_LINE = 1
INIT_TITLE = "WELCOME TO 'CURSED TYPIST' - STUPID TYPING GAME!"
GAME_TITLE = "RUN FROM THE LAVA!"
GAMEOVER_TITLE = "OUCH, YOU HAVE FALLEN INTO THE LAVA!"
WIN_TITLE = "YOU WIN!"

PROMPT_LINE = 2
INIT_PROMPT = "Press any key to start playing"
GAME_PROMPT = "Type the text to run forward"
GAMEOVER_PROMPT = "Press q to quit"
WIN_PROMPT = "You have successfully escaped from lava. Press q to quit"

PLAYER_OFFSET = 10
PLAYER_PIC = "$"
PLAYER_LINE = 4
FLOOR_PIC = "="
FLOOR_LINE = 5
LAVA_CHARS = "~#@_+-:?*"
LAVA_LINE = 6

MESSAGE_LINE = 8
MESSAGE_OFFSET = 12

DEFAULT_TEXT = """\
You can play on your own texts - just pass the path as a command line
argument"""
