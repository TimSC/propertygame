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

	def GetAuctionBid(self, spaceId, highestBid, highestBidder, gameState):
		space = gameState.board[spaceId]
		print ("Auction for {}: highest bid {} by player {}".format(space['name'], highestBid, highestBidder))
		bid = IntegerQuestion("Player {}, your bid (balance {})? (0 to pass)".format(self.playerNum, gameState.playerMoney[self.playerNum]))
		if bid <= highestBid: return None
		return bid

	def UseGetOutOfJailCard(self, gameState):
		questionText = "Player {}, would you like to use a get out of jail card?".format(self.playerNum)
		return TrueOrFalseQuestion(questionText)

	def PayJailFine(self, gameState):
		questionText = "Player {}, would you like to play the fine of {} to get out of jail?".format(self.playerNum, gameState.jailFine)
		return TrueOrFalseQuestion(questionText)

	def TryRaiseMoney(self, moneyNeeded, gameState):
		
		while True:
			print ("Player {} needs {} (has {})".format(self.playerNum, moneyNeeded, gameState.playerMoney[self.playerNum]))
			print ("1. Buy/sell houses and hotels")
			print ("2. Mortgage/unmortgage houses")
			print ("3. Propose a trade with other players")
			print ("-1. Done")

			ch = IntegerQuestion("Choice? (-1 to quit)")

			if ch == -1: break
			if ch == 1: self.DoTradingBuySellHouses(gameState)
			if ch == 2: self.MortgageUnmortgageMenu(gameState)
			if ch == 3: self.TradeMenu(gameState)
	
	def MortgageUnmortgageMenu(self, gameState):

		while True:

			selectable = []
			for spaceId, space in enumerate(gameState.board):

				if self.playerNum == gameState.spaceOwners[spaceId] \
					and not gameState.spaceMortgaged[spaceId] \
					and (spaceId not in gameState.propertyInGroup \
						or gameState.NumHousesInGroup(gameState.propertyInGroup[spaceId])[0] == 0): # Group must be unimproved

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

			if gameState.spaceMortgaged[ind]:
				if gameState.playerMoney[self.playerNum] < gameState.UnmortgageCost(ind):
					print ("Cannot afford to unmortgage")
					continue
				gameState.UnmortgageSpace(ind)
			else:
				gameState.MortgageSpace(ind)

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

		p2 = IntegerQuestion("Trade with player? (-1 to abort)")
		if p2 == -1: return True
		if p2 < 0 or p2 >= gameState.numPlayers or p2 == self.playerNum or gameState.playerBankrupt[p2]:
			print ("Invalid player Id")
			return True

		offer = gameState.NewTrade(self.playerNum, p2)
		while True:
			print (gameState.DescribeTrade(offer))
			print ("1. Add/remove a property you give")
			print ("2. Add/remove a property you get")
			print ("3. Set cash you give")
			print ("4. Set cash you get")
			print ("5. Set get out of jail free cards you give")
			print ("6. Set get out of jail free cards you get")
			print ("7. Propose trade")
			print ("-1. Abort")

			ch = IntegerQuestion("Choice? (-1 to abort)")
			if ch == -1: break

			if ch in [1, 2]:
				side = ch - 1
				tradeable = gameState.TradeableSpaces(offer.playerIds[side])
				for spaceId in tradeable:
					space = gameState.board[spaceId]
					print (spaceId, space['name'], "mortgaged=", gameState.spaceMortgaged[spaceId], "in trade=", spaceId in offer.spaces[side])
				spaceId = IntegerQuestion("Property to add/remove? (-1 to go back)")
				if spaceId not in tradeable: continue
				if spaceId in offer.spaces[side]:
					offer.spaces[side].remove(spaceId)
				else:
					offer.spaces[side].append(spaceId)

			if ch in [3, 4]:
				# Tim note: I used to play an AI on C64 what didn't check for this
				# and always accepted a negative trade!
				amount = IntegerQuestion("Amount?")
				if amount < 0:
					print ("Cannot be negative")
					continue
				offer.money[ch - 3] = amount

			if ch in [5, 6]:
				side = ch - 5
				held = len(gameState.playerGetOutOfJailCards[offer.playerIds[side]])
				count = IntegerQuestion("Number of cards (0 to {})?".format(held))
				if count < 0 or count > held: continue
				offer.jailCards[side] = count

			if ch == 7:
				reasons = gameState.TradeProblems(offer)
				if len(reasons) > 0:
					for reason in reasons: print (reason)
					continue
				if gameState.ProposeTrade(offer):
					print ("Trade accepted")
				else:
					print ("Player rejected proposed trade")
				break

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
			if ch in completeGroups and gameState.IsGroupAllUnmortgaged(ch):
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
			if numBuildings < 0: continue
			impossible, numAllowed, reasons, planCost = gameState.BuildBuildings(self.playerNum, groupId, numBuildings)
			if impossible: print ("Not possible:", reasons)

	def ShowTradePlayerSelect(self):
		return True

	def GetBuildingDemand(self, buildingType, available, gameState):
		return IntegerQuestion("Player {}, there is a {} shortage ({} left). How many would you like to buy? (0 for none)".format(self.playerNum, buildingType, available))

	def GetBuildingBid(self, buildingType, groupIds, highestBid, highestBidder, gameState):
		print ("Auction for a {}: highest bid {} by player {}".format(buildingType, highestBid, highestBidder))
		print ("Player {}, bid for a {} (balance {}). Groups you can build on:".format(self.playerNum, buildingType, gameState.playerMoney[self.playerNum]))
		for groupId in groupIds:
			space = gameState.board[gameState.propertyGroup[groupId][0]]
			print ("Group:", groupId, "minimum bid", space['building_costs'])
		groupId = IntegerQuestion("Group to build on? (-1 to pass)")
		if groupId == -1: return None
		return groupId, IntegerQuestion("Bid?")

	def ConsiderTrade(self, offer, gameState):
		print (gameState.DescribeTrade(offer))
		return TrueOrFalseQuestion("Player {}, do you accept this trade?".format(self.playerNum))

