"""
Pygame user interface for the property game.

Run with:  venv/bin/python pygameui.py

Choose 2-8 players, whether each is a human or the random AI, and the board. Humans
share the screen (hot seat), and every decision the engine needs is asked in a dialog.
Games can be all AI, with the speed set from the side panel.
"""

import re
import pygame
from propertygame import PropertyGame
from interfaces import PlayerInterface, RandomInterface

WINDOW = (1200, 800)
BOARD_X, BOARD_Y, BOARD_SIZE = 10, 10, 780
CORNER = 100
EDGE = (BOARD_SIZE - 2 * CORNER) / 9.0
CENTRE = pygame.Rect(BOARD_X + CORNER, BOARD_Y + CORNER, BOARD_SIZE - 2 * CORNER, BOARD_SIZE - 2 * CORNER)
PANEL_X = 800

BACKGROUND = (28, 60, 44)
BOARD_COLOUR = (206, 230, 208)
CELL_COLOUR = (236, 246, 236)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (150, 150, 150)
DARK_GREY = (80, 80, 80)
PANEL_COLOUR = (240, 240, 232)
HIGHLIGHT = (255, 214, 60)
SELECTED = (170, 225, 170)
GROUP_COLOURS = [(149, 84, 54), (170, 224, 250), (217, 58, 150), (247, 148, 29),
	(237, 27, 36), (254, 242, 0), (31, 178, 90), (0, 114, 187)]
PLAYER_COLOURS = [("Red", (220, 50, 50)), ("Blue", (50, 100, 230)), ("Green", (40, 170, 70)),
	("Yellow", (235, 200, 20)), ("Purple", (150, 70, 200)), ("Orange", (245, 140, 30)),
	("Cyan", (40, 190, 200)), ("Pink", (240, 110, 180))]
SPEEDS = [("Slow", 700), ("Normal", 250), ("Fast", 40), ("Instant", 0)]
BOARDS = [("US", "property-board-us.txt", "$"), ("UK", "property-board-uk.txt", "£")]
SHORT_NAMES = [(" Avenue", " Ave"), (" Street", " St"), (" Railroad", " RR"), (" Raiload", " RR"),
	(" Station", " Stn"), (" Place", " Pl"), (" Company", " Co"), ("Community Chest", "Community Chest")]

class QuitToMenu(Exception):
	pass

class QuitProgram(Exception):
	pass

class Button(object):
	def __init__(self, label, value, rect=None, enabled=True, selected=False, newRow=False, exit=False, colour=None):
		self.label = label
		self.value = value
		self.rect = rect
		self.enabled = enabled
		self.selected = selected
		self.newRow = newRow # Start a new row when laid out automatically
		self.exit = exit # Leaves the dialog (used by automated testing)
		self.colour = colour

