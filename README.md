
Property Game
=============

A simulation of the famous property trading game Monopoly. This is currently a library with a text based interface. It's aimed at developers rather than regular players.


Playing
-------

A pygame interface lets you play against other people (sharing the screen) or AI players:

    venv/bin/python pygameui.py

Choose 2-8 players, whether each is a human or an AI, and the AI speed. The basic AI tries to complete colour sets and build on them, and trades for the pieces it needs; the random AI makes random choices. All players can be AIs, to watch a game. On a human's turn, build, mortgage and trade from the side panel before rolling; other decisions (buying, auctions, jail, raising money, trade offers) are asked in dialogs. Hover over a space to see its details. Space pauses AI play.

Tuning the AI
-------------

The basic AI's behaviour is set by `BasicAIParameters` in `basicai.py` (trading, buying, cash reserve, building, jail and how strong it rates each colour set). `tuneai.py` plays a variant against the default AI and reports whether it wins more often:

    python3 tuneai.py fairness=0.7
    python3 tuneai.py reserveBase=100 --players 3 --games 500