class RandomInterface(object):
	def __init__(self, playerNum):
		self.playerNum = playerNum

	def OptionToBuy(self, spaceId, gameState):
		return random.randint(0, 1)

	def GetAuctionBid(self, spaceId, highestBid, highestBidder, gameState):
		# Raise by a random amount, up to the list price, or pass
		space = gameState.board[spaceId]
		if highestBid >= space['price'] or not random.randint(0, 2): return None
		return random.randint(highestBid + 1, min(space['price'], highestBid + 50))

	def UseGetOutOfJailCard(self, gameState):
		return random.randint(0, 1)

	def PayJailFine(self, gameState):
		return random.randint(0, 1)

	def TryRaiseMoney(self, moneyNeeded, gameState):

		if gameState.PlayerMaxMoneyThatCanBeRaised(self.playerNum) < moneyNeeded:
			# The bank alone cannot cover it, so try selling property to other players
			for attempt in range(3):
				self.TrySellForCash(gameState)
				if gameState.PlayerMaxMoneyThatCanBeRaised(self.playerNum) >= moneyNeeded: break
			if gameState.PlayerMaxMoneyThatCanBeRaised(self.playerNum) < moneyNeeded:
				return # Hopeless, so don't bother mortgaging

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
		cho = random.randint(0, 2)
		if cho == 0:
			# Propose a random trade
			opponents = [oi for oi in gameState.GetPlayersUnbankrupt() if oi != self.playerNum]
			if len(opponents) > 0:
				offer = gameState.NewTrade(self.playerNum, random.choice(opponents))

				worth = [0, 0]
				for side, playerId in enumerate(offer.playerIds):
					tradeable = gameState.TradeableSpaces(playerId)
					random.shuffle(tradeable)
					offer.spaces[side] = tradeable[:random.randint(0, min(2, len(tradeable)))]
					worth[side] = sum([gameState.board[spaceId]['price'] for spaceId in offer.spaces[side]])
					if len(gameState.playerGetOutOfJailCards[playerId]) > 0 and not random.randint(0, 3):
						offer.jailCards[side] = 1
						worth[side] += 50

				# Whoever gets the better deal pays some cash
				amount = int(abs(worth[1] - worth[0]) * random.random() * 1.5)
				if worth[1] > worth[0]:
					offer.money[0] = amount
				else:
					offer.money[1] = amount

				if len(gameState.TradeProblems(offer)) == 0:
					gameState.ProposeTrade(offer)

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

				gameState.BuildBuildings(self.playerNum, groupId, numBuildings)

		elif cho == 2:

			# Random mortgage/unmortgage
			ownedProperties = []
			for spaceId, owner in enumerate(gameState.spaceOwners):
				if owner != self.playerNum: continue
				if spaceId in gameState.propertyInGroup and gameState.NumHousesInGroup(gameState.propertyInGroup[spaceId])[0] != 0: continue
				space = gameState.board[spaceId]
				if gameState.spaceMortgaged[spaceId]:
					if gameState.playerMoney[self.playerNum] >= gameState.UnmortgageCost(spaceId):
						gameState.UnmortgageSpace(spaceId)
				else:
					gameState.MortgageSpace(spaceId)

		return True

	def ShowTradePlayerSelect(self):
		return False

	def ConsiderTrade(self, offer, gameState):
		return bool(random.randint(0, 1))

	def TrySellForCash(self, gameState):
		# Offer a random property to a random player for cash
		tradeable = gameState.TradeableSpaces(self.playerNum)
		opponents = [oi for oi in gameState.GetPlayersUnbankrupt() if oi != self.playerNum]
		if len(tradeable) == 0 or len(opponents) == 0: return
		offer = gameState.NewTrade(self.playerNum, random.choice(opponents))
		spaceId = random.choice(tradeable)
		offer.spaces[0] = [spaceId]
		offer.money[1] = int(gameState.board[spaceId]['price'] * random.random() * 1.5)
		if len(gameState.TradeProblems(offer)) == 0:
			gameState.ProposeTrade(offer)

	def GetBuildingDemand(self, buildingType, available, gameState):
		return random.randint(0, available)

	def GetBuildingBid(self, buildingType, groupIds, highestBid, highestBidder, gameState):
		# Raise by a random amount, up to twice the building cost, or pass
		groupId = random.choice(groupIds)
		cost = gameState.board[gameState.propertyGroup[groupId][0]]['building_costs']
		lowest = max(highestBid + 1, cost)
		highest = min(gameState.playerMoney[self.playerNum], 2 * cost)
		if lowest > highest or not random.randint(0, 3): return None
		return groupId, random.randint(lowest, min(highest, lowest + 20))


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
		self.buildingDemand = 0
		self.buildingBid = None
		self.acceptTrade = False
		self.useGetOutOfJailCard = False

	def OptionToBuy(self, spaceId, gameState):
		if self.optionToBuy is None:
			raise RuntimeError()
		return self.optionToBuy

	def GetAuctionBid(self, spaceId, highestBid, highestBidder, gameState):
		# Bids getAuctionBid if that beats the current bid, otherwise passes
		if self.getAuctionBid is None:
			raise RuntimeError()
		if self.getAuctionBid <= highestBid: return None
		return self.getAuctionBid

	def UseGetOutOfJailCard(self, gameState):
		return self.useGetOutOfJailCard

	def PayJailFine(self, gameState):
		return self.payGetOutOfJail

	def TryRaiseMoney(self, moneyNeeded, gameState):
		pass

	def UnmortgageChoices(self, choices, gameState):
		return choices

	def DoTrading(self, gameState):
		return True

	def ShowTradePlayerSelect(self):
		return False

	def ConsiderTrade(self, offer, gameState):
		return self.acceptTrade

	def GetBuildingDemand(self, buildingType, available, gameState):
		return self.buildingDemand

	def GetBuildingBid(self, buildingType, groupIds, highestBid, highestBidder, gameState):
		# buildingBid is (groupId, bid), made if it beats the current bid
		if self.buildingBid is None: return None
		if self.buildingBid[1] <= highestBid: return None
		return self.buildingBid

