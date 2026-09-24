import json
import random
from interfaces import *

class PropertyGame(object):

	""" 
	Simulation of a monopoly game with hooks for different interfaces 
	and training AIs.
	"""

	def __init__(self, globalInterface, playerInterfaces, boardFile="property-board-us.txt", rollForFirstPlayer=True):
		data = json.load(open(boardFile, "rt"))
		self.board = data['board']
		self.communityCards = data['community_cards']
		random.shuffle(self.communityCards)
		self.chanceCards = data['chance_cards']
		random.shuffle(self.chanceCards)
		self.jailFine = 50
		self.houseMarkers = 32
		self.hotelMarkers = 12

		self.numPlayers = len(playerInterfaces)
		self.playerInterfaces = playerInterfaces
		self.globalInterface = globalInterface
		self.playerPositions = []
		self.playerMoney = []
		self.playerTimeInJail = []
		self.playerGetOutOfJailCards = []
		self.playerBankrupt = []
		for i in range(self.numPlayers):
			self.playerPositions.append(0)
			self.playerMoney.append(1500)
			self.playerTimeInJail.append(None)
			self.playerGetOutOfJailCards.append([])
			self.playerBankrupt.append(False)
		self.spaceOwners = []
		self.spaceMortgaged = []
		self.spaceBuildings = [] # Buildings on each space: 0-4 houses, 5 means a hotel
		self.housesInBank = self.houseMarkers
		self.hotelsInBank = self.hotelMarkers
		self.boardStations = []
		self.boardUtilities = []
		self.boardJailSpaceId = None
		self.propertyGroup = {}
		self.propertyInGroup = {}

		for spaceId, space in enumerate(self.board):
			self.spaceOwners.append(None)
			self.spaceMortgaged.append(False)
			self.spaceBuildings.append(0)
			if 'type' in space:
				ty = space['type']
				if ty == "station":
					self.boardStations.append(spaceId)
				elif ty == "utility":
					self.boardUtilities.append(spaceId)
				elif ty == "property":
					inGroup = space['property_group']
					if inGroup in self.propertyGroup:
						self.propertyGroup[inGroup].append(spaceId)
					else:
						self.propertyGroup[inGroup] = [spaceId]
					self.propertyInGroup[spaceId] = inGroup

				elif ty == "jail":
					self.boardJailSpaceId = spaceId

		# Limits so trading can't stall the game. A "turn" here runs from one EndPlayerTurn
		# to the next, which includes trading between turns.
		self.maxTradeOffersPerTurn = 3
		self.maxFreeTradingPasses = 20
		self.tradeOffersThisTurn = [0] * self.numPlayers
		self.rejectedTradesThisTurn = set()

		self.playerTurn = 0
		if rollForFirstPlayer:
			self.RollForFirstPlayer()

	def RollForFirstPlayer(self, forceRolls=None):
		# Each player rolls two dice and the highest total goes first. Players who tie for
		# highest roll again. Play then passes in player order ("clockwise").
		contenders = list(range(self.numPlayers))
		rollCount = 0
		while True:
			totals = {}
			for playerId in contenders:
				if forceRolls is None:
					dieRoll1 = random.randint(1,6)
					dieRoll2 = random.randint(1,6)
				else:
					dieRoll1, dieRoll2 = forceRolls[rollCount]
				rollCount += 1
				totals[playerId] = dieRoll1 + dieRoll2
				self.globalInterface.Log("Player {} rolled a {} and a {} to decide who goes first".format(playerId, dieRoll1, dieRoll2))

			best = max(totals.values())
			contenders = [playerId for playerId in contenders if totals[playerId] == best]
			if len(contenders) == 1:
				break
			self.globalInterface.Log("{} tied on {}, so roll again".format(" and ".join("Player {}".format(playerId) for playerId in contenders), best))

		self.playerTurn = contenders[0]
		self.globalInterface.Log("Player {} goes first".format(self.playerTurn))
		return self.playerTurn

	def DoTurn(self, forceRolls=None):

		assert not self.playerBankrupt[self.playerTurn]
		justReleasedFromJail = False

		if self.playerTimeInJail[self.playerTurn] is not None and len(self.playerGetOutOfJailCards[self.playerTurn]) > 0:
			response = self.playerInterfaces[self.playerTurn].UseGetOutOfJailCard(self)
			if response:
				self.globalInterface.Log("Player {} used their get out of jail card".format(self.playerTurn))
				goojc = self.playerGetOutOfJailCards[self.playerTurn].pop()
				self.ReturnCardToDeck(goojc, goojc['deck'])
				self.ReleaseFromJail(self.playerTurn)

		if self.playerTimeInJail[self.playerTurn] is not None:
			response = self.playerInterfaces[self.playerTurn].PayJailFine(self)
			if response:
				self.globalInterface.Log("Player {} paid {} to be released".format(self.playerTurn, self.jailFine))
				bankrupted = self.EnsurePlayment(self.playerTurn, self.jailFine)
				if bankrupted: return
				self.ReleaseFromJail(self.playerTurn)

		for i in range(3): # Roll count

			assert not self.playerBankrupt[self.playerTurn]
			if forceRolls is None:
				dieRoll1 = random.randint(1,6)
				dieRoll2 = random.randint(1,6)
			else:
				dieRoll1 = forceRolls[i][0]
				dieRoll2 = forceRolls[i][1]
			rolledDouble = dieRoll1==dieRoll2
			self.globalInterface.Log("Player {} rolled a {} and a {}".format(self.playerTurn, dieRoll1, dieRoll2))

			# Handle if player is in jail
			if self.playerTimeInJail[self.playerTurn] is not None:
				if rolledDouble:
					self.globalInterface.Log("Player {} is in jail and rolled a double to be released".format(self.playerTurn))
					self.ReleaseFromJail(self.playerTurn)
					justReleasedFromJail = True
				else:
					self.globalInterface.Log("Player {} is in jail and didn't roll a double".format(self.playerTurn))
					self.playerTimeInJail[self.playerTurn] += 1

					if self.playerTimeInJail[self.playerTurn] >= 3:
						# Player must pay fine on third attempt
						self.globalInterface.Log("Player {} paid {} to be released".format(self.playerTurn, self.jailFine))
						bankrupted = self.EnsurePlayment(self.playerTurn, self.jailFine)
						if bankrupted: return
						self.ReleaseFromJail(self.playerTurn)
					else:
						break

			if rolledDouble and i == 2:
				self.globalInterface.Log("Rolled double three times in a row, go to jail for speeding")
				self.GoDirectlyToJail(self.playerTurn)
				break
			
			startSpaceId = self.playerPositions[self.playerTurn]
			startSpace = self.board[startSpaceId]

			via, destinationSpaceId = self.PlanMove(self.playerTurn, dieRoll1+dieRoll2)
			destinationSpace = self.board[destinationSpaceId]

			self.globalInterface.Log("Player {} moved from {} to {}".format(self.playerTurn, startSpace['name'], destinationSpace['name']))

			# Check if we pass go
			for spaceId in via:
				space = self.board[spaceId]

				if 'income_on_pass' in space:
					self.playerMoney[self.playerTurn] += space['income_on_pass']
					self.globalInterface.Log("Passed {}, gained {}".format(space['name'], space['income_on_pass']))

			self.playerPositions[self.playerTurn] = destinationSpaceId

			turnEnded = self.PlayerLandedOnSpace(self.playerTurn, destinationSpaceId, dieRoll1+dieRoll2)

			if turnEnded:
				break
			if justReleasedFromJail:
				break
			if self.playerBankrupt[self.playerTurn]:
				break
			activePlayers = self.GetPlayersUnbankrupt() # Players can bankcrupt during an auction
			if len(activePlayers) < 2:
				break # Game effectively over, so end turn
			if not rolledDouble:
				break # End turn if not a double roll
			else:
				self.globalInterface.Log("Continuing turn as we rolled a double")

	def PlayerLandedOnSpace(self, playerId, destinationSpaceId, diceRoll, extraRent=False):
		# Immediate effects of landing on space

		destinationSpace = self.board[destinationSpaceId]
		turnEnded = False

		if 'type' in destinationSpace:
			ty = destinationSpace['type']


			if ty == 'go':
				self.playerMoney[playerId] += destinationSpace['income_on_pass']
				self.globalInterface.Log("Landed on {}, gained {}".format(destinationSpace['name'], destinationSpace['income_on_pass']))

			elif ty =='tax':
				self.globalInterface.Log("Landed on {}, has to pay {}".format(destinationSpace['name'], -destinationSpace['income']))
				bankrupted = self.EnsurePlayment(playerId, -destinationSpace['income'], 'bank')
				if bankrupted: turnEnded = True
				# US boards pre-2008 had a choice of 10% tax choice. This seems to have been removed.

			elif ty in ['property', 'station', 'utility']:
				self.PlayerLandedOnPurchasable(playerId, destinationSpaceId, diceRoll, extraRent)

			elif ty == "chance":
				turnEnded = self.PlayerLandedOnChanceCommunity(playerId, destinationSpaceId, 'chance')

			elif ty == "community":
				turnEnded = self.PlayerLandedOnChanceCommunity(playerId, destinationSpaceId, 'community')

			elif ty == "jail":
				# Just visiting!
				pass

			elif ty == "free_parking":
				pass

			elif ty == "go_to_jail":
				self.GoDirectlyToJail(playerId)
				turnEnded = True
			else:
				raise RuntimeError("Unknown space type")

		return turnEnded

	def PlayerLandedOnPurchasable(self, playerId, destinationSpaceId, diceRoll, extraRent=False):

		ownerId = self.spaceOwners[destinationSpaceId]
		destinationSpace = self.board[destinationSpaceId]

		if ownerId is not None:
			# Already owned

			if playerId != ownerId and not self.spaceMortgaged[destinationSpaceId]: # Don't pay rent on your own properties
				rent = self.CalcRent(playerId, destinationSpaceId, diceRoll, extraRent)
				self.globalInterface.Log("Landed on {}, and has to pay {} to player {}".format(destinationSpace['name'], rent, ownerId))

				self.EnsurePlayment(playerId, rent, ownerId) # Player needs to raise some money

		else:
			# Not owned
			accepted = False
			price = destinationSpace['price']

			if self.playerMoney[playerId] >= price or self.PlayerMaxMoneyThatCanBeRaised(playerId) >= price:
				# Offer the property at full price. Only if the player wants it do they
				# have to raise any cash they are short (by mortgaging or selling buildings).
				accepted = self.playerInterfaces[playerId].OptionToBuy(destinationSpaceId, self)

				if accepted and self.playerMoney[playerId] < price:
					self.globalInterface.Log("Player {} needs to raise cash to buy {}".format(playerId, destinationSpace['name']))
					self.PlayerTryRaiseMoney(playerId, price)
					if self.playerMoney[playerId] < price:
						self.globalInterface.Log("Player {} did not raise enough to buy {}".format(playerId, destinationSpace['name']))
						accepted = False
			else:
				self.globalInterface.Log("Player {} cannot afford {}".format(playerId, destinationSpace['name']))

			if accepted:
				self.playerMoney[playerId] -= destinationSpace['price']
				self.spaceOwners[destinationSpaceId] = playerId
				self.globalInterface.Log("Player {} bought {}".format(playerId, destinationSpace['name']))
			else:
				self.AuctionProperty(destinationSpaceId)

		backrupted = self.playerBankrupt[playerId]
		return backrupted

	def PlayerLandedOnChanceCommunity(self, playerId, spaceId, deck):
		
		turnEnded = False
		drawCard = None
		if deck == 'chance':
			drawCard = self.chanceCards.pop(0)
		else:
			drawCard = self.communityCards.pop(0)

		self.globalInterface.Log("Player {} received {} card {}".format(playerId, deck, drawCard['name']))
		
		if 'move_to' in drawCard:

			if drawCard['move_to'] == 'jail':

				self.GoDirectlyToJail(playerId)			
				turnEnded = True

			else:
				destinationId = drawCard['move_to']

				cursor = self.playerPositions[playerId]
				while (isinstance(destinationId, int) and cursor != destinationId) or \
					(destinationId == 'utility' and self.board[cursor]['type'] != 'utility') or \
					(destinationId == 'station' and self.board[cursor]['type'] != 'station'):

					cursor += 1
					if cursor >= len(self.board):
						cursor = 0

					space = self.board[cursor]
					if 'income_on_pass' in space and cursor != destinationId:
						self.playerMoney[playerId] += space['income_on_pass']
						self.globalInterface.Log("Passed {}, gained {}".format(space['name'], space['income_on_pass']))

				diceTotal = None
				if destinationId == 'utility' and self.spaceOwners[cursor] is not None:
					dieRoll1 = random.randint(1,6)
					dieRoll2 = random.randint(1,6)
					diceTotal = dieRoll1 + dieRoll2
					self.globalInterface.Log("Player {} rolled a {} and a {}".format(playerId, dieRoll1, dieRoll2))

				self.playerPositions[playerId] = cursor
				extraRent = destinationId in ['utility', 'station']
				turnEnded = self.PlayerLandedOnSpace(playerId, cursor, diceTotal, extraRent=extraRent)

		if 'income' in drawCard:
			amount = drawCard['income']
			if amount > 0:	
				self.globalInterface.Log("Player {} gets {} money".format(playerId, amount))
				self.playerMoney[playerId] += amount
			else:
				self.globalInterface.Log("Player {} must play {} money".format(playerId, -amount))
				bankrupted = self.EnsurePlayment(playerId, -amount, 'bank')
				if bankrupted: turnEnded = True

		if 'income_per_player' in drawCard:
			amount = drawCard['income_per_player']
			if amount > 0:	
				self.globalInterface.Log("Player {} gets {} money from each player".format(playerId, amount))
				for plId in range(self.numPlayers):
					if plId == playerId or self.playerBankrupt[plId]: continue
					self.EnsurePlayment(plId, amount, playerId)
			else:
				self.globalInterface.Log("Player {} must pay {} to each player".format(playerId, -amount))
				for plId in range(self.numPlayers):
					if plId == playerId or self.playerBankrupt[plId]: continue
					bankrupted = self.EnsurePlayment(playerId, -amount, plId)
					if bankrupted:
						turnEnded = True
						break # Nothing left to pay the remaining players

		if 'pay_per_house' in drawCard:
			count = 0
			for spaceId, buildings in enumerate(self.spaceBuildings):
				if self.spaceOwners[spaceId] == playerId and buildings < 5:
					count += buildings

			bankrupted = self.EnsurePlayment(playerId, count * drawCard['pay_per_house'], 'bank')
			if bankrupted: turnEnded = True

		if 'pay_per_hotel' in drawCard:
			count = 0
			for spaceId, buildings in enumerate(self.spaceBuildings):
				if self.spaceOwners[spaceId] == playerId and buildings == 5:
					count += 1

			bankrupted = self.EnsurePlayment(playerId, count * drawCard['pay_per_hotel'], 'bank')
			if bankrupted: turnEnded = True

		if 'relative_move' in drawCard:
			pos = self.playerPositions[playerId]
			pos += drawCard['relative_move']
			while pos < 0: pos += len(self.board)
			while pos >= len(self.board): pos -= len(self.board)
			self.playerPositions[playerId] = pos
			turnEnded = self.PlayerLandedOnSpace(playerId, pos, None)

		if 'get_out_of_jail' in drawCard:
			# Player keeps this card
			self.playerGetOutOfJailCards[playerId].append(drawCard)
		else:
			self.ReturnCardToDeck(drawCard, deck)

		return turnEnded


	def ReturnCardToDeck(self, card, deck):
		# Cards go to the bottom of their deck ('chance' or 'community')
		if deck == 'chance':
			self.chanceCards.append(card)
		else:
			self.communityCards.append(card)

	def PlanMove(self, playerId, move):

		via = []
		pos = self.playerPositions[playerId]
		for i in range(move):
			pos += 1
			if pos >= len(self.board):
				pos = 0
			if i < move-1:
				via.append(pos)
		
		return via, pos

	def GoDirectlyToJail(self, playerId):
		assert self.playerTimeInJail[playerId] is None
		self.playerPositions[playerId] = None
		self.playerTimeInJail[playerId] = 0

	def ReleaseFromJail(self, playerId):
		assert self.playerTimeInJail[playerId] is not None
		self.playerPositions[playerId] = self.boardJailSpaceId
		self.playerTimeInJail[playerId] = None

	def CalcRent(self, playerId, spaceId, diceRoll, extraRent=False):
		space = self.board[spaceId]
		ownerId = self.spaceOwners[spaceId]
		ty = space['type']
		if ty == 'property':
			# https://boardgames.stackexchange.com/questions/53743/in-monopoly-if-a-player-owns-all-of-a-set-of-properties-but-one-of-the-properti
			# Sets with mortgaged properies don't count in certain editions but we will allow them
			houses = self.NumHousesOnSpace(spaceId)
			fullGroupOwned = None

			if houses == 0:
				# Check if the full set is owned
				countOwned = 0
				propGroupId = self.propertyInGroup[spaceId]
				propGroup = self.propertyGroup[propGroupId]
				for prId in propGroup:
					if self.spaceOwners[prId] == ownerId:
						countOwned += 1
				fullGroupOwned = countOwned == len(propGroup)

				if fullGroupOwned:
					return space['rent'][0] * 2 # Rent is double in a full set

			return space['rent'][houses]

		elif ty == 'station':
			ownerHasNumStations = 0
			for stId in self.boardStations:
				# Discussion on this rule https://boardgames.stackexchange.com/questions/51432/interpretation-of-if-x-r-r-s-are-owned
				# Rent is based on the number owned by that specific player.
				if self.spaceOwners[stId] == ownerId:
					ownerHasNumStations += 1

			r = space['rent'][ownerHasNumStations-1]
			if extraRent: r *= 2
			return r

		elif ty == 'utility':
			ownerHasNumUtilities = 0
			for utId in self.boardUtilities:
				if self.spaceOwners[utId] == ownerId:
					ownerHasNumUtilities += 1
			if extraRent:
				return diceRoll * 10
			return diceRoll * space['multiplier'][ownerHasNumUtilities-1]

		raise RuntimeError("Unknown space type")
		
	def AuctionProperty(self, spaceId):

		# https://boardgames.stackexchange.com/questions/49502/what-happens-if-no-one-wants-to-buy-a-property-at-auction-in-monopoly
		space = self.board[spaceId]

		self.globalInterface.Log("Auction started for {}".format(space['name']))

		# Any non bankrupt player may bid, including one who declined to buy.
		# "The bidding may start at any price."
		def AskBid(playerId, highestBid, highestBidder):
			bid = self.playerInterfaces[playerId].GetAuctionBid(spaceId, highestBid, highestBidder, self)
			if bid is None: return None
			return int(bid), None

		highestBidder, highestBid, extra = self.OpenAuction(self.GetBiddersInTurnOrder(), AskBid)

		if highestBidder is not None:
			price = highestBid

			# Bidding too high can cause bankruptcy
			# https://boardgames.stackexchange.com/questions/39455/in-monopoly-what-happens-if-the-auction-winner-cannot-pay-his-her-bid
			bankrupted = self.EnsurePlayment(highestBidder, price, 'bank')
			if bankrupted:
				self.globalInterface.Log("Player {} could not pay for {}, it remains unowned".format(highestBidder, space['name']))
				return
			self.spaceOwners[spaceId] = highestBidder
			self.globalInterface.Log("Player {} bought {} for {}".format(highestBidder, space['name'], price))

		else:
			self.globalInterface.Log("Auction ended with no bids")

	def GetBiddersInTurnOrder(self, firstPlayerId=None):
		# Non bankrupt players, starting with firstPlayerId (default: the current player)
		if firstPlayerId is None: firstPlayerId = self.playerTurn
		out = []
		for i in range(self.numPlayers):
			playerId = (firstPlayerId + i) % self.numPlayers
			if not self.playerBankrupt[playerId]:
				out.append(playerId)
		return out

	def OpenAuction(self, bidderIds, askBid):
		# Open ascending auction. Bidders are asked in turn and may bid as many times
		# as they like, each bid beating the current highest. It ends once everyone
		# else has passed in a row since the last bid; passing does not stop a player
		# bidding again later in the same auction.
		# askBid(playerId, highestBid, highestBidder) returns (bid, extra) or None to pass.
		# Returns (highestBidder, highestBid, extra); highestBidder is None if nobody bid.
		assert len(bidderIds) >= 2
		highestBid, highestBidder, highestExtra = 0, None, None
		passesInARow = 0
		i = 0
		while True:
			needed = len(bidderIds) if highestBidder is None else len(bidderIds) - 1
			if passesInARow >= needed: break

			playerId = bidderIds[i % len(bidderIds)]
			i += 1
			if playerId == highestBidder: continue

			response = askBid(playerId, highestBid, highestBidder)
			if response is not None and response[0] > highestBid:
				highestBid, highestExtra = response
				highestBidder = playerId
				passesInARow = 0
				self.globalInterface.Log("Player {} bids {}".format(playerId, highestBid))
			else:
				passesInARow += 1

		return highestBidder, highestBid, highestExtra

	def EndPlayerTurn(self):
		self.tradeOffersThisTurn = [0] * self.numPlayers
		self.rejectedTradesThisTurn = set()
		self.playerTurn += 1
		if self.playerTurn >= self.numPlayers:
			self.playerTurn = 0

	def EnsurePlayment(self, playerOwingId, moneyNeeded, playerOwedId='bank'):
		#print ("EnsurePlayment", playerOwingId, moneyNeeded, playerOwedId)

		if self.playerMoney[playerOwingId] < moneyNeeded:
			# Even if the bank alone cannot cover it, selling property to other
			# players might, so the player always gets the chance to raise money
			self.globalInterface.Log("Player {} cannot afford to pay {} immediately".format(playerOwingId, moneyNeeded))
			self.PlayerTryRaiseMoney(playerOwingId, moneyNeeded)

		if self.playerMoney[playerOwingId] < moneyNeeded:
			self.globalInterface.Log("Player {} did not raise enough and went bankrupt".format(playerOwingId))
			self.PlayerGoesBankrupt(playerOwingId, playerOwedId)
			return True

		self.playerMoney[playerOwingId] -= moneyNeeded
		if playerOwedId != 'bank':
			self.playerMoney[playerOwedId] += moneyNeeded
		return False

	def PlayerTryRaiseMoney(self, playerId, moneyNeeded):

		# The rules are ambiguous about what actions are allowed before payment is resolved.
		# https://boardgames.stackexchange.com/questions/6472/in-monopoly-is-it-ok-for-a-third-party-to-make-a-trade-with-a-player-who-is-abo
		# Answer from Hasbro: https://boardgames.stackexchange.com/a/53545/45611
		# Property sales are allowed at any time, so the player may:
		# * Mortgage properties to the bank
		# * Sell houses back to the bank
		# * Trade with other players (properties, cash and get out of jail free cards)
		
		self.playerInterfaces[playerId].TryRaiseMoney(moneyNeeded, self)

	def PlayerMaxMoneyThatCanBeRaised(self, playerId):

		assert playerId is not None
		# Plan to sell all buildings, once per group
		totalBuildings = 0
		for groupId in self.propertyGroup:
			if self.GetGroupOwner(groupId) != playerId: continue
			if self.NumHousesInGroup(groupId)[0] == 0: continue

			impossible, numAllowed, reasons, planCost = self.SetNumBuildingsInGroup(groupId, 0, planOnly = True)
			totalBuildings -= planCost # Negative cost is money received

		# Plan to mortgage everything
		totalMortgage = 0
		for spaceId, space in enumerate(self.board):
			ownerId = self.spaceOwners[spaceId]
			if ownerId != playerId: continue
			if self.spaceMortgaged[spaceId]: continue

			totalMortgage += space["mortgage"]

		return self.playerMoney[playerId] + totalMortgage + totalBuildings


	def MortgageSpace(self, spaceId):

		assert not self.spaceMortgaged[spaceId]
		if spaceId in self.propertyInGroup:
			assert self.NumHousesInGroup(self.propertyInGroup[spaceId])[0] == 0
		space = self.board[spaceId]
		ownerId = self.spaceOwners[spaceId]
		self.playerMoney[ownerId] += space['mortgage']
		self.spaceMortgaged[spaceId] = True

	def MortgageInterest(self, spaceId):
		# 10% interest, rounded up to a whole dollar
		return (self.board[spaceId]['mortgage'] + 9) // 10

	def UnmortgageCost(self, spaceId):
		return self.board[spaceId]['mortgage'] + self.MortgageInterest(spaceId)

	def UnmortgageSpace(self, spaceId):

		assert self.spaceMortgaged[spaceId]
		if spaceId in self.propertyInGroup:
			assert self.NumHousesInGroup(self.propertyInGroup[spaceId])[0] == 0
		ownerId = self.spaceOwners[spaceId]
		cost = self.UnmortgageCost(spaceId)
		assert self.playerMoney[ownerId] >= cost
		self.playerMoney[ownerId] -= cost
		self.spaceMortgaged[spaceId] = False

	def PlayerGoesBankrupt(self, playerOwingId, playerOwedId):

		self.globalInterface.Log("Player {} goes backrupt and pays everything to {}".format(playerOwingId, playerOwedId))
		self.playerBankrupt[playerOwingId] = True

		# Remove all houses and hotels for cash (before cash is transferred)
		for spaceId, space in enumerate(self.board):
			owner = self.spaceOwners[spaceId]
			if owner == playerOwingId and spaceId in self.propertyInGroup and self.NumHousesOnSpace(spaceId) > 0:
				propGroupId = self.propertyInGroup[spaceId]
				self.SetNumBuildingsInGroup(propGroupId, 0)

		# Check all buildings have been returned
		for spaceId, owner in enumerate(self.spaceOwners):
			if owner == playerOwingId:
				assert self.spaceBuildings[spaceId] == 0

		# Transfer all cash
		if playerOwedId != 'bank':
			self.playerMoney[playerOwedId] += self.playerMoney[playerOwingId]
		self.playerMoney[playerOwingId] = 0

		# Transfer get out of jail cards
		# https://boardgames.stackexchange.com/questions/22829/do-get-out-of-jail-free-cards-have-value
		if playerOwedId != 'bank':
			self.playerGetOutOfJailCards[playerOwedId].extend(self.playerGetOutOfJailCards[playerOwingId])
		else:
			# Bank takes them, so return them to their decks
			for goojc in self.playerGetOutOfJailCards[playerOwingId]:
				self.ReturnCardToDeck(goojc, goojc['deck'])
		self.playerGetOutOfJailCards[playerOwingId] = []

		# Transfer all property to owed player
		mortgaged = []
		toauction = []
		for spaceId, space in enumerate(self.board):
			owner = self.spaceOwners[spaceId]
			if owner == playerOwingId:

				if playerOwedId != 'bank':
					self.spaceOwners[spaceId] = playerOwedId
					if self.spaceMortgaged[spaceId]:
						mortgaged.append(spaceId)

				else:
					self.spaceOwners[spaceId] = None
					self.spaceMortgaged[spaceId] = False
					toauction.append(spaceId)


		if playerOwedId != 'bank':

			# The receiving player gets to choose if they unmortgage properties
			choices = []
			for spaceId in mortgaged:
				interest = self.MortgageInterest(spaceId)
				mortgagePlusInterest = self.UnmortgageCost(spaceId)
				choices.append([spaceId, True, interest, mortgagePlusInterest])

			choices = self.playerInterfaces[playerOwedId].UnmortgageChoices(choices, self)
			
			totalBill = 0
			for spaceId, propMortgaged, interest, mortgagePlusInterest in choices:
				self.spaceMortgaged[spaceId] = propMortgaged
				if propMortgaged:
					totalBill += interest
				else:
					totalBill += mortgagePlusInterest

			# Paying for interest on properties following a bankruptcy could trigger another bankruptcy
			# https://boardgames.stackexchange.com/questions/50930/monopoly-can-you-go-bankrupt-by-having-someone-else-go-bankrupt-on-you/
			self.EnsurePlayment(playerOwedId, totalBill, 'bank')
		else:

			# If the bank is owed, the bank auctions all property.
			random.shuffle(toauction)

			for spaceId in toauction:
				space = self.board[spaceId]
				activePlayers = self.GetPlayersUnbankrupt() # Players can bankcrupt during an auction

				if len(activePlayers) > 1:
					self.globalInterface.Log("Start auction of {} with {} potential bidders".format(space['name'], len(activePlayers)))
					self.AuctionProperty(spaceId)

	def FreeTrading(self):

		show = False
		for playerId, pl in enumerate(self.playerInterfaces):
			show |= pl.ShowTradePlayerSelect()

		if show:
			while True:
				playerId = self.globalInterface.GetPlayerIdToTrade()
				if playerId == -1: break
				if self.playerBankrupt[playerId]: continue

				self.playerInterfaces[playerId].DoTrading(self)

		else:
			# All players are AIs. Stop after a limit, in case an AI never says it's finished.
			complete = False
			passes = 0
			while not complete and passes < self.maxFreeTradingPasses:
				passes += 1
				complete = True
				for playerId, pl in enumerate(self.playerInterfaces):
					if self.playerBankrupt[playerId]: continue
					complete &= self.playerInterfaces[playerId].DoTrading(self)

	def GetCompleteHouseGroups(self, ownedBy=None):
		
		completeGroups = []
		for groupId, group in self.propertyGroup.items():
			firstSpace = None
			groupOwnedBy = None
			groupCheckedMembers = []

			for spaceId in group:
				space = self.board[spaceId]
				owner = self.spaceOwners[spaceId]

				if ownedBy is not None and ownedBy != owner:
					continue
				if groupOwnedBy is not None and groupOwnedBy != owner:
					continue
				if firstSpace is None:
					firstSpace = space
					if groupOwnedBy is None:
						groupOwnedBy = owner
				
				groupCheckedMembers.append(spaceId)

			fullGroup = len(groupCheckedMembers) == len(group)
			if fullGroup:
				completeGroups.append(groupId)

		return completeGroups

	def GetGroupOwner(self, groupId):
		
		firstSpace = None
		groupOwnedBy = None
		allOwned = True
		for spaceId in self.propertyGroup[groupId]:
			owner = self.spaceOwners[spaceId]

			if firstSpace is None:
				firstSpace = spaceId
				groupOwnedBy = owner

			if owner is None:
				allOwned = False
			elif groupOwnedBy != owner:
				allOwned = False

		if allOwned:
			return groupOwnedBy
		return None

	def IsGroupAllUnmortgaged(self, groupId):
		
		group = self.propertyGroup[groupId]
		allUnmortgaged = True
		for spaceId in group:
			space = self.board[spaceId]
			mortgaged = self.spaceMortgaged[spaceId]
			if mortgaged:
				allUnmortgaged = False
				break

		return allUnmortgaged

	def NumHousesInGroup(self, groupId):
		
		group = self.propertyGroup[groupId]
		existingHouses = 0
		groupHouses = []
		for spaceId in group:
			count = self.NumHousesOnSpace(spaceId)
			existingHouses += count
			groupHouses.append([spaceId, count])

		return existingHouses, groupHouses

	def NumHousesOnSpace(self, spaceId):
		# 0-4 houses, or 5 for a hotel
		return self.spaceBuildings[spaceId]

	def GetFreeBuildings(self):
		# Number of houses and hotels left in the bank
		return self.housesInBank, self.hotelsInBank

	def CheckBuildingTotals(self):
		housesOnBoard = sum([b for b in self.spaceBuildings if b < 5])
		hotelsOnBoard = len([b for b in self.spaceBuildings if b == 5])
		assert housesOnBoard + self.housesInBank == self.houseMarkers
		assert hotelsOnBoard + self.hotelsInBank == self.hotelMarkers

	# Buying and selling houses and hotels
	def SetNumBuildingsInGroup(self, groupId, numBuildings, planOnly = False, applyPayment = True, preferredSpaces = None):
		# Changes the number of buildings on a colour group to numBuildings (a hotel counts
		# as 5), one building at a time, keeping the group even.
		# Returns (impossible, numAllowed, reasons, planCost). If the change is impossible, or
		# planOnly is set, numAllowed is how many buildings could be added or removed and
		# planCost is what that would cost (negative for a sale). Otherwise nothing is
		# planned: the change is made, numAllowed is None and planCost is 0.
		#
		# preferredSpaces is the owner's order of preference for where buildings stand
		# (any spaces in the group not listed come after, in the default order). Within the
		# even building rule, new buildings go on the most preferred property among those
		# with the fewest, and buildings are sold from the least preferred among those with
		# the most. By default, buildings go on the most expensive properties first and are
		# sold from the least expensive first.

		assert self.IsGroupAllUnmortgaged(groupId)
		groupOwner = self.GetGroupOwner(groupId)
		assert groupOwner is not None
		assert numBuildings >= 0
		group = self.propertyGroup[groupId]

		defaultOrder = sorted(group, key = lambda spaceId: -spaceId) # Expensive properties first
		if preferredSpaces is None:
			preferenceOrder = defaultOrder
		else:
			assert len(set(preferredSpaces)) == len(preferredSpaces)
			for spaceId in preferredSpaces:
				assert spaceId in group
			preferenceOrder = list(preferredSpaces) + [spaceId for spaceId in defaultOrder if spaceId not in preferredSpaces]
		priority = {spaceId: i for i, spaceId in enumerate(preferenceOrder)}

		counts = {spaceId: self.spaceBuildings[spaceId] for spaceId in group}
		existing = sum(counts.values())
		housesInBank, hotelsInBank = self.housesInBank, self.hotelsInBank
		cost = 0 # Paid to the bank, negative when selling
		changed = 0
		impossible = False
		reasons = []

		if numBuildings == existing:
			return False, None, reasons, 0

		elif numBuildings == 0:
			# Total liquidation. "All houses on one color-group may be sold at once, or they may
			# be sold one house at a time (one hotel equals five houses)". Selling a hotel
			# outright needs no houses from the bank, so this cannot fail.
			for spaceId in group:
				cost -= counts[spaceId] * self.board[spaceId]['building_costs'] // 2
				if counts[spaceId] == 5:
					hotelsInBank += 1
				else:
					housesInBank += counts[spaceId]
				counts[spaceId] = 0
			changed = existing

		elif numBuildings > existing:
			for i in range(numBuildings - existing):
				# Build on the most preferred of the properties with the fewest buildings
				spaceId = min(group, key = lambda s: (counts[s], priority[s]))
				buildingCost = self.board[spaceId]['building_costs']

				if counts[spaceId] >= 5:
					reasons.append("Too many buildings")
					impossible = True
					break
				if applyPayment and cost + buildingCost > self.playerMoney[groupOwner]:
					reasons.append("Cost is too high")
					impossible = True
					break
				if counts[spaceId] < 4:
					if housesInBank == 0:
						reasons.append("Ran out of house markers")
						impossible = True
						break
					housesInBank -= 1
				else:
					if hotelsInBank == 0:
						reasons.append("Ran out of hotel markers")
						impossible = True
						break
					hotelsInBank -= 1
					housesInBank += 4 # The hotel replaces 4 houses, which go back to the bank

				counts[spaceId] += 1
				cost += buildingCost
				changed += 1

		else:
			for i in range(existing - numBuildings):
				# Sell from the least preferred of the properties with the most buildings
				spaceId = max(group, key = lambda s: (counts[s], priority[s]))

				if counts[spaceId] == 5:
					# Breaking down a hotel needs 4 houses from the bank. What if we run out?
					# https://boardgames.stackexchange.com/questions/925/what-happens-when-you-need-to-tear-down-a-hotel-but-no-houses-are-in-the-bank-in
					# Approach used is to forbid the sale.
					if housesInBank < 4:
						reasons.append("Insufficient houses available to replace hotel")
						impossible = True
						break
					housesInBank -= 4
					hotelsInBank += 1
				else:
					housesInBank += 1

				counts[spaceId] -= 1
				cost -= self.board[spaceId]['building_costs'] // 2
				changed += 1

		if impossible or planOnly:
			return impossible, changed, reasons, cost

		assert max(counts.values()) - min(counts.values()) <= 1 # Group is even
		for spaceId in group:
			self.spaceBuildings[spaceId] = counts[spaceId]
		self.housesInBank, self.hotelsInBank = housesInBank, hotelsInBank
		self.CheckBuildingTotals()

		if applyPayment:
			if cost > 0:
				bankrupted = self.EnsurePlayment(groupOwner, cost, 'bank')
				assert not bankrupted # Checked above
			else:
				self.playerMoney[groupOwner] -= cost

		return False, None, reasons, 0

	def NextBuildingType(self, groupId):
		# Building evenly means every house in a group comes before any hotel
		existingHouses, groupHouses = self.NumHousesInGroup(groupId)
		lowest = min([g[1] for g in groupHouses])
		if lowest < 4: return 'house'
		if lowest == 4: return 'hotel'
		return None

	def BuildingsNeeded(self, groupId, numBuildings):
		# Count the houses and hotels the bank must supply to reach numBuildings
		existingHouses, groupHouses = self.NumHousesInGroup(groupId)
		counts = [g[1] for g in groupHouses]
		housesNeeded, hotelsNeeded = 0, 0
		for i in range(numBuildings - existingHouses):
			ind = counts.index(min(counts))
			if counts[ind] >= 5: break
			if counts[ind] < 4:
				housesNeeded += 1
			else:
				hotelsNeeded += 1
			counts[ind] += 1
		return housesNeeded, hotelsNeeded

	def GetBuildableGroups(self, playerId, buildingType):
		out = []
		for groupId in self.GetCompleteHouseGroups(playerId):
			if not self.IsGroupAllUnmortgaged(groupId): continue
			if self.NextBuildingType(groupId) != buildingType: continue
			out.append(groupId)
		return out

	def BuildingCapacity(self, playerId, buildingType):
		# Upper bound on how many buildings of this type a player could add
		capacity = 0
		for groupId in self.GetCompleteHouseGroups(playerId):
			if not self.IsGroupAllUnmortgaged(groupId): continue
			for spaceId, count in self.NumHousesInGroup(groupId)[1]:
				if buildingType == 'house':
					capacity += max(0, 4 - count)
				elif count < 5:
					capacity += 1
		return capacity

	def BuildBuildings(self, playerId, groupId, numBuildings, preferredSpaces = None):
		# Player purchases and sales of buildings should go through this rather than
		# SetNumBuildingsInGroup, so the building shortage rule is applied.
		# See SetNumBuildingsInGroup for preferredSpaces.
		assert self.GetGroupOwner(groupId) == playerId
		existingHouses = self.NumHousesInGroup(groupId)[0]

		if numBuildings > existingHouses:
			housesNeeded, hotelsNeeded = self.BuildingsNeeded(groupId, numBuildings)
			if housesNeeded > 0:
				freeHouses, freeHotels = self.GetFreeBuildings()
				self.ResolveBuildingShortage(playerId, 'house', housesNeeded, freeHouses)

			# Only compete for hotels if the houses needed to reach them are now available
			housesNeeded, hotelsNeeded = self.BuildingsNeeded(groupId, numBuildings)
			freeHouses, freeHotels = self.GetFreeBuildings()
			if hotelsNeeded > 0 and housesNeeded <= freeHouses:
				self.ResolveBuildingShortage(playerId, 'hotel', hotelsNeeded, freeHotels)

			if self.NumHousesInGroup(groupId)[0] >= numBuildings:
				return False, None, [], 0 # Already reached by buildings won at auction

		return self.SetNumBuildingsInGroup(groupId, numBuildings, preferredSpaces = preferredSpaces)

	def ResolveBuildingShortage(self, requesterId, buildingType, needed, available):

		# "If there are a limited number of houses and hotels available and two or more
		# players wish to buy more than the Bank has, the houses or hotels must be sold
		# at auction to the highest bidder."
		# Each building is auctioned individually. A bid must be at least the building
		# cost of the group it will go on, and the winner builds on that group at once.
		# If the bank has none, players must wait until some are returned.
		if available == 0: return

		others = {}
		for plId in self.GetPlayersUnbankrupt():
			if plId == requesterId: continue
			capacity = self.BuildingCapacity(plId, buildingType)
			if capacity > 0: others[plId] = capacity
		if needed + sum(others.values()) <= available:
			return # No shortage is possible, so don't ask anyone

		demand = {requesterId: needed}
		for plId, capacity in others.items():
			wanted = int(self.playerInterfaces[plId].GetBuildingDemand(buildingType, available, self))
			wanted = max(0, min(wanted, capacity))
			if wanted > 0: demand[plId] = wanted
		if len(demand) < 2 or sum(demand.values()) <= available:
			return # Enough to go round

		self.globalInterface.Log("Shortage of {}s: {} available, players want {}".format(buildingType, available, sum(demand.values())))

		while True:
			freeHouses, freeHotels = self.GetFreeBuildings()
			free = freeHouses if buildingType == 'house' else freeHotels
			if free == 0: break

			bidderIds = []
			for plId in self.GetBiddersInTurnOrder(requesterId):
				if demand.get(plId, 0) <= 0: continue
				if len(self.GetBuildableGroups(plId, buildingType)) == 0: continue
				bidderIds.append(plId)

			if len(bidderIds) < 2:
				break # No longer contested, so remaining buildings sell at the normal price

			def AskBid(plId, highestBid, highestBidder):
				groups = self.GetBuildableGroups(plId, buildingType)
				# A bid is (groupId, amount), optionally followed by the bidder's order of
				# preference for where the building goes (see SetNumBuildingsInGroup)
				bid = self.playerInterfaces[plId].GetBuildingBid(buildingType, groups, highestBid, highestBidder, self)
				if bid is None: return None
				bidGroupId, amount = bid[0], int(bid[1])
				preferredSpaces = bid[2] if len(bid) > 2 else None
				if bidGroupId not in groups: return None
				group = self.propertyGroup[bidGroupId]
				if preferredSpaces is not None and (len(set(preferredSpaces)) != len(preferredSpaces) or any(s not in group for s in preferredSpaces)):
					return None
				cost = self.board[group[0]]['building_costs']
				if amount < cost or amount > self.playerMoney[plId]: return None
				return amount, (bidGroupId, preferredSpaces)

			self.globalInterface.Log("Auction started for a {}".format(buildingType))
			winnerId, price, winningBid = self.OpenAuction(bidderIds, AskBid)
			if winnerId is None:
				break # Nobody bid, so remaining buildings sell at the normal price
			winGroupId, winPreferredSpaces = winningBid

			existing = self.NumHousesInGroup(winGroupId)[0]
			impossible, numAllowed, reasons, planCost = self.SetNumBuildingsInGroup(winGroupId, existing + 1, applyPayment = False, preferredSpaces = winPreferredSpaces)
			assert not impossible
			bankrupted = self.EnsurePlayment(winnerId, price, 'bank')
			assert not bankrupted # Bids are limited to cash in hand
			demand[winnerId] -= 1
			self.globalInterface.Log("Player {} won a {} at auction for {}".format(winnerId, buildingType, price))

	def GetPlayersUnbankrupt(self):
		out = []
		for i, b in enumerate(self.playerBankrupt):
			if not b:
				out.append(i)
		return out
	
	# Trading
	# "Unimproved properties, railroads and utilities (but not buildings) may be sold
	# to any player as a private transaction for any amount the owner can get; however,
	# no property can be sold to another player if buildings are standing on any
	# properties of that color-group." Get out of jail free cards may also be sold,
	# and cash can be part of a deal, but "no player may borrow from or lend money to
	# another player", so a trade only exchanges things the players hold now.

	def NewTrade(self, proposerId, recipientId):
		return TradeOffer(proposerId, recipientId)

	def CounterOffer(self, offer):
		# A counter-offer is a fresh trade from the recipient back to the proposer, starting
		# from the original terms, for the recipient to change and propose. The original
		# offer counts as rejected.
		counter = TradeOffer(offer.playerIds[1], offer.playerIds[0])
		counter.spaces = [list(offer.spaces[1]), list(offer.spaces[0])]
		counter.money = [offer.money[1], offer.money[0]]
		counter.jailCards = [offer.jailCards[1], offer.jailCards[0]]
		return counter

	def TradeableSpaces(self, playerId):
		out = []
		for spaceId, ownerId in enumerate(self.spaceOwners):
			if ownerId != playerId: continue
			if spaceId in self.propertyInGroup and self.NumHousesInGroup(self.propertyInGroup[spaceId])[0] != 0: continue
			out.append(spaceId)
		return out

	def TradeInterestDue(self, offer, side):
		# Interest the player on this side must pay on mortgaged spaces they receive
		interest = 0
		for spaceId in offer.spaces[1 - side]:
			if self.spaceMortgaged[spaceId]:
				interest += self.MortgageInterest(spaceId)
		return interest

	def TradeSignature(self, offer):
		return (tuple(offer.playerIds), tuple(tuple(sorted(sp)) for sp in offer.spaces), tuple(offer.money), tuple(offer.jailCards))

	def TradeProblems(self, offer, checkLimits=True):
		# Returns a list of reasons the trade is not allowed (empty if allowed). checkLimits
		# also applies the limits on proposing trades, which stop trading stalling the game.
		reasons = []
		proposerId, recipientId = offer.playerIds
		if proposerId == recipientId:
			return ["Cannot trade with yourself"]
		for playerId in offer.playerIds:
			if playerId < 0 or playerId >= self.numPlayers or self.playerBankrupt[playerId]:
				return ["Player {} cannot trade".format(playerId)]

		if sum([len(sp) for sp in offer.spaces]) + sum(offer.money) + sum(offer.jailCards) == 0:
			reasons.append("Trade is empty")

		for side, playerId in enumerate(offer.playerIds):
			tradeable = self.TradeableSpaces(playerId)
			if len(set(offer.spaces[side])) != len(offer.spaces[side]):
				reasons.append("Player {} lists a property twice".format(playerId))
			for spaceId in offer.spaces[side]:
				if spaceId not in tradeable:
					reasons.append("Player {} cannot trade {} (not owned, or its group has buildings)".format(playerId, self.board[spaceId]['name']))

			if offer.money[side] < 0 or offer.jailCards[side] < 0:
				reasons.append("Amounts cannot be negative")
			if offer.jailCards[side] > len(self.playerGetOutOfJailCards[playerId]):
				reasons.append("Player {} does not have {} get out of jail free cards".format(playerId, offer.jailCards[side]))

			# Cash changes hands at the same time, then interest on mortgages is due
			cashAfter = self.playerMoney[playerId] - offer.money[side] + offer.money[1 - side]
			if cashAfter < self.TradeInterestDue(offer, side):
				reasons.append("Player {} cannot afford this trade".format(playerId))

		if checkLimits:
			if self.tradeOffersThisTurn[proposerId] >= self.maxTradeOffersPerTurn:
				reasons.append("Player {} has made {} trade offers this turn, the most allowed".format(proposerId, self.maxTradeOffersPerTurn))
			if self.TradeSignature(offer) in self.rejectedTradesThisTurn:
				reasons.append("This offer was already rejected this turn")
		return reasons

	def DescribeTrade(self, offer):
		lines = []
		for side, playerId in enumerate(offer.playerIds):
			items = [self.board[spaceId]['name'] + (" (mortgaged)" if self.spaceMortgaged[spaceId] else "") for spaceId in offer.spaces[side]]
			if offer.money[side]: items.append("{} cash".format(offer.money[side]))
			if offer.jailCards[side]: items.append("{} get out of jail free card(s)".format(offer.jailCards[side]))
			if len(items) == 0: items.append("nothing")
			lines.append("Player {} gives: {}".format(playerId, ", ".join(items)))
		return "\n".join(lines)

	def ProposeTrade(self, offer):
		# Ask the recipient, and process the trade if they accept. Returns True if traded.
		reasons = self.TradeProblems(offer)
		if len(reasons) > 0:
			return False
		self.tradeOffersThisTurn[offer.playerIds[0]] += 1
		accepted = self.playerInterfaces[offer.playerIds[1]].ConsiderTrade(offer, self)
		if not accepted:
			self.rejectedTradesThisTurn.add(self.TradeSignature(offer))
			self.globalInterface.Log("Player {} rejected a trade from player {}".format(offer.playerIds[1], offer.playerIds[0]))
			return False
		self.ProcessTrade(offer)
		return True

	def ProcessTrade(self, offer):

		assert len(self.TradeProblems(offer, checkLimits=False)) == 0
		self.globalInterface.Log("Trade agreed:\n" + self.DescribeTrade(offer))

		for side, playerId in enumerate(offer.playerIds):
			otherId = offer.playerIds[1 - side]
			for spaceId in offer.spaces[side]:
				self.spaceOwners[spaceId] = otherId

			self.playerMoney[playerId] -= offer.money[side]
			self.playerMoney[otherId] += offer.money[side]

			for i in range(offer.jailCards[side]):
				self.playerGetOutOfJailCards[otherId].append(self.playerGetOutOfJailCards[playerId].pop())

		# A new owner of a mortgaged property must pay the 10% interest at once, then may
		# also pay off the mortgage. If kept mortgaged, interest is charged again when it
		# is later unmortgaged.
		for side, playerId in enumerate(offer.playerIds):
			received = [spaceId for spaceId in offer.spaces[1 - side] if self.spaceMortgaged[spaceId]]
			if len(received) == 0: continue

			interest = self.TradeInterestDue(offer, side)
			self.playerMoney[playerId] -= interest
			self.globalInterface.Log("Player {} paid {} interest on mortgaged property".format(playerId, interest))

			choices = []
			for spaceId in received:
				choices.append([spaceId, True, self.MortgageInterest(spaceId), self.UnmortgageCost(spaceId)])
			choices = self.playerInterfaces[playerId].UnmortgageChoices(choices, self)
			for spaceId, propMortgaged, interest, mortgagePlusInterest in choices:
				if propMortgaged: continue
				space = self.board[spaceId]
				if self.playerMoney[playerId] >= space['mortgage']:
					self.playerMoney[playerId] -= space['mortgage']
					self.spaceMortgaged[spaceId] = False
					self.globalInterface.Log("Player {} paid off the mortgage on {}".format(playerId, space['name']))
				else:
					self.globalInterface.Log("Player {} cannot afford to pay off the mortgage on {}".format(playerId, space['name']))

