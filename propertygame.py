import json
import random

class PropertyGame(object):

	""" 
	Simulation of a monopoly game with hooks for different interfaces 
	and training AIs.
	"""

	def __init__(self, globalInterface, playerInterfaces):
		data = json.load(open("property-board-us.txt", "rt"))
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
		self.boardHouses = []
		self.boardHotels = []
		self.boardGroupBuildOrder = {}
		self.boardStations = []
		self.boardUtilities = []
		self.boardJailSpaceId = None
		self.propertyGroup = {}
		self.propertyInGroup = {}

		for spaceId, space in enumerate(self.board):
			self.spaceOwners.append(None)
			self.spaceMortgaged.append(False)
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
					if inGroup not in self.boardGroupBuildOrder:
						self.boardGroupBuildOrder[inGroup] = []

				elif ty == "jail":
					self.boardJailSpaceId = spaceId

		for i in range(self.houseMarkers):
			self.boardHouses.append(None)
		for i in range(self.hotelMarkers):
			self.boardHotels.append(None)

		self.playerTurn = random.randint(0, self.numPlayers-1)

	def DoTurn(self, forceRolls=None):

		assert not self.playerBankrupt[self.playerTurn]
		justReleasedFromJail = False

		if self.playerTimeInJail[self.playerTurn] is not None and len(self.playerGetOutOfJailCards[self.playerTurn]) > 0:
			response = self.playerInterfaces[self.playerTurn].UseGetOutOfJailCard(self)
			if response:
				self.globalInterface.Log("Player used their get out of jail card".format(self.playerTurn, self.jailFine))
				goojc = self.playerGetOutOfJailCards[self.playerTurn].pop()
				if goojc['deck'] == 'chance': # Add card to bottom of appropriate deck
					self.chanceCards.append(goojc)
				else:
					self.communityCards.append(goojc)
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

				# TODO Implement 10% tax choice (on US not UK board)

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

			#TODO a player is allowed to mortgage and sell houses here?
			if self.playerMoney[playerId] > destinationSpace['price']:
				# Allow a player to purpose the property at full price
				accepted = self.playerInterfaces[playerId].OptionToBuy(destinationSpaceId, self)
			else:
				self.globalInterface.Log("Player {} cannot automatically afford {}".format(playerId, destinationSpace['name']))

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
					if 'income_on_pass' in space:
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
					if plId != playerId: continue
					self.EnsurePlayment(plId, amount, playerId)
			else:
				self.globalInterface.Log("Player {} must pay {} to each player".format(playerId, amount))
				for plId in range(self.numPlayers):
					if plId != playerId: continue
					bankrupted = self.EnsurePlayment(playerId, amount, plId)
					if bankrupted: turnEnded = True

		if 'pay_per_house' in drawCard:
			count = 0
			for spaceId in self.boardHouses:
				ownerId = self.spaceOwners[spaceId]
				if ownerId == playerId:
					count += 1

			bankrupted = self.EnsurePlayment(playerId, count * drawCard['pay_per_house'], 'bank')
			if bankrupted: turnEnded = True

		if 'pay_per_hotel' in drawCard:
			count = 0
			for spaceId in self.boardHotels:
				ownerId = self.spaceOwners[spaceId]
				if ownerId == playerId:
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
			# Add card to bottom of deck
			if deck == 'chance':
				self.chanceCards.append(drawCard)
			else:
				self.communityCards.append(drawCard)

		return turnEnded


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
			groupHouses = 0

			if houses == 0:
				# Check if the full set is owned
				countOwned = 0
				propGroupId = self.propertyInGroup[spaceId]
				propGroup = self.propertyGroup[propGroupId]
				for prId in propGroup:
					if self.spaceOwners[prId] == ownerId:
						countOwned += 1
						groupHouses += self.NumHousesOnSpace(prId)
				fullGroupOwned = countOwned == len(propGroup)

				if groupHouses == 0 and fullGroupOwned:
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
		bids = []
		for playerId, pl in enumerate(self.playerInterfaces):
			bid = int(pl.GetActionBid(spaceId, self))
			bids.append((playerId, bid))

		bids.sort(key = lambda x: x[1])		

		# Give the property to the highest bidder, for 1 more than the second highest bid
		secondHighestBid = bids[-2][1]
		highestBid = bids[-1][1]
		highestBidder = bids[-1][0]

		if highestBid >= 1:
			# Bidding too high can cause bankrupcy
			# https://boardgames.stackexchange.com/questions/39455/in-monopoly-what-happens-if-the-auction-winner-cannot-pay-his-her-bid
			bankrupted = self.EnsurePlayment(highestBidder, secondHighestBid + 1, 'bank')
			self.spaceOwners[spaceId] = highestBidder
			self.globalInterface.Log("Player {} bought {} for {}".format(highestBidder, space['name'], secondHighestBid + 1))

		else:
			self.globalInterface.Log("Auction ended with no bids")

	def EndPlayerTurn(self):
		self.playerTurn += 1
		if self.playerTurn >= self.numPlayers:
			self.playerTurn = 0

	def EnsurePlayment(self, playerOwingId, moneyNeeded, playerOwedId='bank'):
		#print ("EnsurePlayment", playerOwingId, moneyNeeded, playerOwedId)

		if self.playerMoney[playerOwingId] < moneyNeeded:
			self.globalInterface.Log("Player {} cannot afford to pay {}".format(playerOwingId, moneyNeeded))
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
		# Some actions are listed as "any time" but we have gone for a fairly strict
		# interpretation by only allowing:
		# * Mortgaging properties to the bank
		# * Selling houses back to the bank
		
		self.playerInterfaces[playerId].TryRaiseMoney(moneyNeeded, self)

	def MortgageSpace(self, spaceId):
		assert NumHousesOnSpace(spaceId) == 0
		space = self.board[spaceId]
		ownerId = self.spaceOwners[spaceId]
		self.playerMoney[ownerId] += space['mortgage']
		self.spaceMortgaged[spaceId] = True

	def PlayerGoesBankrupt(self, playerOwingId, playerOwedId):

		self.globalInterface.Log("Player {} goes backrupt and pays everything to {}".format(playerOwingId, playerOwedId))
		self.playerBankrupt[playerOwingId] = True

		# Transfer all cash
		if playerOwedId != 'bank':
			self.playerMoney[playerOwedId] += self.playerMoney[playerOwingId]
		self.playerMoney[playerOwingId] = 0

		# Transfer get out of jail cards
		# https://boardgames.stackexchange.com/questions/22829/do-get-out-of-jail-free-cards-have-value
		if playerOwedId != 'bank':
			self.playerGetOutOfJailCards[playerOwedId].extend(self.playerGetOutOfJailCards[playerOwingId])
		self.playerGetOutOfJailCards[playerOwingId] = []

		# Remove all houses and hotels for cash
		for spaceId, space in enumerate(self.board):
			owner = self.spaceOwners[spaceId]
			if owner == playerOwingId:
				propGroupId = self.propertyInGroup[spaceId]
				self.SetNumBuildingsInGroup(propGroupId, 0)

		# Transfer all property to owed player
		mortgaged = []
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
		
		if playerOwedId != 'bank':

			# The receiving player gets to choose if they unmortgage properties
			choices = []
			for spaceId in mortgaged:
				space = self.board[spaceId]
				interest = int(round(space['mortgage'] * 0.1))
				mortgagePlusInterest = space['mortgage'] + interest
				choices.append([spaceId, True, interest, mortgagePlusInterest])

			choices = self.playerInterfaces[playerOwedId].UnmortgageChoices(choices, self)
			
			totalBill = 0
			for spaceId, propMortgaged, interest, mortgagePlusInterest in choices:
				self.spaceMortgaged[spaceId] = propMortgaged
				if propMortgaged:
					totalBill += interest
				else:
					totalBill += mortgagePlusInterest

			# Paying for interest on properties following a bankrupcy could trigger another bankrupcy
			# https://boardgames.stackexchange.com/questions/50930/monopoly-can-you-go-bankrupt-by-having-someone-else-go-bankrupt-on-you/
			self.EnsurePlayment(playerOwedId, totalBill, 'bank')

	def FreeTrading():

		while True:

			playerId = self.globalInterface.GetPlayerIdToTrade()
			if playerId == -1: break

			self.playerInterfaces[playerId].DoTrading(self)

	def GetCompleteHouseGroups(self, ownedBy=None):
		
		completeGroups = []
		for groupId, group in self.propertyGroup:
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
		countHouses = 0
		for si in self.boardHouses:
			if si == spaceId:
				countHouses += 1

		countHotels = 0
		for si in self.boardHotels:
			if si == spaceId:
				countHotels += 1
				
		assert countHouses == 0 or countHotels == 0
		assert countHouses >= 0 and countHouses <= 4
		assert countHotels >= 0 and countHotels <= 1

		if countHotels: return 5
		return countHouses

	def GetFreeBuildings(self):
		freeHouses = []
		for i, si in enumerate(self.boardHouses):
			if si is None:
				freeHouses.append(i)

		freeHotels = []
		for i, si in enumerate(self.boardHotels):
			if si is None:
				freeHotels.append(i)

		return freeHouses, freeHotels

	# Buying and selling houses and hotels
	def SetNumBuildingsInGroup(self, groupId, numBuildings, planOnly = False, applyPayment = True):
		
		assert self.IsGroupAllUnmortgaged(groupId)
		assert self.GetGroupOwner(groupId) is not None
		group = self.propertyGroup[groupId]
		assert numBuildings >= 0

		groupOwner = self.GetGroupOwner(groupId)
		availableMoney = self.playerMoney[groupOwner]

		freeHouses, freeHotels = self.GetFreeBuildings()
		
		existingHouses, groupHouses = self.NumHousesInGroup(groupId)
		assert existingHouses == len(self.boardGroupBuildOrder[groupId])

		groupHouses.sort(key = lambda x: x[1])	
		impossible = False
		reasons = []

		#TODO put houses on expensive properties first

		if numBuildings == existingHouses:
			return False, None, reasons #No change

		elif numBuildings > existingHouses:
			# Increase wanted

			# Plan addition checking limits at each stage
			cursor = 0
			planAddHouseId = []
			planAddHotelId = []
			planAddSpaceId = []
			planAddCost = 0

			for i in range(numBuildings - existingHouses):
				# Plan adding a single building

				space = self.board[groupHouses[cursor][0]]

				if groupHouses[cursor][1] >= 5:
					reasons.append("Too many buildings")
					impossible = True
					break

				singleBuildingCost = space['building_costs']
				newCost = planAddCost + singleBuildingCost
				if applyPayment and newCost > availableMoney:
					reasons.append("Cost is too high")
					impossible = True
					break

				if groupHouses[cursor][1] <= 3:
					if len(freeHouses) == 0:
						reasons.append("Ran out of house markers")
						impossible = True
						break
					planAddHouseId.append(freeHouses.pop())
					planAddHotelId.append(None)
				else:
					if len(freeHotels) == 0:
						reasons.append("Ran out of hotel markers")
						impossible = True
						break
					planAddHouseId.append(None)
					planAddHotelId.append(freeHotels.pop())

				planAddCost = newCost
				planAddSpaceId.append(groupHouses[cursor][0])
				groupHouses[cursor][1] += 1

				cursor += 1
				if cursor >= len(groupHouses):
					cursor = 0
			
			if impossible or planOnly:
				return impossible, len(planAddSpaceId), reasons

			# Execute plan to board
			for houseId, hotelId, spaceId in zip(planAddHouseId, planAddHotelId, planAddSpaceId):
				if houseId is not None:
					self.boardHouses[houseId] = spaceId					
				else:
					# Remove 4 houses and replace with hotel
					for hi, si in enumerate(self.boardHouses):
						if si == spaceId: self.boardHouses[hi] = None
					self.boardHotels[hotelId] = spaceId
				self.boardGroupBuildOrder[groupId].append(spaceId)

			if applyPayment:
				bankrupted = self.EnsurePlayment(groupOwner, planAddCost, 'bank')
				assert not bankrupted # Checks above should block bankrupcy
			
			existingHouses2, groupHouses2 = self.NumHousesInGroup(groupId)

			assert existingHouses2 == numBuildings
			return impossible, None, reasons

		else:

			# Plan removal of buildings
			planHouseCount = {}
			for spaceId, buildCount in groupHouses:
				planHouseCount[spaceId] = buildCount
			planRemoveCount = 0
			planningFreeHouses = freeHouses[:]
			for i in range(existingHouses-numBuildings):

				# Plan removal of a single building
				spaceId = self.boardGroupBuildOrder[groupId][-i-1]
				space = self.board[spaceId]

				if planHouseCount[spaceId] >= 5:

					# Add houses
					# What if we run out?
					# https://boardgames.stackexchange.com/questions/925/what-happens-when-you-need-to-tear-down-a-hotel-but-no-houses-are-in-the-bank-in
					# Approach used is to forhid sale of hotel
					if len(planningFreeHouses) < 4:
						# Forbid sale if we ran out
						reasons.append(["Insufficient houses available to replace hotel"])
						return True, planRemoveCount, reasons
					else:
						for j in range(4):
							planningFreeHouses.pop()

				planHouseCount[spaceId] -= 1
				planRemoveCount += 1

			# Execute the removal plan
			houseCount = {}
			for spaceId, buildCount in groupHouses:
				houseCount[spaceId] = buildCount
			for i in range(planRemoveCount):

				spaceId = self.boardGroupBuildOrder[groupId].pop(-1)
				space = self.board[spaceId]

				if houseCount[spaceId] >= 5:
					# Remove hotel
					ind = self.boardHotels.index(spaceId)
					self.boardHotels[ind] = None
			
					# Add 4 houses
					for j in range(4):
						self.boardHouses[freeHouses.pop()] = spaceId

				else:
					ind = self.boardHouses.index(spaceId)
					self.boardHouses[ind] = None

				if applyPayment:
					self.playerMoney[groupOwner] += space['building_costs'] // 2
				houseCount[spaceId] -= 1

		return impossible, None, reasons

