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
		
		#TODO Add option to sell buildings

		unmortgaged = []
		for spaceId, space in enumerate(gameState.board):

			if self.playerNum == gameState.spaceOwners[spaceId] \
				and not gameState.spaceMortgaged[spaceId] \
				and gameState.NumHousesOnSpace(spaceId) == 0: # Property must be unimproved

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
	
			# TODO add trading interface

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

class TestInterface(object):
	def __init__(self, playerNum):
		self.playerNum = playerNum
		self.Reset()

	def Reset(self):
		self.optionToBuy = None
		self.getAuctionBid = None

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
		pass

	def TryRaiseMoney(self, moneyNeeded, gameState):
		pass

	def UnmortgageChoices(self, choices, gameState):
		pass

	def DoTrading(self, gameState):
		return