class TradeOffer(object):

	""" A trade between two players. Each side (0 = proposer, 1 = recipient) can give
	any mix of unimproved properties, cash and get out of jail free cards. """

	def __init__(self, proposerId, recipientId):
		self.playerIds = [proposerId, recipientId]
		self.spaces = [[], []] # Space IDs given by each side
		self.money = [0, 0] # Cash given by each side
		self.jailCards = [0, 0] # Get out of jail free cards given by each side

def BasicGameLoop(turnLimit = None):

	playerInterfaces = [RandomInterface(0)]
	while len(playerInterfaces) < 3:
		playerInterfaces.append(RandomInterface(len(playerInterfaces)))

	globalInterface = GlobalInterface()

	propertyGame = PropertyGame(globalInterface, playerInterfaces)

	turnCount = 0
	while True:
		if not propertyGame.playerBankrupt[propertyGame.playerTurn]:

			print ("Player {} money: {}".format(propertyGame.playerTurn, propertyGame.playerMoney[propertyGame.playerTurn]))
			propertyGame.DoTurn()

			print ("Player {} money: {}".format(propertyGame.playerTurn, propertyGame.playerMoney[propertyGame.playerTurn]))
		propertyGame.EndPlayerTurn()
		
		propertyGame.FreeTrading()

		activePlayers = propertyGame.GetPlayersUnbankrupt()
		if len(activePlayers) == 1:
			print ("Player {} wins!".format(activePlayers[0]))
			break
		elif len(activePlayers) == 0: # Possible due to one backruptcy triggering another backruptcy.
			print ("Everyone is backrupt! No-one wins!")
			break

		turnCount += 1
		if turnLimit is not None and turnCount >= turnLimit:
			break

if __name__=="__main__":

	while True:
		BasicGameLoop(1000)