class UI(object):

	def __init__(self):
		pygame.init()
		self.screen = pygame.display.set_mode(WINDOW)
		pygame.display.set_caption("Property Game")
		self.clock = pygame.time.Clock()
		self.fonts = {}
		self.game = None
		self.names = []
		self.isHuman = []
		self.currency = "$"
		self.log = []
		self.dice = None
		self.speed = 1
		self.paused = False
		self.hover = None
		self.panelButtons = []
		self.statusText = None
		self.turnLimit = None # Used by automated testing
		self.logsSinceDraw = 0

	# Drawing helpers

	def Font(self, size):
		if size not in self.fonts:
			self.fonts[size] = pygame.font.Font(None, size)
		return self.fonts[size]

	def Text(self, text, pos, size=20, colour=BLACK, centre=False, right=False):
		surface = self.Font(size).render(text, True, colour)
		x, y = pos
		if centre:
			x -= surface.get_width() // 2
			y -= surface.get_height() // 2
		elif right:
			x -= surface.get_width()
		self.screen.blit(surface, (x, y))
		return surface.get_width()

	def Wrap(self, text, width, size):
		font = self.Font(size)
		lines = []
		for paragraph in text.split("\n"):
			line = ""
			for word in paragraph.split(" "):
				candidate = word if line == "" else line + " " + word
				if font.size(candidate)[0] <= width or line == "":
					line = candidate
				else:
					lines.append(line)
					line = word
			lines.append(line)
		return lines

	def FitText(self, text, rect, sizes=(16, 14, 13, 12, 11)):
		# Wrap text into rect, shrinking the font until it fits
		for size in sizes:
			lines = self.Wrap(text, rect.width - 4, size)
			font = self.Font(size)
			if all(font.size(l)[0] <= rect.width - 2 for l in lines) and len(lines) * font.get_linesize() <= rect.height:
				break
		lineHeight = self.Font(size).get_linesize()
		y = rect.y + (rect.height - len(lines) * lineHeight) // 2
		for line in lines:
			self.Text(line, (rect.centerx, y + lineHeight // 2), size, centre=True)
			y += lineHeight

	def DrawButton(self, button):
		if button.selected:
			fill = SELECTED
		elif button.colour is not None:
			fill = button.colour
		elif button.enabled:
			fill = WHITE
		else:
			fill = (215, 215, 215)
		if button.enabled and button.rect.collidepoint(pygame.mouse.get_pos()):
			fill = tuple(max(0, c - 25) for c in fill)
		pygame.draw.rect(self.screen, fill, button.rect, border_radius=6)
		pygame.draw.rect(self.screen, DARK_GREY if button.enabled else GREY, button.rect, 1, border_radius=6)
		size = 20
		while size > 12 and self.Font(size).size(button.label)[0] > button.rect.width - 6:
			size -= 1
		self.Text(button.label, button.rect.center, size, BLACK if button.enabled else GREY, centre=True)

	def ShortName(self, name):
		for long, short in SHORT_NAMES:
			name = name.replace(long, short)
		return name

	def Pretty(self, text):
		# Engine logs use 0-based player numbers and card identifiers
		def Name(match):
			i = int(match.group(1))
			return self.names[i] if i < len(self.names) else match.group(0)
		text = re.sub(r'\b[Pp]layer (\d+)', Name, text)
		text = re.sub(r'card ([A-Z][A-Za-z0-9]+)', lambda m: 'card "' + re.sub(r'(?<=[a-z0-9])(?=[A-Z])', ' ', m.group(1)) + '"', text)
		return text

	def Money(self, amount):
		return "{}{}".format(self.currency, amount)

	# Board geometry

	def SpaceRect(self, i):
		b, x0, y0 = BOARD_SIZE, BOARD_X, BOARD_Y
		if i == 0: return pygame.Rect(x0 + b - CORNER, y0 + b - CORNER, CORNER, CORNER)
		if i < 10: return pygame.Rect(round(x0 + b - CORNER - i * EDGE), y0 + b - CORNER, round(EDGE), CORNER)
		if i == 10: return pygame.Rect(x0, y0 + b - CORNER, CORNER, CORNER)
		if i < 20: return pygame.Rect(x0, round(y0 + b - CORNER - (i - 10) * EDGE), CORNER, round(EDGE))
		if i == 20: return pygame.Rect(x0, y0, CORNER, CORNER)
		if i < 30: return pygame.Rect(round(x0 + CORNER + (i - 21) * EDGE), y0, round(EDGE), CORNER)
		if i == 30: return pygame.Rect(x0 + b - CORNER, y0, CORNER, CORNER)
		return pygame.Rect(x0 + b - CORNER, round(y0 + CORNER + (i - 31) * EDGE), CORNER, round(EDGE))

	def Side(self, i):
		if i % 10 == 0: return "corner"
		return ["bottom", "left", "top", "right"][i // 10]

	def BandRect(self, rect, side, depth=18):
		# The colour band is on the side facing the centre of the board
		if side == "bottom": return pygame.Rect(rect.x, rect.y, rect.width, depth)
		if side == "top": return pygame.Rect(rect.x, rect.bottom - depth, rect.width, depth)
		if side == "left": return pygame.Rect(rect.right - depth, rect.y, depth, rect.height)
		return pygame.Rect(rect.x, rect.y, depth, rect.height)

	def OuterStrip(self, rect, side, depth=5):
		# The strip on the outside edge, used to show the owner
		if side == "bottom": return pygame.Rect(rect.x, rect.bottom - depth, rect.width, depth)
		if side == "top": return pygame.Rect(rect.x, rect.y, rect.width, depth)
		if side == "left": return pygame.Rect(rect.x, rect.y, depth, rect.height)
		return pygame.Rect(rect.right - depth, rect.y, depth, rect.height)

	def CellAreas(self, i):
		# Split an edge space into (text area, token area). Text sits next to the colour
		# band, on the side facing the centre, and tokens on the outer side.
		rect = self.SpaceRect(i)
		side = self.Side(i)
		inner = rect
		if self.game.board[i].get('type') == 'property':
			inner = self.RemainingRect(rect, self.BandRect(rect, side))
		inner = inner.inflate(-2, -4)
		if side in ("bottom", "top"):
			tokenHeight = 30
			if side == "bottom":
				return pygame.Rect(inner.x, inner.y, inner.width, inner.height - tokenHeight), pygame.Rect(inner.x, inner.bottom - tokenHeight, inner.width, tokenHeight)
			return pygame.Rect(inner.x, inner.y + tokenHeight, inner.width, inner.height - tokenHeight), pygame.Rect(inner.x, inner.y, inner.width, tokenHeight)
		tokenWidth = 18
		if side == "left":
			return pygame.Rect(inner.x + tokenWidth, inner.y, inner.width - tokenWidth, inner.height), pygame.Rect(inner.x, inner.y, tokenWidth, inner.height)
		return pygame.Rect(inner.x, inner.y, inner.width - tokenWidth, inner.height), pygame.Rect(inner.right - tokenWidth, inner.y, tokenWidth, inner.height)

	def JailBox(self):
		rect = self.SpaceRect(10)
		return pygame.Rect(rect.right - 64, rect.y, 64, 64)

	# Drawing the game

	def Draw(self):
		self.screen.fill(BACKGROUND)
		if self.game is not None:
			self.DrawBoard()
			self.DrawPanel()

	def DrawBoard(self):
		game = self.game
		pygame.draw.rect(self.screen, BOARD_COLOUR, (BOARD_X, BOARD_Y, BOARD_SIZE, BOARD_SIZE))
		for i in range(len(game.board)):
			self.DrawSpace(i)
		pygame.draw.rect(self.screen, BLACK, (BOARD_X, BOARD_Y, BOARD_SIZE, BOARD_SIZE), 2)
		self.DrawCentre()
		self.DrawTokens()

	def DrawSpace(self, i):
		game = self.game
		space = game.board[i]
		rect = self.SpaceRect(i)
		side = self.Side(i)
		kind = space.get('type')
		pygame.draw.rect(self.screen, CELL_COLOUR, rect)

		if side == "corner":
			self.DrawCorner(i, rect, kind)
		else:
			textRect, tokenRect = self.CellAreas(i)
			if kind == 'property':
				band = self.BandRect(rect, side)
				pygame.draw.rect(self.screen, GROUP_COLOURS[space['property_group'] % len(GROUP_COLOURS)], band)
				pygame.draw.rect(self.screen, BLACK, band, 1)
				self.DrawBuildings(i, band, side)
			label = self.ShortName(space['name'])
			if kind == 'tax':
				label += "\nPay " + self.Money(-space['income'])
			elif 'price' in space:
				label += "\n" + self.Money(space['price'])
			self.FitText(label, textRect)

			owner = game.spaceOwners[i]
			if owner is not None:
				pygame.draw.rect(self.screen, PLAYER_COLOURS[owner][1], self.OuterStrip(rect, side))
			if game.spaceMortgaged[i]:
				shade = pygame.Surface(rect.size, pygame.SRCALPHA)
				shade.fill((90, 90, 90, 120))
				self.screen.blit(shade, rect.topleft)
				self.FitText("MORT-\nGAGED" if tokenRect.width < 40 else "MORTGAGED", tokenRect, (12, 11))

		if self.hover == i:
			pygame.draw.rect(self.screen, HIGHLIGHT, rect, 3)
		else:
			pygame.draw.rect(self.screen, BLACK, rect, 1)

	def RemainingRect(self, rect, band):
		if band.width == rect.width:
			if band.y == rect.y:
				return pygame.Rect(rect.x, band.bottom, rect.width, rect.height - band.height)
			return pygame.Rect(rect.x, rect.y, rect.width, rect.height - band.height)
		if band.x == rect.x:
			return pygame.Rect(band.right, rect.y, rect.width - band.width, rect.height)
		return pygame.Rect(rect.x, rect.y, rect.width - band.width, rect.height)

	def DrawBuildings(self, i, band, side):
		count = self.game.spaceBuildings[i]
		if count == 0: return
		horizontal = side in ("bottom", "top")
		if count == 5:
			hotel = band.inflate(-8, -6) if horizontal else band.inflate(-6, -8)
			pygame.draw.rect(self.screen, (130, 0, 0), hotel)
			pygame.draw.rect(self.screen, WHITE, hotel, 1)
			self.Text("H", hotel.center, 14, WHITE, centre=True)
			return
		length = band.width if horizontal else band.height
		step = length / 4.0
		for k in range(count):
			if horizontal:
				house = pygame.Rect(round(band.x + k * step + 2), band.y + 4, round(step - 4), band.height - 8)
			else:
				house = pygame.Rect(band.x + 4, round(band.y + k * step + 2), band.width - 8, round(step - 4))
			pygame.draw.rect(self.screen, (30, 150, 50), house)
			pygame.draw.rect(self.screen, BLACK, house, 1)

	def DrawCorner(self, i, rect, kind):
		if kind == 'go':
			self.Text("GO", (rect.centerx, rect.centery - 10), 44, (200, 30, 30), centre=True)
			self.Text("Collect " + self.Money(self.game.board[i]['income_on_pass']), (rect.centerx, rect.centery + 22), 16, centre=True)
		elif kind == 'jail':
			box = self.JailBox()
			pygame.draw.rect(self.screen, (250, 165, 90), box)
			for k in range(1, 4):
				x = box.x + k * box.width // 4
				pygame.draw.line(self.screen, DARK_GREY, (x, box.y), (x, box.bottom), 2)
			pygame.draw.rect(self.screen, BLACK, box, 1)
			self.Text("JAIL", (box.centerx, box.bottom - 10), 18, centre=True)
			self.Text("Just visiting", (rect.centerx, rect.bottom - 14), 16, centre=True)
		elif kind == 'free_parking':
			self.FitText("FREE\nPARKING", rect.inflate(-10, -10), (22, 20))
		elif kind == 'go_to_jail':
			self.FitText("GO TO\nJAIL", rect.inflate(-10, -10), (24, 22))

	def TokenSpots(self, i, count):
		if i is None:
			area = self.JailBox().inflate(-10, -20)
		elif i == 10:
			rect = self.SpaceRect(10)
			area = pygame.Rect(rect.x + 2, rect.y + 2, rect.width - self.JailBox().width - 4, rect.height - 30)
		elif i % 10 == 0:
			area = self.SpaceRect(i).inflate(-20, -20)
		else:
			area = self.CellAreas(i)[1]
		if area.width >= area.height:
			columns = 4
		else:
			columns = 1 if area.width < 34 else 2
		rows = (count + columns - 1) // columns
		stepX = min(15, area.width / float(min(count, columns)))
		stepY = min(15, area.height / float(rows))
		spots = []
		for k in range(count):
			c, r = k % columns, k // columns
			x = area.centerx + (c - (min(count, columns) - 1) / 2.0) * stepX
			y = area.centery + (r - (rows - 1) / 2.0) * stepY
			spots.append((int(x), int(y)))
		return spots

	def DrawTokens(self):
		game = self.game
		byPosition = {}
		for p in range(game.numPlayers):
			if game.playerBankrupt[p]: continue
			byPosition.setdefault(game.playerPositions[p], []).append(p)
		for position, players in byPosition.items():
			for p, spot in zip(players, self.TokenSpots(position, len(players))):
				pygame.draw.circle(self.screen, PLAYER_COLOURS[p][1], spot, 8)
				current = p == game.playerTurn
				pygame.draw.circle(self.screen, WHITE if current else BLACK, spot, 8, 3 if current else 1)

	def DrawCentre(self):
		game = self.game
		self.Text("PROPERTY GAME", (CENTRE.centerx, CENTRE.y + 36), 56, (170, 20, 20), centre=True)
		if self.dice is not None:
			for k, value in enumerate(self.dice):
				die = pygame.Rect(CENTRE.centerx - 56 + k * 64, CENTRE.y + 70, 48, 48)
				pygame.draw.rect(self.screen, WHITE, die, border_radius=8)
				pygame.draw.rect(self.screen, BLACK, die, 2, border_radius=8)
				for dx, dy in {1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)],
						4: [(-1, -1), (1, -1), (-1, 1), (1, 1)], 5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)],
						6: [(-1, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (1, 1)]}.get(value, []):
					pygame.draw.circle(self.screen, BLACK, (die.centerx + dx * 12, die.centery + dy * 12), 5)
		status = self.statusText or "{}'s turn".format(self.names[game.playerTurn])
		self.Text(status, (CENTRE.centerx, CENTRE.y + 140), 26, centre=True)

		logRect = pygame.Rect(CENTRE.x + 20, CENTRE.y + 165, CENTRE.width - 40, CENTRE.height - 185)
		pygame.draw.rect(self.screen, WHITE, logRect, border_radius=6)
		pygame.draw.rect(self.screen, GREY, logRect, 1, border_radius=6)
		lines = []
		for entry in self.log[-40:]:
			lines.extend(self.Wrap(entry, logRect.width - 16, 18))
		lineHeight = self.Font(18).get_linesize()
		lines = lines[-((logRect.height - 12) // lineHeight):]
		y = logRect.y + 6
		for line in lines:
			self.Text(line, (logRect.x + 8, y), 18, DARK_GREY)
			y += lineHeight

	def DrawPanel(self):
		game = self.game
		pygame.draw.rect(self.screen, PANEL_COLOUR, (PANEL_X, 10, WINDOW[0] - PANEL_X - 10, WINDOW[1] - 20), border_radius=8)
		y = 18
		cardHeight = 50 if game.numPlayers <= 6 else 44
		for p in range(game.numPlayers):
			card = pygame.Rect(PANEL_X + 8, y, WINDOW[0] - PANEL_X - 26, cardHeight)
			bankrupt = game.playerBankrupt[p]
			pygame.draw.rect(self.screen, (225, 225, 225) if bankrupt else WHITE, card, border_radius=6)
			pygame.draw.rect(self.screen, HIGHLIGHT if p == game.playerTurn else GREY, card, 3 if p == game.playerTurn else 1, border_radius=6)
			pygame.draw.circle(self.screen, PLAYER_COLOURS[p][1], (card.x + 18, card.centery), 11)
			pygame.draw.circle(self.screen, BLACK, (card.x + 18, card.centery), 11, 1)
			self.Text("{} ({})".format(self.names[p], "Human" if self.isHuman[p] else "AI"), (card.x + 36, card.y + 5), 22, GREY if bankrupt else BLACK)
			self.Text(self.Money(game.playerMoney[p]), (card.right - 10, card.y + 5), 24, GREY if bankrupt else BLACK, right=True)
			self.Text(self.PlayerSummary(p), (card.x + 36, card.y + cardHeight - 18), 16, DARK_GREY)
			y += cardHeight + 4

		self.panelButtons = []
		y += 6
		self.Text("AI speed:", (PANEL_X + 12, y + 8), 18)
		for k, (label, ms) in enumerate(SPEEDS):
			self.panelButtons.append(Button(label, ("speed", k), pygame.Rect(PANEL_X + 84 + k * 62, y, 58, 28), selected=(k == self.speed)))
		y += 34
		self.panelButtons.append(Button("Resume" if self.paused else "Pause", ("pause",), pygame.Rect(PANEL_X + 12, y, 110, 28), selected=self.paused))
		self.panelButtons.append(Button("Quit game", ("quit",), pygame.Rect(WINDOW[0] - 132, y, 110, 28)))
		for button in self.panelButtons:
			self.DrawButton(button)
		self.panelBottom = y + 40

		if self.hover is not None:
			self.DrawSpaceInfo(self.hover, pygame.Rect(PANEL_X + 8, WINDOW[1] - 190, WINDOW[0] - PANEL_X - 26, 172))

	def PlayerSummary(self, p):
		game = self.game
		if game.playerBankrupt[p]:
			return "Bankrupt"
		owned = [s for s, o in enumerate(game.spaceOwners) if o == p]
		houses = sum(game.spaceBuildings[s] for s in owned if game.spaceBuildings[s] < 5)
		hotels = sum(1 for s in owned if game.spaceBuildings[s] == 5)
		parts = ["{} properties".format(len(owned))]
		if houses: parts.append("{} houses".format(houses))
		if hotels: parts.append("{} hotels".format(hotels))
		if game.playerTimeInJail[p] is not None: parts.append("in jail")
		cards = len(game.playerGetOutOfJailCards[p])
		if cards: parts.append("{} jail card{}".format(cards, "s" if cards > 1 else ""))
		return ", ".join(parts)

	def DrawSpaceInfo(self, i, rect):
		game = self.game
		space = game.board[i]
		pygame.draw.rect(self.screen, WHITE, rect, border_radius=6)
		pygame.draw.rect(self.screen, GREY, rect, 1, border_radius=6)
		kind = space.get('type')
		title = space['name']
		if kind == 'property':
			pygame.draw.rect(self.screen, GROUP_COLOURS[space['property_group'] % len(GROUP_COLOURS)], (rect.x, rect.y, rect.width, 26), border_top_left_radius=6, border_top_right_radius=6)
		self.Text(title, (rect.centerx, rect.y + 13), 22, centre=True)
		lines = []
		if kind == 'property':
			rent = space['rent']
			lines.append("Price {}   Houses {} each   Mortgage {}".format(self.Money(space['price']), self.Money(space['building_costs']), self.Money(space['mortgage'])))
			lines.append("Rent {}  (full set {})".format(self.Money(rent[0]), self.Money(rent[0] * 2)))
			lines.append("Houses 1-4: {}".format(", ".join(self.Money(r) for r in rent[1:5])))
			lines.append("Hotel: {}".format(self.Money(rent[5])))
		elif kind == 'station':
			lines.append("Price {}   Mortgage {}".format(self.Money(space['price']), self.Money(space['mortgage'])))
			lines.append("Rent with 1-4 stations: {}".format(", ".join(self.Money(r) for r in space['rent'])))
		elif kind == 'utility':
			lines.append("Price {}   Mortgage {}".format(self.Money(space['price']), self.Money(space['mortgage'])))
			lines.append("Rent: {} x dice with one, {} x with both".format(*space['multiplier']))
		elif kind == 'tax':
			lines.append("Pay {}".format(self.Money(-space['income'])))
		elif kind in ('chance', 'community'):
			lines.append("Draw a card")
		if 'price' in space:
			owner = game.spaceOwners[i]
			status = "Unowned" if owner is None else "Owned by " + self.names[owner]
			if game.spaceMortgaged[i]: status += " (mortgaged)"
			buildings = game.spaceBuildings[i]
			if buildings == 5: status += ", hotel"
			elif buildings: status += ", {} house{}".format(buildings, "s" if buildings > 1 else "")
			lines.append(status)
		y = rect.y + 34
		for line in lines:
			self.Text(line, (rect.x + 10, y), 18)
			y += 22

	# Input

	def ProcessEvent(self, event, buttons):
		# Returns the value of a clicked dialog button, or None
		if event.type == pygame.QUIT:
			raise QuitProgram()
		if event.type == pygame.MOUSEMOTION and self.game is not None:
			self.hover = None
			for i in range(len(self.game.board)):
				if self.SpaceRect(i).collidepoint(event.pos):
					self.hover = i
		if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and self.game is not None:
			self.paused = not self.paused
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
			for button in buttons:
				if button.enabled and button.rect is not None and button.rect.collidepoint(event.pos):
					return button
			for button in self.panelButtons if self.game is not None else []:
				if button.rect.collidepoint(event.pos):
					if button.value[0] == "speed":
						self.speed = button.value[1]
					elif button.value[0] == "pause":
						self.paused = not self.paused
					elif button.value[0] == "quit":
						if self.Confirm("Quit this game?", ["The game will be abandoned."]):
							raise QuitToMenu()
		return None

	def Choose(self, buttons, title=None, lines=(), big=False, extraDraw=None):
		"""
		Wait for the user to click one of buttons and return its value. With a title,
		the buttons are shown in a dialog over the board; big dialogs fill the centre.
		Buttons without a rect are laid out along the bottom of the dialog.
		"""
		dialog = self.LayoutDialog(buttons, title, lines, big) if title is not None else None
		while True:
			for event in pygame.event.get():
				clicked = self.ProcessEvent(event, buttons)
				if clicked is not None:
					return clicked.value
			self.Draw()
			if dialog is not None:
				self.DrawDialog(dialog, title, lines)
			if extraDraw is not None:
				extraDraw()
			for button in buttons:
				self.DrawButton(button)
			pygame.display.flip()
			self.clock.tick(30)

	def LayoutDialog(self, buttons, title, lines, big):
		width = CENTRE.width - 40
		wrapped = []
		for line in lines:
			wrapped.extend(self.Wrap(line, width - 30, 20))
		rows = []
		for button in buttons:
			if button.rect is not None: continue
			if not rows or button.newRow:
				rows.append([])
			rows[-1].append(button)
		# Split rows that are too wide
		fitted = []
		for row in rows:
			current, used = [], 0
			for button in row:
				w = max(60, self.Font(20).size(button.label)[0] + 24)
				if current and used + w > width - 30:
					fitted.append(current)
					current, used = [], 0
				current.append((button, w))
				used += w + 8
			if current: fitted.append(current)
		if big:
			rect = CENTRE.inflate(-20, -20)
		else:
			height = 60 + len(wrapped) * 22 + len(fitted) * 42 + 10
			rect = pygame.Rect(0, 0, width, height)
			rect.center = CENTRE.center
		y = rect.bottom - 10 - len(fitted) * 42
		for row in fitted:
			total = sum(w for b, w in row) + 8 * (len(row) - 1)
			x = rect.centerx - total // 2
			for button, w in row:
				button.rect = pygame.Rect(x, y + 4, w, 34)
				x += w + 8
			y += 42
		return rect

	def DrawDialog(self, rect, title, lines):
		shade = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)
		shade.fill((0, 0, 0, 90))
		self.screen.blit(shade, (BOARD_X, BOARD_Y))
		pygame.draw.rect(self.screen, WHITE, rect, border_radius=10)
		pygame.draw.rect(self.screen, DARK_GREY, rect, 2, border_radius=10)
		self.Text(title, (rect.centerx, rect.y + 24), 28, centre=True)
		y = rect.y + 48
		for line in lines:
			for wrapped in self.Wrap(line, rect.width - 30, 20):
				self.Text(wrapped, (rect.x + 15, y), 20)
				y += 22

	def DialogArea(self, lines=()):
		# Where big dialogs can place their own rows of buttons, below the text lines
		rect = CENTRE.inflate(-20, -20)
		textHeight = sum(len(self.Wrap(line, rect.width - 30, 20)) for line in lines) * 22
		top = rect.y + 50 + textHeight + (8 if textHeight else 0)
		return pygame.Rect(rect.x + 15, top, rect.width - 30, rect.bottom - 60 - top)

	def Message(self, title, lines=()):
		self.Choose([Button("OK", True, exit=True)], title, list(lines))

	def Confirm(self, title, lines=(), yes="Yes", no="No"):
		return self.Choose([Button(yes, True), Button(no, False, exit=True)], title, list(lines))

	def AskAmount(self, title, lines, value, minimum, maximum, okLabel, cancelLabel=None, steps=(1, 10, 100)):
		# Returns the chosen amount, or None if cancelled
		value = max(minimum, min(value, maximum))
		while True:
			buttons = []
			for step in reversed(steps):
				buttons.append(Button("-{}".format(step), -step, enabled=value - step >= minimum))
			for step in steps:
				buttons.append(Button("+{}".format(step), step, enabled=value + step <= maximum))
			buttons.append(Button(okLabel.format(value), "ok", newRow=True, exit=True))
			if cancelLabel is not None:
				buttons.append(Button(cancelLabel, "cancel", exit=True))
			choice = self.Choose(buttons, title, list(lines))
			if choice == "ok": return value
			if choice == "cancel": return None
			value += choice

	# Game flow

	def Wait(self, milliseconds):
		# Let AI moves be seen, while keeping the window responsive
		end = pygame.time.get_ticks() + milliseconds
		while pygame.time.get_ticks() < end or self.paused:
			for event in pygame.event.get():
				self.ProcessEvent(event, [])
			self.Draw()
			if self.paused:
				self.Text("Paused (space to resume)", (CENTRE.centerx, CENTRE.y + 160), 22, (170, 20, 20), centre=True)
			pygame.display.flip()
			self.clock.tick(60)

	def AddLog(self, event):
		match = re.match(r'Player \d+ rolled a (\d) and a (\d)', event)
		if match:
			self.dice = (int(match.group(1)), int(match.group(2)))
		self.log.append(self.Pretty(event))
		milliseconds = SPEEDS[self.speed][1]
		if milliseconds > 0 and self.game is not None and not self.isHuman[self.game.playerTurn]:
			self.Wait(milliseconds)
		else:
			# Keep the window responsive during fast play
			self.logsSinceDraw += 1
			if self.logsSinceDraw >= 25:
				self.logsSinceDraw = 0
				self.Wait(0)

	def Setup(self):
		numPlayers = 3
		kinds = [True] + [False] * 7
		board = 1
		while True:
			buttons = []
			left, top = 330, 150
			buttons.append(Button("-", ("players", -1), pygame.Rect(left + 230, top, 40, 36), enabled=numPlayers > 2))
			buttons.append(Button("+", ("players", 1), pygame.Rect(left + 320, top, 40, 36), enabled=numPlayers < 8))
			for p in range(numPlayers):
				y = top + 60 + p * 44
				buttons.append(Button("Human", ("kind", p, True), pygame.Rect(left + 230, y, 100, 36), selected=kinds[p]))
				buttons.append(Button("AI", ("kind", p, False), pygame.Rect(left + 340, y, 100, 36), selected=not kinds[p]))
			y = top + 60 + 8 * 44 + 10
			for k, (label, filename, currency) in enumerate(BOARDS):
				buttons.append(Button(label, ("board", k), pygame.Rect(left + 230 + k * 110, y, 100, 36), selected=(k == board)))
			for k, (label, ms) in enumerate(SPEEDS):
				buttons.append(Button(label, ("speed", k), pygame.Rect(left + 230 + k * 90, y + 50, 84, 36), selected=(k == self.speed)))
			buttons.append(Button("Start game", ("start",), pygame.Rect(left + 130, y + 120, 180, 44), colour=(190, 230, 190)))
			buttons.append(Button("Quit", ("exit",), pygame.Rect(left + 330, y + 120, 120, 44)))

			def Labels():
				self.Text("PROPERTY GAME", (WINDOW[0] // 2, 70), 72, (240, 200, 60), centre=True)
				self.Text("Players", (left, top + 8), 28, WHITE)
				self.Text(str(numPlayers), (left + 295, top + 18), 32, WHITE, centre=True)
				for p in range(numPlayers):
					y = top + 60 + p * 44
					pygame.draw.circle(self.screen, PLAYER_COLOURS[p][1], (left + 12, y + 18), 12)
					self.Text(PLAYER_COLOURS[p][0], (left + 34, y + 8), 28, WHITE)
				y = top + 60 + 8 * 44 + 10
				self.Text("Board", (left, y + 8), 28, WHITE)
				self.Text("AI speed", (left, y + 58), 28, WHITE)
				if not any(kinds[:numPlayers]):
					self.Text("All players are AI: sit back and watch", (WINDOW[0] // 2, y + 180), 22, (200, 220, 200), centre=True)

			choice = self.Choose(buttons, extraDraw=Labels)
			if choice[0] == "players": numPlayers += choice[1]
			elif choice[0] == "kind": kinds[choice[1]] = choice[2]
			elif choice[0] == "board": board = choice[1]
			elif choice[0] == "speed": self.speed = choice[1]
			elif choice[0] == "exit": raise QuitProgram()
			elif choice[0] == "start": return numPlayers, kinds[:numPlayers], board

	def Play(self, numPlayers, kinds, board):
		label, boardFile, self.currency = BOARDS[board]
		self.names = [PLAYER_COLOURS[p][0] for p in range(numPlayers)]
		self.isHuman = list(kinds)
		interfaces = [PygameHumanInterface(p, self) if kinds[p] else RandomInterface(p) for p in range(numPlayers)]
		self.log = []
		self.dice = None
		self.statusText = None
		self.game = PropertyGame(PygameGlobalInterface(self), interfaces, boardFile)
		game = self.game
		self.AddLog("{} goes first".format(self.names[game.playerTurn]))

		turns = 0
		while len(game.GetPlayersUnbankrupt()) > 1:
			if self.turnLimit is not None and turns >= self.turnLimit:
				return
			turns += 1
			p = game.playerTurn
			if game.playerBankrupt[p]:
				game.EndPlayerTurn()
				continue
			if self.isHuman[p]:
				self.BeforeRoll(p)
			game.DoTurn()
			game.EndPlayerTurn()

			# AI players can build, mortgage and trade between turns
			for q in game.GetPlayersUnbankrupt():
				if not self.isHuman[q]:
					interfaces[q].DoTrading(game)

		winners = game.GetPlayersUnbankrupt()
		title = "{} wins!".format(self.names[winners[0]]) if winners else "Everyone is bankrupt!"
		self.statusText = title
		self.Choose([Button("New game", True, exit=True)], title, ["Final money: " + self.Money(game.playerMoney[winners[0]])] if winners else [])

	def BeforeRoll(self, p):
		# A human player can build, mortgage and trade before rolling
		game = self.game
		while True:
			if game.playerBankrupt[p]: return
			area = pygame.Rect(PANEL_X + 12, self.panelBottom if hasattr(self, "panelBottom") else 560, WINDOW[0] - PANEL_X - 34, 90)
			half = (area.width - 8) // 2
			buttons = [
				Button("Roll dice", "roll", pygame.Rect(area.x, area.y, area.width, 40), colour=(190, 230, 190), exit=True),
				Button("Build / sell", "build", pygame.Rect(area.x, area.y + 46, half, 34)),
				Button("Mortgage", "mortgage", pygame.Rect(area.x + half + 8, area.y + 46, half, 34)),
				Button("Trade", "trade", pygame.Rect(area.x, area.y + 86, half, 34)),
			]
			self.statusText = "{}: roll when ready".format(self.names[p])
			choice = self.Choose(buttons)
			self.statusText = None
			if choice == "roll": return
			if choice == "build": self.ManageBuildings(p)
			if choice == "mortgage": self.ManageMortgages(p)
			if choice == "trade": self.ManageTrade(p)

	# Management dialogs, used before rolling and when raising money

	def ManageMenu(self, p):
		while not self.game.playerBankrupt[p]:
			buttons = [Button("Build / sell", "build"), Button("Mortgage", "mortgage"), Button("Trade", "trade"), Button("Done", "done", newRow=True, exit=True)]
			choice = self.Choose(buttons, "{}: build, mortgage or trade".format(self.names[p]))
			if choice == "done": return
			if choice == "build": self.ManageBuildings(p)
			if choice == "mortgage": self.ManageMortgages(p)
			if choice == "trade": self.ManageTrade(p)

	def ManageBuildings(self, p):
		game = self.game
		while True:
			groups = [g for g in game.GetCompleteHouseGroups(p) if game.IsGroupAllUnmortgaged(g)]
			if not groups:
				self.Message("Build / sell", ["{} doesn't own a complete colour set without mortgages.".format(self.names[p])])
				return
			houses, hotels = game.GetFreeBuildings()
			lines = ["{} has {}. The bank has {} houses and {} hotels. Build evenly: one house on each property before a second.".format(
				self.names[p], self.Money(game.playerMoney[p]), houses, hotels)]
			area = self.DialogArea(lines)
			buttons = []
			rows = []
			y = area.y
			for g in groups:
				group = game.propertyGroup[g]
				counts = [game.spaceBuildings[s] for s in group]
				for s in group:
					space = game.board[s]
					count = game.spaceBuildings[s]
					canAdd = count == min(counts) and count < 5 and game.playerMoney[p] >= space['building_costs']
					canSell = count == max(counts) and count > 0
					rows.append((s, y))
					buttons.append(Button("Buy " + self.Money(space['building_costs']), ("add", g, s), pygame.Rect(area.right - 190, y, 90, 22), enabled=canAdd))
					buttons.append(Button("Sell " + self.Money(space['building_costs'] // 2), ("sell", g, s), pygame.Rect(area.right - 94, y, 90, 22), enabled=canSell))
					y += 25
				y += 6
			buttons.append(Button("Done", ("done",), exit=True))

			def Rows():
				for s, rowY in rows:
					space = game.board[s]
					pygame.draw.rect(self.screen, GROUP_COLOURS[space['property_group'] % len(GROUP_COLOURS)], (area.x, rowY + 3, 16, 16))
					self.Text(space['name'], (area.x + 24, rowY + 4), 20)
					count = game.spaceBuildings[s]
					self.Text("Hotel" if count == 5 else "{} house{}".format(count, "" if count == 1 else "s"), (area.right - 290, rowY + 4), 20)

			choice = self.Choose(buttons, "Build / sell", lines, big=True, extraDraw=Rows)
			if choice[0] == "done": return
			kind, g, s = choice
			group = game.propertyGroup[g]
			total = game.NumHousesInGroup(g)[0]
			if kind == "add":
				result = game.BuildBuildings(p, g, total + 1, [s])
			else:
				result = game.BuildBuildings(p, g, total - 1, [x for x in group if x != s] + [s])
			if result[0]:
				self.Message("Not possible", [", ".join(str(r) for r in result[2])])

	def ManageMortgages(self, p):
		game = self.game
		page = 0
		while True:
			owned = [s for s, o in enumerate(game.spaceOwners) if o == p]
			if not owned:
				self.Message("Mortgage", ["{} doesn't own any property.".format(self.names[p])])
				return
			lines = ["{} has {}. Sell a group's buildings before mortgaging it; unmortgaging costs 10% interest.".format(self.names[p], self.Money(game.playerMoney[p]))]
			area = self.DialogArea(lines)
			perPage = max(1, area.height // 26)
			pages = (len(owned) + perPage - 1) // perPage
			page = min(page, pages - 1)
			buttons = []
			rows = []
			for k, s in enumerate(owned[page * perPage:(page + 1) * perPage]):
				y = area.y + k * 26
				rows.append((s, y))
				if game.spaceMortgaged[s]:
					cost = game.UnmortgageCost(s)
					buttons.append(Button("Unmortgage -" + self.Money(cost), ("unmortgage", s), pygame.Rect(area.right - 170, y, 166, 23), enabled=game.playerMoney[p] >= cost))
				else:
					free = s not in game.propertyInGroup or game.NumHousesInGroup(game.propertyInGroup[s])[0] == 0
					buttons.append(Button("Mortgage +" + self.Money(game.board[s]['mortgage']), ("mortgage", s), pygame.Rect(area.right - 170, y, 166, 23), enabled=free))
			if pages > 1:
				buttons.append(Button("Previous", ("page", -1), enabled=page > 0))
				buttons.append(Button("Next", ("page", 1), enabled=page < pages - 1))
			buttons.append(Button("Done", ("done",), exit=True))

			def Rows():
				for s, y in rows:
					space = game.board[s]
					if 'property_group' in space:
						pygame.draw.rect(self.screen, GROUP_COLOURS[space['property_group'] % len(GROUP_COLOURS)], (area.x, y + 3, 16, 16))
					self.Text(space['name'] + ("  (mortgaged)" if game.spaceMortgaged[s] else ""), (area.x + 24, y + 4), 20, DARK_GREY if game.spaceMortgaged[s] else BLACK)

			choice = self.Choose(buttons, "Mortgage", lines, big=True, extraDraw=Rows)
			if choice[0] == "done": return
			if choice[0] == "page": page += choice[1]
			if choice[0] == "mortgage": game.MortgageSpace(choice[1])
			if choice[0] == "unmortgage": game.UnmortgageSpace(choice[1])

	def ManageTrade(self, p):
		game = self.game
		others = [q for q in game.GetPlayersUnbankrupt() if q != p]
		if not others:
			return
		buttons = [Button(self.names[q], q, colour=PLAYER_COLOURS[q][1]) for q in others] + [Button("Cancel", None, newRow=True, exit=True)]
		partner = self.Choose(buttons, "Trade", ["Who does {} want to trade with?".format(self.names[p])])
		if partner is None:
			return
		offer = game.NewTrade(p, partner)
		pages = [0, 0]
		while True:
			area = self.DialogArea()
			columnWidth = (area.width - 20) // 2
			buttons = []
			perPage = 11
			for side, player in enumerate(offer.playerIds):
				x = area.x + side * (columnWidth + 20)
				tradeable = game.TradeableSpaces(player)
				numPages = max(1, (len(tradeable) + perPage - 1) // perPage)
				pages[side] = min(pages[side], numPages - 1)
				for k, s in enumerate(tradeable[pages[side] * perPage:(pages[side] + 1) * perPage]):
					label = self.ShortName(game.board[s]['name']) + (" (M)" if game.spaceMortgaged[s] else "")
					buttons.append(Button(label, ("space", side, s), pygame.Rect(x, area.y + 24 + k * 25, columnWidth, 23), selected=s in offer.spaces[side]))
				if numPages > 1:
					buttons.append(Button("<", ("page", side, -1), pygame.Rect(x, area.y + 24 + perPage * 25, 40, 23), enabled=pages[side] > 0))
					buttons.append(Button(">", ("page", side, 1), pygame.Rect(x + 44, area.y + 24 + perPage * 25, 40, 23), enabled=pages[side] < numPages - 1))
				y = area.y + 24 + perPage * 25 + 30
				for k, step in enumerate((-50, -10, 10, 50)):
					buttons.append(Button("{:+d}".format(step), ("money", side, step), pygame.Rect(x + k * (columnWidth // 4), y + 22, columnWidth // 4 - 4, 24),
						enabled=0 <= offer.money[side] + step <= game.playerMoney[player]))
				held = len(game.playerGetOutOfJailCards[player])
				if held:
					buttons.append(Button("Jail card -", ("cards", side, -1), pygame.Rect(x, y + 76, columnWidth // 2 - 4, 24), enabled=offer.jailCards[side] > 0))
					buttons.append(Button("Jail card +", ("cards", side, 1), pygame.Rect(x + columnWidth // 2, y + 76, columnWidth // 2 - 4, 24), enabled=offer.jailCards[side] < held))
			problems = [r for r in game.TradeProblems(offer) if r != "Trade is empty"]
			empty = "Trade is empty" in game.TradeProblems(offer)
			buttons.append(Button("Propose", ("propose",), enabled=not problems and not empty))
			buttons.append(Button("Cancel", ("cancel",), exit=True))

			def Columns():
				for side, player in enumerate(offer.playerIds):
					x = area.x + side * (columnWidth + 20)
					self.Text("{} gives".format(self.names[player]), (x, area.y), 24, PLAYER_COLOURS[player][1])
					y = area.y + 24 + perPage * 25 + 30
					self.Text("Cash: {} (has {})".format(self.Money(offer.money[side]), self.Money(game.playerMoney[player])), (x, y), 20)
					if len(game.playerGetOutOfJailCards[player]):
						self.Text("Get out of jail free cards: {}".format(offer.jailCards[side]), (x, y + 54), 20)
				if problems:
					self.Text(self.Pretty(problems[0]), (area.x, area.bottom - 16), 18, (180, 30, 30))

			choice = self.Choose(buttons, "Trade: {} and {}".format(self.names[p], self.names[partner]), [], big=True, extraDraw=Columns)
			if choice[0] == "cancel": return
			if choice[0] == "page": pages[choice[1]] += choice[2]
			if choice[0] == "space":
				side, s = choice[1], choice[2]
				if s in offer.spaces[side]: offer.spaces[side].remove(s)
				else: offer.spaces[side].append(s)
			if choice[0] == "money": offer.money[choice[1]] += choice[2]
			if choice[0] == "cards": offer.jailCards[choice[1]] += choice[2]
			if choice[0] == "propose":
				accepted = game.ProposeTrade(offer)
				self.Message("Trade accepted" if accepted else "Trade rejected", ["{} {} the trade.".format(self.names[partner], "accepted" if accepted else "rejected")])
				return

class PygameGlobalInterface(object):

	def __init__(self, ui):
		self.ui = ui

	def Log(self, event):
		self.ui.AddLog(event)

	def GetPlayerIdToTrade(self):
		return -1 # Trading is done from each human's turn instead

class PygameHumanInterface(PlayerInterface):

	""" A human player, asked each decision in a dialog """

	def __init__(self, playerNum, ui):
		super().__init__(playerNum)
		self.ui = ui

	def Name(self):
		return self.ui.names[self.playerNum]

	def OptionToBuy(self, spaceId, gameState):
		space = gameState.board[spaceId]
		money = gameState.playerMoney[self.playerNum]
		lines = ["{} for {}. {} has {}.".format(space['name'], self.ui.Money(space['price']), self.Name(), self.ui.Money(money))]
		if money < space['price']:
			lines.append("Buying means raising {} by mortgaging or selling buildings.".format(self.ui.Money(space['price'] - money)))
		lines.append("If not bought, it goes to auction.")
		return self.ui.Confirm("{}: buy {}?".format(self.Name(), space['name']), lines, "Buy", "Auction")

	def GetAuctionBid(self, spaceId, highestBid, highestBidder, gameState):
		space = gameState.board[spaceId]
		leader = "No bids yet" if highestBidder is None else "Highest bid: {} by {}".format(self.ui.Money(highestBid), self.ui.names[highestBidder])
		maximum = gameState.PlayerMaxMoneyThatCanBeRaised(self.playerNum)
		lines = [leader, "{} (list price {}). {} has {}, and could raise up to {}.".format(space['name'], self.ui.Money(space['price']),
			self.Name(), self.ui.Money(gameState.playerMoney[self.playerNum]), self.ui.Money(maximum))]
		if highestBid + 1 > maximum:
			self.ui.Message("{}: auction for {}".format(self.Name(), space['name']), lines + ["You can't beat the highest bid."])
			return None
		return self.ui.AskAmount("{}: auction for {}".format(self.Name(), space['name']), lines, highestBid + 1, highestBid + 1, maximum,
			"Bid " + self.ui.currency + "{}", "Pass")

	def UseGetOutOfJailCard(self, gameState):
		return self.ui.Confirm("{}: use a get out of jail free card?".format(self.Name()), ["You are in jail."], "Use card", "Not now")

	def PayJailFine(self, gameState):
		return self.ui.Confirm("{}: pay {} to leave jail?".format(self.Name(), self.ui.Money(gameState.jailFine)),
			["Or roll for a double. After three failed rolls you must pay.", "{} has {}.".format(self.Name(), self.ui.Money(gameState.playerMoney[self.playerNum]))],
			"Pay", "Roll for a double")

	def TryRaiseMoney(self, moneyNeeded, gameState):
		while True:
			money = gameState.playerMoney[self.playerNum]
			lines = ["{} needs {} but has {}.".format(self.Name(), self.ui.Money(moneyNeeded), self.ui.Money(money)),
				"Mortgage property, sell buildings or trade with another player."]
			if money >= moneyNeeded:
				lines.append("You now have enough.")
			buttons = [Button("Mortgage", "mortgage"), Button("Sell buildings", "build"), Button("Trade", "trade"),
				Button("Done" if money >= moneyNeeded else "Give up", "done", newRow=True, exit=True)]
			choice = self.ui.Choose(buttons, "{}: raise money".format(self.Name()), lines)
			if choice == "done": return
			if choice == "mortgage": self.ui.ManageMortgages(self.playerNum)
			if choice == "build": self.ui.ManageBuildings(self.playerNum)
			if choice == "trade": self.ui.ManageTrade(self.playerNum)

	def UnmortgageChoices(self, choices, gameState):
		choices = [list(c) for c in choices]
		lines = ["10% interest is due now on each. Pay off a mortgage now to avoid paying interest again later."]
		while True:
			area = self.ui.DialogArea(lines)
			buttons = []
			rows = []
			for k, (spaceId, mortgaged, interest, total) in enumerate(choices[:(area.height - 30) // 26]):
				y = area.y + k * 26
				rows.append((spaceId, y))
				buttons.append(Button("Keep mortgaged ({})".format(self.ui.Money(interest)), ("keep", k), pygame.Rect(area.right - 330, y, 160, 23), selected=mortgaged))
				buttons.append(Button("Pay off ({})".format(self.ui.Money(total)), ("pay", k), pygame.Rect(area.right - 165, y, 160, 23), selected=not mortgaged))
			bill = sum(c[2] if c[1] else c[3] for c in choices)
			buttons.append(Button("Done", ("done",), exit=True))

			def Rows():
				for spaceId, y in rows:
					self.ui.Text(gameState.board[spaceId]['name'], (area.x, y + 4), 20)
				self.ui.Text("Total to pay now: {} (has {})".format(self.ui.Money(bill), self.ui.Money(gameState.playerMoney[self.playerNum])), (area.x, area.bottom - 10), 22)

			choice = self.ui.Choose(buttons, "{}: mortgaged property received".format(self.Name()), lines, big=True, extraDraw=Rows)
			if choice[0] == "done": return choices
			choices[choice[1]][1] = choice[0] == "keep"

	def DoTrading(self, gameState):
		self.ui.ManageMenu(self.playerNum)
		return True

	def ShowTradePlayerSelect(self):
		return False # The UI offers trading on each human's turn

	def ConsiderTrade(self, offer, gameState):
		proposer = offer.playerIds[0]
		lines = self.ui.Pretty(gameState.DescribeTrade(offer)).split("\n")
		return self.ui.Confirm("{}: trade offer from {}".format(self.Name(), self.ui.names[proposer]), lines, "Accept", "Reject")

	def GetBuildingDemand(self, buildingType, available, gameState):
		amount = self.ui.AskAmount("{}: {} shortage".format(self.Name(), buildingType),
			["Only {} {}s are left, so they may be auctioned. How many does {} want to buy?".format(available, buildingType, self.Name())],
			0, 0, available, "Want {}", steps=(1,))
		return amount or 0

	def GetBuildingBid(self, buildingType, groupIds, highestBid, highestBidder, gameState):
		leader = "No bids yet" if highestBidder is None else "Highest bid: {} by {}".format(self.ui.Money(highestBid), self.ui.names[highestBidder])
		buttons = []
		for g in groupIds:
			first = gameState.board[gameState.propertyGroup[g][0]]
			buttons.append(Button(self.ui.ShortName(first['name']) + " set", g, colour=GROUP_COLOURS[first['property_group'] % len(GROUP_COLOURS)]))
		buttons.append(Button("Pass", None, newRow=True, exit=True))
		g = self.ui.Choose(buttons, "{}: auction for a {}".format(self.Name(), buildingType), [leader, "Which set would the {} go on?".format(buildingType)])
		if g is None:
			return None
		cost = gameState.board[gameState.propertyGroup[g][0]]['building_costs']
		minimum = max(highestBid + 1, cost)
		maximum = gameState.playerMoney[self.playerNum]
		if minimum > maximum:
			self.ui.Message("{}: auction for a {}".format(self.Name(), buildingType), ["{} can't afford to beat the highest bid.".format(self.Name())])
			return None
		amount = self.ui.AskAmount("{}: auction for a {}".format(self.Name(), buildingType), [leader, "Building cost {}.".format(self.ui.Money(cost))],
			minimum, minimum, maximum, "Bid " + self.ui.currency + "{}", "Pass")
		if amount is None:
			return None
		return g, amount

def Main():
	ui = UI()
	try:
		while True:
			ui.game = None
			numPlayers, kinds, board = ui.Setup()
			try:
				ui.Play(numPlayers, kinds, board)
			except QuitToMenu:
				pass
	except QuitProgram:
		pass
	pygame.quit()

if __name__ == "__main__":
	Main()
