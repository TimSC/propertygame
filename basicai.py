from interfaces import PlayerInterface

class BasicAIParameters(object):

	"""
	Settings for BasicAIInterface. Change any of them by name, for example
	BasicAIParameters(fairness=0.7, reserveBase=100). tuneai.py plays a variant against the
	defaults to see whether a change helps.
	"""

	def __init__(self, **changes):

		# Trading. A trade must gain this AI at least minimumGain, and the other player must not
		# gain much more: this AI's gain must be at least fairness times theirs (lower is more
		# willing). It offers trades that it would accept if it were the other player.
		self.minimumGain = 10
		self.fairness = 0.8
		self.jailCardValue = 30 # Value of a get out of jail free card in a trade
		self.retryRejectedAfter = 12 # Calls to DoTrading before asking the same player for the same set again
		self.spareTradeCandidates = 8 # How many of its least useful spare properties it considers offering
		self.tradeCashStep = 10 # Cash in offers is rounded to this
		self.tradeKeepReserveFraction = 0.5 # Fraction of its reserve it keeps when accepting a trade

		# How it values holdings in trades, as multiples of their prices. A colour set it could
		# still complete is worth 1 + openSetBonus * (fraction owned); one blocked by an opponent
		# is worth 1. Stations and utilities are worth more the more of them it holds (1-4, 1-2).
		self.completeSetMultiplier = 2.0
		self.openSetBonus = 0.3
		self.stationMultipliers = [1.0, 1.15, 1.35, 1.6]
		self.utilityMultipliers = [1.0, 1.3]

		# Buying and auctions. What a property is worth to it, as a multiple of its price,
		# depending on what owning it would do to its set: complete it, keep it open (plus a
		# bonus for each piece already held), block an opponent, or nothing (the set is split).
		self.completesSetWorth = 1.6
		self.openSetWorth = 1.1
		self.openSetWorthPerPiece = 0.2
		self.blocksSetWorth = 1.0
		self.splitSetWorth = 0.6
		# When buying, the fraction of its reserve it keeps back, by what the property does.
		# (It will mortgage other property to buy one that completes a set.)
		self.buyKeepOpen = 0.5
		self.buyKeepBlocks = 0.75
		self.buyKeepSplit = 1.0
		self.bidStepFraction = 0.05 # Auction bids rise by this fraction of the price
		self.completionBidMargin = 50 # Cash it keeps when bidding for a property that completes a set

		# Cash reserve for rent: reserveBase plus reserveRentFraction of the worst rent an
		# opponent's property could charge, up to reserveMax
		self.reserveBase = 150
		self.reserveRentFraction = 0.5
		self.reserveMax = 600
		self.unmortgageBuffer = 100 # Spare cash above the reserve before paying off a mortgage

		# Building. Three houses give the best return; hotels only when rich.
		self.housesPerProperty = 3
		self.hotelsWhenCashAbove = 1500
		self.shortageBidMultiplier = 1.5 # Most it bids for a building in a shortage, times its cost
		self.shortageBidStep = 10

		# Jail. Early on it gets out to buy property. Once few properties are left for sale and
		# opponents have built (so its reserve is high), it stays in to avoid their rent.
		self.stayInJailWhenUnownedBelow = 6
		self.stayInJailWhenReserveAbove = 250

		# How strong it thinks each colour set is, indexed by property group in board order:
		# brown, light blue, pink, orange, red, yellow, green, dark blue. 1.0 is neutral. It
		# scales what it will bid, how much cash it keeps back when buying, how it values sets in
		# trades and where it builds first. Common advice would be something like
		# [0.8, 1.05, 1.05, 1.25, 1.2, 1.1, 0.95, 1.0] (orange and red are landed on most, by
		# players leaving jail), but against a neutral AI that won only about 42% of two-player
		# games, by overpaying for the favoured sets, so the default is neutral.
		self.setStrength = [1.0] * 8

		for name, value in changes.items():
			if not hasattr(self, name):
				raise AttributeError("Unknown basic AI parameter: {}".format(name))
			setattr(self, name, value)

	def Changes(self):
		# The settings that differ from the defaults
		defaults = BasicAIParameters().__dict__
		return {name: value for name, value in self.__dict__.items() if value != defaults[name]}