def TrueOrFalseQuestion(questionText):
	playerIn = None
	while True:
		playerIn = input(questionText)
		if len(playerIn) == 0:
			continue
		try:
			if playerIn[0].lower() in ["y", "1"]:
				playerIn = True
			elif playerIn[0].lower() in ["n", "0"]:
				playerIn = False
			else:
				playerIn = None

		except ValueError:
			continue
		if playerIn is not None:
			break
	return playerIn

def IntegerQuestion(questionText):
	while True:

		playerIn = input(questionText)
		try:
			playerIn = int(playerIn)
		except ValueError:
			continue
		break
	return playerIn

class HumanInterface(object):
	def __init__(self, playerNum):
		self.playerNum = playerNum

	def OptionToBuy(self, spaceId, gameState):
		space = gameState.board[spaceId]
		questionText = "Player {}, would you like to buy {} for {}?".format(self.playerNum, space['name'], space['price'])
		return TrueOrFalseQuestion(questionText)

	def GetActionBid(self, spaceId, gameState):
		space = gameState.board[spaceId]
		return IntegerQuestion("Player {}, what is your maximum bid for {} (balance {})?".format(self.playerNum, space['name'], gameState.playerMoney[self.playerNum]))

	def UseGetOutOfJailCard(self, gameState):
		questionText = "Player {}, would you like to use a get out of jail card?".format(self.playerNum)
		return TrueOrFalseQuestion(questionText)

	def PayJailFine(self, gameState):
		questionText = "Player {}, would you like to play the fine of {} to get out of jail?".format(self.playerNum, gameState.jailFine)
		return TrueOrFalseQuestion(questionText)

	def TryRaiseMoney(self, moneyNeeded, gameState):
		
		unmortgaged = []
		for spaceId, space in enumerate(gameState.board):
			if self.playerNum == gameState.spaceOwners[spaceId] \
				and not gameState.spaceMortgaged[spaceId]:

				unmortgaged.append(spaceId)

		while len(unmortgaged) > 0:
			
			print ("Player {}, choose property to mortgage:".format(self.playerNum))
			for choiceId, spaceId in enumerate(unmortgaged):
				space = gameState.board[spaceId]
				print (choiceId, space)
			ind = IntegerQuestion("Index?")
			spaceId = unmortgaged.pop(ind)
			gameState.MortgageSpace(spaceId)

			if gameState.playerMoney[self.playerNum] >= moneyNeeded:
				break # Stop now we have enough cash

	def UnmortgageChoices(self, choices, gameState):
		
		choices = choices[:] #We are going to modify this
		while True:
			print ("Player {}, choose which properties to unmortgage:".format(self.playerNum))
			totalBill = 0
			for choiceId, (spaceId, mortgaged, interest, mortgagePlusInterest) in enumerate(choices):
				space = gameState.board[spaceId]
				print (choiceId, space['name'], interest, mortgagePlusInterest, "mortgaged=", mortgaged)			
				if mortgaged: 
					totalBill += interest
				else:
					totalBill += mortgagePlusInterest
			print ("Total bill", totalBill)
			if totalBill > gameState.playerMoney[self.playerNum]:
				print ("Warning: this is more than your current balance")
	
			ind = IntegerQuestion("Index to toggle? (-1 to quit)")
			if ind == -1:
				break
			choices[ind][1] = bool(1-choices[ind][1])

		return choices

	def DoTrading(self, gameState):
		while True:
			print ("1. Buy/sell houses and hotels")
			print ("2. Mortgage/unmortgage houses")
			print ("3. Propose a trade with other players")
			print ("-1. Done")

			ch = IntegerQuestion("Choice? (-1 to quit)")

			if ch == -1: break
			if ch == 1: self.DoTradingBuySellHouses(gameState)

	def DoTradingBuySellHouses(self, gameState):
		completeGroups = gameState.GetCompleteHouseGroups(self.playerId)

		while True:
			print ("Choose housing group:")
			for group in completeGroups:
				print (groupId, end="")
				if not gameState.IsGroupAllUnmortgaged(groupId):
					print (" Mortgaged")
					continue

				for spaceId in propertyGroup[groupId]:
					print (" {}".format(gameState.NumHousesOnSpace()), end="")
	
			print ("-1. Done")

			ch = IntegerQuestion("Group to change? (-1 to quit)")
			if self.playerId == gameState.GetGroupOwner(ch) and gameState.IsGroupAllUnmortgaged(groupId):
				self.DoTradingBuySellHousesOnGroup(ch, gameState)
				
			if ch == -1: break

	def DoTradingBuySellHousesOnGroup(self, groupId, gameState):
		
		while True:

			print ("Group", groupId)
			group = self.propertyGroup[groupId]
			
			freeHouses, freeHotels = gameState.GetFreeBuildings()
			countHouses, countHotels = len(freeHouses), len(freeHotels)

			for spaceId in group:
				space = self.board[spaceId]
				print (spaceId, space['name'], self.NumHousesOnSpace(spaceId))

			print ("{} houses and {} hotels free".format(countHouses, countHotels))

			ch = IntegerQuestion("Set number of houses? (-1 to quit)")
			
			if ch == -1: break
			gameState.SetNumBuildingsInGroup(groupId, numBuildiungs)
			

