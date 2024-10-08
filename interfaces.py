import random

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
		
		while True:
			print ("1. Buy/sell houses and hotels")
			print ("2. Mortgage/unmortgage houses")
			print ("-1. Done")

			ch = IntegerQuestion("Choice? (-1 to quit)")

			if ch == -1: break
			if ch == 1: self.DoTradingBuySellHouses(gameState)
			if ch == 2: self.MortgageUnmortgageMenu(gameState)
	
	def MortgageUnmortgageMenu(self, gameState):

		while True:

			selectable = []
			for spaceId, space in enumerate(gameState.board):

				if self.playerNum == gameState.spaceOwners[spaceId] \
					and not gameState.spaceMortgaged[spaceId] \
					and gameState.NumHousesOnSpace(spaceId) == 0: # Property must be unimproved

					selectable.append(spaceId)

				if self.playerNum == gameState.spaceOwners[spaceId] \
					and gameState.spaceMortgaged[spaceId]:

					selectable.append(spaceId)
			
			if len(selectable) == 0: break

			print ("Player {}, choose property to toggle mortgage:".format(self.playerNum))
			for spaceId in selectable:
				space = gameState.board[spaceId]
				print (spaceId, space['name'], gameState.spaceMortgaged[spaceId])
			ind = IntegerQuestion("Index (-1 to abort)?")
			if ind == -1: break
			if ind not in selectable: continue

			if gameState.spaceMortgaged[spaceId]:
				gameState.UnmortgageSpace(spaceId)	
			else:
				gameState.MortgageSpace(spaceId)

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
			print ("2. Mortgage/unmortgage properties")
			print ("3. Propose a trade with other players")
			print ("-1. Done")

			ch = IntegerQuestion("Choice? (-1 to quit)")

			if ch == -1: break
			if ch == 1: self.DoTradingBuySellHouses(gameState)
			if ch == 2: self.MortgageUnmortgageMenu(gameState)
			if ch == 3: self.TradeMenu(gameState)

		return True

	def TradeMenu(self, gameState):

		
		while True:
			print ("Simple (one space) trading supported. TODO add complex trades.")
			print ("Properties:")
			selectable = []
			for spaceId, space in enumerate(gameState.board):
				ownerId = gameState.spaceOwners[spaceId]
				if ownerId is None: continue
				print (spaceId, space['name'], ownerId)
				selectable.append(spaceId)

			ch = IntegerQuestion("Select property? (-1 to quit)")

			if ch in selectable:

				ownerId = gameState.spaceOwners[ch]
				space = gameState.board[ch]
				accepted = False

				if ownerId == self.playerNum:

					p2 = IntegerQuestion("Trade with player? (-1 to about)")
					if p2 == -1:
						print ("Trade Aborted")
						continue
					if p2 < 0 or p2 >= gameState.numPlayers:
						print ("Invalid player Id")
						continue
					if p2 == self.playerNum:
						print ("Can't trade with self")
						continue
					if gameState.playerBankrupt[p2]:
						print ("Player is backrupt")
						continue
					oppInterface = gameState.playerInterfaces[p2]

					offer = IntegerQuestion("Offer to sell {} for? (-1 to abort)".format(space['name']))
					if offer < 0:
						# Tim note: I used to play an AI on C64 what didn't check for this
						# and always accepted a negative trade!
						print ("Cannot be a negative offer")
						continue
					accepted = oppInterface.OfferTrade(self.playerNum, ch, True, offer)
					
					if accepted:
						if gameState.playerMoney[p2] >= offer:
							gameState.ProcessTrade(self.playerNum, p2, ch, offer)
						else:
							print ("Player cannot afford sale")
					else:
						print ("Player rejected proposed trade")

				else:
					oppInterface = gameState.playerInterfaces[ownerId]

					offer = IntegerQuestion("Offer to buy {} from player {} for? (-1 to abort)".format(space['name'], ownerId))
					if offer < 0:
						print ("Cannot be a negative offer")
						continue

					accepted = oppInterface.OfferTrade(self.playerNum, ch, False, offer)

					if accepted:
						if gameState.playerMoney[self.playerNum] >= offer:
							gameState.ProcessTrade(ownerId, self.playerNum, ch, offer)
						else:
							print ("Player cannot afford sale")							

					else:
						print ("Player rejected proposed trade")

			if ch == -1: break

		return True


	def DoTradingBuySellHouses(self, gameState):
		completeGroups = gameState.GetCompleteHouseGroups(self.playerNum)

		while True:
			print ("Choose housing group:")
			for groupId in completeGroups:
				print ("Group:", groupId, end="")
				if not gameState.IsGroupAllUnmortgaged(groupId):
					print (" Mortgaged", end="")
					continue

				print (" Num buildings: ", end="")
				for spaceId in gameState.propertyGroup[groupId]:
					print (" {}".format(gameState.NumHousesOnSpace(spaceId)), end="")
				print ("")	

			print ("-1. Done")

			ch = IntegerQuestion("Group to change? (-1 to quit)")
			if self.playerNum == gameState.GetGroupOwner(ch) and gameState.IsGroupAllUnmortgaged(groupId):
				self.DoTradingBuySellHousesOnGroup(ch, gameState)
				
			if ch == -1: break

	def DoTradingBuySellHousesOnGroup(self, groupId, gameState):
		
		while True:

			print ("Group", groupId)
			group = gameState.propertyGroup[groupId]
			
			freeHouses, freeHotels = gameState.GetFreeBuildings()
			countHouses, countHotels = len(freeHouses), len(freeHotels)

			for spaceId in group:
				space = gameState.board[spaceId]
				print (spaceId, space['name'], gameState.NumHousesOnSpace(spaceId))

			print ("{} houses and {} hotels free".format(countHouses, countHotels))

			numBuildings = IntegerQuestion("Set number of houses? (-1 to quit)")
			
			if numBuildings == -1: break
			gameState.SetNumBuildingsInGroup(groupId, numBuildings)

	def ShowTradePlayerSelect(self):
		return True

	def OfferTrade(self, fromPlayerId, spaceId, isSellOffer, moneyOffer):

		verb = "sell"
		if isSellOffer: verb = "buy"
		space = gameState.board[spaceId]
		
		questionText = "Player {}, would you like to {} {} for {}?".format(self.playerNum, space['name'], moneyOffer)
		return TrueOrFalseQuestion(questionText)

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

		# Find suitable properties
		unmortgaged = []
		for spaceId, space in enumerate(gameState.board):
			if self.playerNum == gameState.spaceOwners[spaceId] \
				and not gameState.spaceMortgaged[spaceId]:

				if spaceId in gameState.propertyInGroup \
					and gameState.NumHousesInGroup(gameState.propertyInGroup[spaceId])[0] != 0: continue

				unmortgaged.append(spaceId)

		# Find suitable buildings
		buildingsInGroup = {}
		for groupId in gameState.GetCompleteHouseGroups(self.playerNum):

			existingHouses, groupHouses = gameState.NumHousesInGroup(groupId)
			buildingsInGroup[groupId] = existingHouses
		totalBuildings = sum(buildingsInGroup.values())

		# Sell buildings and mortgage properties until we get enough money
		while len(unmortgaged) > 0 or totalBuildings > 0:

			if totalBuildings > 0:

				groupId = random.choice(list(buildingsInGroup.keys()))
				if buildingsInGroup[groupId] > 0:
					# Sell some buildings
					gameState.SetNumBuildingsInGroup(groupId, random.randint(0, buildingsInGroup[groupId]-1))
					
					newNumBuildings = gameState.NumHousesInGroup(groupId)[0]
					buildingsInGroup[groupId] = newNumBuildings
					if newNumBuildings == 0:
						for spaceId in gameState.propertyGroup[groupId]:
							if spaceId not in unmortgaged:
								unmortgaged.append(spaceId)
					totalBuildings = sum(buildingsInGroup.values())

			if len(unmortgaged) > 0:
				# Mortgage some properties
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
		cho = bool(random.randint(0, 100))
		if cho == 0:
			# Trade random building
			sellable, buyable = [], []
			for spaceId, space in enumerate(gameState.board):
				ownerId = gameState.spaceOwners[spaceId]
				if ownerId is None: continue
				if spaceId in gameState.propertyInGroup and gameState.NumHousesInGroup(gameState.propertyInGroup[spaceId]) != 0: continue
				if ownerId == self.playerNum:
					sellable.append(spaceId)
				else:
					buyable.append(spaceId)

			if bool(random.randint(0, 1)):

				# Oppenents
				opponents = []
				for oi, ban in enumerate(gameState.playerBankrupt):
					if oi == self.playerNum: continue
					if not ban: opponents.append(oi)			
				oppenentId, oppInterface = None, None
				if len(opponents) > 0:
					oppenentId = random.choice(opponents)
					oppInterface = gameState.playerInterfaces[oppenentId]

				if len(sellable) > 0 and len(opponents) > 0: #Sell
					spaceId = random.choice(sellable)
					space = gameState.board[spaceId]

					money = int(space['price'] * random.random() * 1.5)

					accepted = oppInterface.OfferTrade(self.playerNum, spaceId, True, money)

					if accepted and gameState.playerMoney[oppenentId] >= money:
						gameState.ProcessTrade(self.playerNum, oppenentId, spaceId, money)
			else:
				if len(buyable) > 0: #Buy
					spaceId = random.choice(buyable)
					space = gameState.board[spaceId]
					ownerId = gameState.spaceOwners[spaceId]
					oppInterface = gameState.playerInterfaces[ownerId]

					money = int(space['price'] * random.random() * 1.5)

					accepted = oppInterface.OfferTrade(self.playerNum, spaceId, False, money)

					if accepted and gameState.playerMoney[self.playerNum] >= money:
						gameState.ProcessTrade(ownerId, self.playerNum, spaceId, money)

		elif cho == 1:

			# Random buy/sell houses
			groupIds = gameState.GetCompleteHouseGroups(self.playerNum)

			allUnmortgaged = []
			for gi in groupIds:
				if gameState.IsGroupAllUnmortgaged(gi):
					allUnmortgaged.append(gi)

			if len(allUnmortgaged) > 0:
				groupId = random.choice(allUnmortgaged)

				group = gameState.propertyGroup[groupId]
				numBuildings = random.randint(0, 5 * len(group))

				impossible, numAllowed, reasons, planCost = gameState.SetNumBuildingsInGroup(groupId, numBuildings, planOnly=True)
		
				if not impossible:
					gameState.SetNumBuildingsInGroup(groupId, numBuildings)

		elif cho == 2:

			# Random mortgage/unmortgage
			ownedProperties = []
			for spaceId, owner in enumerate(gameState.spaceOwners):
				if owner != self.playerNum: continue
				if gameState.NumHousesInGroup(gameState.propertyInGroup[spaceId]) != 0: continue
				space = gameState.board[spaceId]
				if gameState.spaceMortgaged[spaceId]:
					if gameState.playerMoney[self.playerNum] > int(1.1 * space['mortgage']):
						gameState.UnmortgageSpace(spaceId)
				else:
					gameState.MortgageSpace(spaceId)

		return True

	def ShowTradePlayerSelect(self):
		return False

	def OfferTrade(self, fromPlayerId, spaceId, isSellOffer, moneyOffer):
		return bool(random.randint(0, 1))


class GlobalInterface(object):
	def Log(self, event):
		print (event)

	def GetPlayerIdToTrade(self):
		return IntegerQuestion("Player ID wanting to trade (-1 to skip)?")

class TestInterface(object):
	def __init__(self, playerNum):
		self.playerNum = playerNum
		self.Reset()

	def Reset(self):
		self.optionToBuy = None
		self.getAuctionBid = None
		self.payGetOutOfJail = False

	def OptionToBuy(self, spaceId, gameState):
		if self.optionToBuy is None:
			raise RuntimeError()
		return self.optionToBuy

	def GetActionBid(self, spaceId, gameState):
		if self.getAuctionBid is None:
			raise RuntimeError()
		return self.getAuctionBid

	def UseGetOutOfJailCard(self, gameState):
		pass

	def PayJailFine(self, gameState):
		return self.payGetOutOfJail

	def TryRaiseMoney(self, moneyNeeded, gameState):
		pass

	def UnmortgageChoices(self, choices, gameState):
		pass

	def DoTrading(self, gameState):
		return True

	def ShowTradePlayerSelect(self):
		return False

	def OfferTrade(self, fromPlayerId, spaceId, isSellOffer, moneyOffer):
		return False