class BasicAIInterface(PlayerInterface):

	"""
	A simple AI that tries to complete colour sets and build on them. It keeps a cash
	reserve, bids up to what a property is worth to it, mortgages its least useful
	property first when short of money, and trades for the pieces it needs. Its behaviour
	is set by a BasicAIParameters.
	"""

	def __init__(self, playerNum, params=None):
		super().__init__(playerNum)
		self.params = params if params is not None else BasicAIParameters()
		self.tradingRounds = 0
		self.rejectedOffers = {} # (opponent, groupId) -> trading round an offer for that set was rejected in

	def Strength(self, spaceId, gameState):
		# This AI's opinion of a space's colour set (stations and utilities are neutral)
		if spaceId in gameState.propertyInGroup:
			return self.params.setStrength[gameState.propertyInGroup[spaceId]]
		return 1.0

	def SetOf(self, spaceId, gameState):
		# The spaces that go together for rent: a colour group, the stations or the utilities
		space = gameState.board[spaceId]
		if space['type'] == 'property': return gameState.propertyGroup[space['property_group']]
		if space['type'] == 'station': return gameState.boardStations
		return gameState.boardUtilities

	def SetStatus(self, spaceId, gameState):
		# What owning this space would do to its set for this player: 'completes' it, keeps it
		# 'open' (it can still be completed), 'blocks' one opponent completing it, or 'split'
		# (nothing useful). Also returns how many of the rest of the set this player owns.
		others = [s for s in self.SetOf(spaceId, gameState) if s != spaceId]
		mine = len([s for s in others if gameState.spaceOwners[s] == self.playerNum])
		opponents = set(gameState.spaceOwners[s] for s in others) - set([None, self.playerNum])
		if mine == len(others):
			return 'completes', mine
		if not opponents:
			return 'open', mine
		if len(opponents) == 1 and all(gameState.spaceOwners[s] in opponents for s in others):
			return 'blocks', mine
		return 'split', mine

	def Worth(self, spaceId, gameState):
		# What a space is worth to this player, as a multiple of its price
		p = self.params
		status, mine = self.SetStatus(spaceId, gameState)
		if status == 'completes': return p.completesSetWorth
		if status == 'open': return p.openSetWorth + p.openSetWorthPerPiece * mine
		if status == 'blocks': return p.blocksSetWorth
		return p.splitSetWorth

	def Reserve(self, gameState):
		# Cash to keep in hand for rent: more once opponents have built houses
		p = self.params
		worst = 0
		for spaceId, owner in enumerate(gameState.spaceOwners):
			if owner in (None, self.playerNum) or gameState.spaceMortgaged[spaceId]: continue
			if gameState.board[spaceId]['type'] == 'property':
				worst = max(worst, gameState.CalcRent(self.playerNum, spaceId, 7))
		return min(p.reserveMax, p.reserveBase + int(worst * p.reserveRentFraction))

	def OptionToBuy(self, spaceId, gameState):
		p = self.params
		status, mine = self.SetStatus(spaceId, gameState)
		if status == 'completes':
			return True # Worth mortgaging other property for (the game only asks if it can be raised)
		price = gameState.board[spaceId]['price']
		fraction = {'open': p.buyKeepOpen, 'blocks': p.buyKeepBlocks, 'split': p.buyKeepSplit}[status]
		keep = self.Reserve(gameState) * fraction / self.Strength(spaceId, gameState)
		return gameState.playerMoney[self.playerNum] - price >= keep

	def GetAuctionBid(self, spaceId, highestBid, highestBidder, gameState):
		p = self.params
		price = gameState.board[spaceId]['price']
		if self.SetStatus(spaceId, gameState)[0] == 'completes':
			available = gameState.PlayerMaxMoneyThatCanBeRaised(self.playerNum) - p.completionBidMargin
		else:
			available = gameState.playerMoney[self.playerNum] - self.Reserve(gameState) // 2
		limit = min(int(price * self.Worth(spaceId, gameState) * self.Strength(spaceId, gameState)), available)
		if highestBid + 1 > limit:
			return None
		return min(limit, highestBid + max(1, int(price * p.bidStepFraction)))

	def StayInJail(self, gameState):
		p = self.params
		unowned = len([s for s, space in enumerate(gameState.board) if 'price' in space and gameState.spaceOwners[s] is None])
		return unowned < p.stayInJailWhenUnownedBelow and self.Reserve(gameState) > p.stayInJailWhenReserveAbove

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
			gameState.MortgageSpace(min(loose, key = lambda s: (self.Worth(s, gameState) * self.Strength(s, gameState), gameState.board[s]['mortgage'])))
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

	# Trading

	def SetValue(self, playerId, members, owners, gameState):
		# Value of a player's holding in one set, given who owns what (owners)
		p = self.params
		mine = [s for s in members if owners[s] == playerId]
		if not mine:
			return 0
		prices = sum(gameState.board[s]['price'] for s in mine)
		kind = gameState.board[members[0]]['type']
		if kind == 'station':
			multiplier = p.stationMultipliers[len(mine) - 1]
		elif kind == 'utility':
			multiplier = p.utilityMultipliers[len(mine) - 1]
		elif len(mine) == len(members):
			multiplier = p.completeSetMultiplier # A complete colour set can be built on
		elif all(owners[s] in (None, playerId) for s in members):
			multiplier = 1.0 + p.openSetBonus * len(mine) / len(members) # Could still be completed
		else:
			multiplier = 1.0 # Blocked by an opponent
		if kind == 'property':
			multiplier *= p.setStrength[gameState.propertyInGroup[members[0]]]
		# A mortgaged property is worth less by what it would cost to pay off
		mortgages = sum(gameState.UnmortgageCost(s) for s in mine if gameState.spaceMortgaged[s])
		return prices * multiplier - mortgages

	def PositionValue(self, playerId, owners, gameState):
		sets = list(gameState.propertyGroup.values()) + [gameState.boardStations, gameState.boardUtilities]
		return sum(self.SetValue(playerId, members, owners, gameState) for members in sets)

	def TradeGain(self, offer, side, gameState, before=None):
		# How much better off the player on this side of the offer would be. before is
		# their current position value, if already known.
		owners = list(gameState.spaceOwners)
		for fromSide in (0, 1):
			for spaceId in offer.spaces[fromSide]:
				owners[spaceId] = offer.playerIds[1 - fromSide]
		playerId = offer.playerIds[side]
		if before is None:
			before = self.PositionValue(playerId, gameState.spaceOwners, gameState)
		gain = self.PositionValue(playerId, owners, gameState) - before
		gain += offer.money[1 - side] - offer.money[side]
		gain += self.params.jailCardValue * (offer.jailCards[1 - side] - offer.jailCards[side])
		gain -= gameState.TradeInterestDue(offer, side)
		return gain

	def Acceptable(self, offer, side, gameState):
		# Would the player on this side accept, judged the way this AI judges trades?
		gain = self.TradeGain(offer, side, gameState)
		otherGain = self.TradeGain(offer, 1 - side, gameState)
		return gain >= self.params.minimumGain and gain >= self.params.fairness * otherGain

	def ConsiderTrade(self, offer, gameState):
		me = self.playerNum
		money = gameState.playerMoney[me]
		cashAfter = money - offer.money[1] + offer.money[0] - gameState.TradeInterestDue(offer, 1)
		if cashAfter < min(money, int(self.Reserve(gameState) * self.params.tradeKeepReserveFraction)):
			return False # Would leave too little cash for rent
		return self.Acceptable(offer, 1, gameState)

	def FindTradeOffer(self, gameState):
		# Look for an opponent holding the last pieces of a colour set, and the best offer
		# for them that they should still accept
		p = self.params
		me = self.playerNum
		money = gameState.playerMoney[me]
		reserve = self.Reserve(gameState)
		mine = gameState.TradeableSpaces(me)
		complete = set(gameState.GetCompleteHouseGroups(me))
		best = None
		for groupId, group in gameState.propertyGroup.items():
			if groupId in complete or not any(gameState.spaceOwners[s] == me for s in group):
				continue
			missing = [s for s in group if gameState.spaceOwners[s] != me]
			holders = set(gameState.spaceOwners[s] for s in missing)
			if None in holders or len(holders) != 1:
				continue # Still for sale, or held by more than one opponent
			opponent = holders.pop()
			if gameState.playerBankrupt[opponent] or any(s not in gameState.TradeableSpaces(opponent) for s in missing):
				continue

			# Offer cash, or one of the spare properties least useful to me plus cash
			spare = [s for s in mine if s not in group and gameState.propertyInGroup.get(s) not in complete]
			spare = sorted(spare, key = lambda s: self.Worth(s, gameState))[:p.spareTradeCandidates]
			myBefore = self.PositionValue(me, gameState.spaceOwners, gameState)
			theirBefore = self.PositionValue(opponent, gameState.spaceOwners, gameState)
			for give in [[]] + [[s] for s in spare]:
				offer = gameState.NewTrade(me, opponent)
				offer.spaces = [give, list(missing)]
				# Gains before any cash changes hands. Cash just moves value between us.
				myGain = self.TradeGain(offer, 0, gameState, myBefore)
				theirGain = self.TradeGain(offer, 1, gameState, theirBefore)

				# Cash (positive: paid by me) that makes it acceptable to them:
				# theirGain + cash >= fairness * (myGain - cash) + minimumGain
				cash = (p.fairness * myGain + p.minimumGain - theirGain) / (1 + p.fairness)
				cash = int(-(-cash // p.tradeCashStep) * p.tradeCashStep) # Round up
				if cash >= 0:
					offer.money = [cash, 0]
				else:
					cash = -min(-cash, gameState.playerMoney[opponent])
					offer.money = [0, -cash]
				myNet, theirNet = myGain - cash, theirGain + cash
				if myNet < p.minimumGain or money - offer.money[0] < reserve:
					continue
				if myNet < p.fairness * theirNet or theirNet < p.minimumGain or theirNet < p.fairness * myNet:
					continue # Not a trade both sides would accept
				if gameState.TradeProblems(offer):
					continue
				if self.rejectedOffers.get((opponent, groupId), -99) > self.tradingRounds - p.retryRejectedAfter:
					continue # They turned down an offer for this set recently
				if best is None or myNet > best[0]:
					best = (myNet, offer)
		return best[1] if best is not None else None

	def DoTrading(self, gameState):
		# Between turns: try one trade for a set, pay off mortgages, then build on complete sets
		p = self.params
		me = self.playerNum
		self.tradingRounds += 1
		offer = self.FindTradeOffer(gameState)
		if offer is not None and not gameState.ProposeTrade(offer):
			groupId = gameState.propertyInGroup[offer.spaces[1][0]]
			self.rejectedOffers[(offer.playerIds[1], groupId)] = self.tradingRounds

		reserve = self.Reserve(gameState)
		mortgaged = [s for s, owner in enumerate(gameState.spaceOwners) if owner == me and gameState.spaceMortgaged[s]]
		for spaceId in sorted(mortgaged, key = lambda s: -self.Worth(s, gameState)):
			if gameState.playerMoney[me] - gameState.UnmortgageCost(spaceId) >= reserve + p.unmortgageBuffer:
				gameState.UnmortgageSpace(spaceId)

		for attempt in range(60):
			money = gameState.playerMoney[me]
			best = None
			for groupId in gameState.GetCompleteHouseGroups(me):
				if not gameState.IsGroupAllUnmortgaged(groupId): continue
				group = gameState.propertyGroup[groupId]
				cost = gameState.board[group[0]]['building_costs']
				limit = 5 if money > p.hotelsWhenCashAbove else p.housesPerProperty
				if min(gameState.spaceBuildings[s] for s in group) >= limit or money - cost < reserve: continue

				# The next building goes on the most expensive property with the fewest
				spaceId = min(group, key = lambda s: (gameState.spaceBuildings[s], -s))
				count = gameState.spaceBuildings[spaceId]
				rent = gameState.board[spaceId]['rent']
				gain = (rent[count + 1] - (rent[0] * 2 if count == 0 else rent[count])) * p.setStrength[groupId]
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

	def GetBuildingDemand(self, buildingType, available, gameState):
		groups = gameState.GetBuildableGroups(self.playerNum, buildingType)
		if not groups:
			return 0
		cost = min(gameState.board[gameState.propertyGroup[g][0]]['building_costs'] for g in groups)
		affordable = max(0, (gameState.playerMoney[self.playerNum] - self.Reserve(gameState)) // cost)
		return min(available, affordable)

	def GetBuildingBid(self, buildingType, groupIds, highestBid, highestBidder, gameState):
		# Bid for the set with the highest rents, up to a multiple of the building cost
		p = self.params
		groupId = max(groupIds, key = lambda g: gameState.board[gameState.propertyGroup[g][-1]]['rent'][0])
		cost = gameState.board[gameState.propertyGroup[groupId][0]]['building_costs']
		limit = min(int(cost * p.shortageBidMultiplier), gameState.playerMoney[self.playerNum] - self.Reserve(gameState))
		bid = max(highestBid + p.shortageBidStep, cost)
		if bid > limit:
			return None
		return groupId, bid