class RandomInterface(object):
	def __init__(self, playerNum):
		self.playerNum = playerNum

	def OptionToBuy(self, spaceId, gameState):
		return random.randint(0, 1)

	def GetActionBid(self, spaceId, gameState):
		space = gameState.board[spaceId]
		return random.randint(0, space['price'])

	def UseGetOutOfJailCard(self, gameState):
		return random.randint(0, 1)

	def PayJailFine(self, gameState):
		return random.randint(0, 1)

	def TryRaiseMoney(self, moneyNeeded, gameState):
		
		unmortgaged = []
		for spaceId, space in enumerate(gameState.board):
			if self.playerNum == gameState.spaceOwners[spaceId] \
				and not gameState.spaceMortgaged[spaceId]:

				unmortgaged.append(spaceId)

		while len(unmortgaged) > 0:
			
			ind = random.randint(0, len(unmortgaged)-1)
			spaceId = unmortgaged.pop(ind)
			gameState.MortgageSpace(spaceId)

			if gameState.playerMoney[self.playerNum] >= moneyNeeded:
				break # Stop now we have enough cash

	def UnmortgageChoices(self, choices, gameState):
		
		choices = choices[:] #We are going to modify this

		for choiceId, (spaceId, mortgaged, interest, mortgagePlusInterest) in enumerate(choices):
			space = gameState.board[spaceId]

			choices[choiceId][1] = random.randint(0,1)

		return choices

	def DoTrading(self, gameState):
		return

class GlobalInterface(object):
	def Log(self, event):
		print (event)

	def GetPlayerIdToTrade(self):
		return IntegerQuestion("Player ID wanting to trade (-1 to skip)?")

if __name__=="__main__":

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

		turnCount += 1

