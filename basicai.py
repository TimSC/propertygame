from interfaces import PlayerInterface

class BasicAIInterface(PlayerInterface):

	"""
	A simple AI that tries to complete colour sets and build on them. It keeps a cash
	reserve, bids up to what a property is worth to it, mortgages its least useful
	property first when short of money, and doesn't trade.
	"""

	def SetOf(self, spaceId, gameState):
		# The spaces that go together for rent: a colour group, the stations or the utilities
		space = gameState.board[spaceId]
		if space['type'] == 'property': return gameState.propertyGroup[space['property_group']]
		if space['type'] == 'station': return gameState.boardStations
		return gameState.boardUtilities

	def Worth(self, spaceId, gameState):
		# What a space is worth to this player, as a multiple of its price
		others = [s for s in self.SetOf(spaceId, gameState) if s != spaceId]
		mine = len([s for s in others if gameState.spaceOwners[s] == self.playerNum])
		opponents = set(gameState.spaceOwners[s] for s in others) - set([None, self.playerNum])
		if mine == len(others):
			return 1.6 # Completes the set
		if not opponents:
			return 1.1 + 0.2 * mine # The set can still be completed
		if len(opponents) == 1 and all(gameState.spaceOwners[s] in opponents for s in others):
			return 1.0 # Stops an opponent completing the set
		return 0.6

	def Reserve(self, gameState):
		# Cash to keep in hand for rent: more once opponents have built houses
		worst = 0
		for spaceId, owner in enumerate(gameState.spaceOwners):
			if owner in (None, self.playerNum) or gameState.spaceMortgaged[spaceId]: continue
			if gameState.board[spaceId]['type'] == 'property':
				worst = max(worst, gameState.CalcRent(self.playerNum, spaceId, 7))
		return min(600, 150 + worst // 2)

	def OptionToBuy(self, spaceId, gameState):
		worth = self.Worth(spaceId, gameState)
		if worth >= 1.6:
			return True # Worth mortgaging other property for (the game only asks if it can be raised)
		price = gameState.board[spaceId]['price']
		keep = self.Reserve(gameState) * (0.5 if worth >= 1.1 else (0.75 if worth >= 1.0 else 1.0))
		return gameState.playerMoney[self.playerNum] - price >= keep

	def GetAuctionBid(self, spaceId, highestBid, highestBidder, gameState):
		price = gameState.board[spaceId]['price']
		worth = self.Worth(spaceId, gameState)
		if worth >= 1.6:
			available = gameState.PlayerMaxMoneyThatCanBeRaised(self.playerNum) - 50
		else:
			available = gameState.playerMoney[self.playerNum] - self.Reserve(gameState) // 2
		limit = min(int(price * worth), available)
		if highestBid + 1 > limit:
			return None
		return min(limit, highestBid + max(1, price // 20))

	def StayInJail(self, gameState):
		# Early on, get out to buy property. Later, once opponents have built, jail is a safe place to wait.
		unowned = len([s for s, space in enumerate(gameState.board) if 'price' in space and gameState.spaceOwners[s] is None])
		return unowned < 6 and self.Reserve(gameState) > 250

	def UseGetOutOfJailCard(self, gameState):
		return not self.StayInJail(gameState)

	def PayJailFine(self, gameState):
		money = gameState.playerMoney[self.playerNum]
		return not self.StayInJail(gameState) and money - gameState.jailFine >= self.Reserve(gameState)

	def TryRaiseMoney(self, moneyNeeded, gameState):
		while gameState.playerMoney[self.playerNum] < moneyNeeded:
			if not self.RaiseSomeMoney(gameState):
				return

	def RaiseSomeMoney(self, gameState):
		# Mortgage or sell one thing, least useful first. Returns False if there is nothing left.
		me = self.playerNum
		complete = set(gameState.GetCompleteHouseGroups(me))
		unmortgaged = [s for s, owner in enumerate(gameState.spaceOwners) if owner == me and not gameState.spaceMortgaged[s]]
		mortgageable = [s for s in unmortgaged
			if s not in gameState.propertyInGroup or gameState.NumHousesInGroup(gameState.propertyInGroup[s])[0] == 0]

		# Property that isn't part of a complete set
		loose = [s for s in mortgageable if gameState.propertyInGroup.get(s) not in complete]
		if loose:
			gameState.MortgageSpace(min(loose, key = lambda s: (self.Worth(s, gameState), gameState.board[s]['mortgage'])))
			return True

		# Buildings, from the cheapest set first
		built = [g for g in complete if gameState.NumHousesInGroup(g)[0] > 0]
		if built:
			groupId = min(built, key = lambda g: gameState.board[gameState.propertyGroup[g][0]]['building_costs'])
			existing = gameState.NumHousesInGroup(groupId)[0]
			impossible = gameState.BuildBuildings(me, groupId, existing - 1)[0]
			if impossible:
				gameState.BuildBuildings(me, groupId, 0) # A hotel can't be broken down, so sell everything
			return True

		# Finally, property in complete sets
		if mortgageable:
			gameState.MortgageSpace(min(mortgageable, key = lambda s: gameState.board[s]['mortgage']))
			return True
		return False

	def UnmortgageChoices(self, choices, gameState):
		# Pay off the most useful mortgages now, if cash allows
		choices = [list(c) for c in choices]
		cash = gameState.playerMoney[self.playerNum] - sum(c[2] for c in choices)
		for choice in sorted(choices, key = lambda c: -self.Worth(c[0], gameState)):
			principal = choice[3] - choice[2]
			if cash - principal >= self.Reserve(gameState):
				choice[1] = False
				cash -= principal
		return choices

	def DoTrading(self, gameState):
		# Between turns: pay off mortgages, then build on complete sets
		me = self.playerNum
		reserve = self.Reserve(gameState)
		mortgaged = [s for s, owner in enumerate(gameState.spaceOwners) if owner == me and gameState.spaceMortgaged[s]]
		for spaceId in sorted(mortgaged, key = lambda s: -self.Worth(s, gameState)):
			if gameState.playerMoney[me] - gameState.UnmortgageCost(spaceId) >= reserve + 100:
				gameState.UnmortgageSpace(spaceId)

		for attempt in range(60):
			money = gameState.playerMoney[me]
			best = None
			for groupId in gameState.GetCompleteHouseGroups(me):
				if not gameState.IsGroupAllUnmortgaged(groupId): continue
				group = gameState.propertyGroup[groupId]
				cost = gameState.board[group[0]]['building_costs']
				limit = 5 if money > 1500 else 3 # Three houses give the best return, hotels when rich
				if min(gameState.spaceBuildings[s] for s in group) >= limit or money - cost < reserve: continue

				# The next building goes on the most expensive property with the fewest
				spaceId = min(group, key = lambda s: (gameState.spaceBuildings[s], -s))
				count = gameState.spaceBuildings[spaceId]
				rent = gameState.board[spaceId]['rent']
				gain = rent[count + 1] - (rent[0] * 2 if count == 0 else rent[count])
				if best is None or gain / float(cost) > best[0]:
					best = (gain / float(cost), groupId)
			if best is None:
				break
			groupId = best[1]
			if gameState.BuildBuildings(me, groupId, gameState.NumHousesInGroup(groupId)[0] + 1)[0]:
				break # Couldn't build (for example, no houses left)
		return True

	def ShowTradePlayerSelect(self):
		return False

	def ConsiderTrade(self, offer, gameState):
		return False # Doesn't trade yet

	def GetBuildingDemand(self, buildingType, available, gameState):
		groups = gameState.GetBuildableGroups(self.playerNum, buildingType)
		if not groups:
			return 0
		cost = min(gameState.board[gameState.propertyGroup[g][0]]['building_costs'] for g in groups)
		affordable = max(0, (gameState.playerMoney[self.playerNum] - self.Reserve(gameState)) // cost)
		return min(available, affordable)

	def GetBuildingBid(self, buildingType, groupIds, highestBid, highestBidder, gameState):
		# Bid for the set with the highest rents, up to half as much again as the building cost
		groupId = max(groupIds, key = lambda g: gameState.board[gameState.propertyGroup[g][-1]]['rent'][0])
		cost = gameState.board[gameState.propertyGroup[groupId][0]]['building_costs']
		limit = min(cost * 3 // 2, gameState.playerMoney[self.playerNum] - self.Reserve(gameState))
		bid = max(highestBid + 10, cost)
		if bid > limit:
			return None
		return groupId, bid
