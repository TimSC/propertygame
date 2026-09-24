
Property Game
=============

A simulation of the famous property trading game Monopoly. This is currently a library with a text based interface. It's aimed at developers rather than regular players.


Playing
-------

A pygame interface lets you play against other people (sharing the screen) or AI players:

    venv/bin/python pygameui.py

Choose 2-8 players, whether each is a human or an AI, and the AI speed. The basic AI tries to complete colour sets and build on them, but doesn't trade; the random AI makes random choices. All players can be AIs, to watch a game. On a human's turn, build, mortgage and trade from the side panel before rolling; other decisions (buying, auctions, jail, raising money, trade offers) are asked in dialogs. Hover over a space to see its details. Space pauses AI play.
