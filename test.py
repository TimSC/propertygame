import random
from propertygame import PropertyGame, GlobalInterface
from interfaces import *

def SetCardPosition(deck, cardName, position):
	
	ind = None
	for i, card in enumerate(deck):
		if card['name'] == cardName:
			ind = i
			break

	card = deck.pop(ind)
	deck.insert(position, card)

def CheckBuildingCode():

	playerInterfaces = [TestInterface(0), TestInterface(1), TestInterface(2)]

	globalInterface = GlobalInterface()

	# Build n houses on unimproved group
	ownerId = 0
	groupId = 3
	propertyGame = PropertyGame(globalInterface, playerInterfaces)
	assert propertyGame.GetGroupOwner(groupId) is None
	freeHouses, freeHotels = propertyGame.GetFreeBuildings()
	assert len(freeHouses) == propertyGame.houseMarkers
	assert len(freeHotels) == propertyGame.hotelMarkers

	numSpacesInGroup = len(propertyGame.propertyGroup[groupId])
	fullHousesNeeded = 4 * numSpacesInGroup
	fullBuildingsNeeded = 5 * numSpacesInGroup

	for numBuildings in range(fullBuildingsNeeded+1):

		propertyGame = PropertyGame(globalInterface, playerInterfaces)
		
		for spaceId in propertyGame.propertyGroup[groupId]:
			propertyGame.spaceOwners[spaceId] = ownerId # Assign space ownership to player 0

		impossible, numAllowed,reasons, planCost = propertyGame.SetNumBuildingsInGroup(groupId, numBuildings)
		assert not impossible
		assert numAllowed is None
		existingHouses, groupHouses = propertyGame.NumHousesInGroup(groupId)
		assert existingHouses == numBuildings
		freeHouses, freeHotels = propertyGame.GetFreeBuildings()

		diffHouses = max([g[1] for g in groupHouses]) - min([g[1] for g in groupHouses])
		assert diffHouses <= 1 # Add houses as evenly as possible

		expectedCost = 0
		for spaceId, nb in groupHouses:
			space = propertyGame.board[spaceId]
			expectedCost += nb * space['building_costs']
		assert propertyGame.playerMoney[ownerId] == 1500 - expectedCost

		if numBuildings <= fullHousesNeeded:
			assert len(freeHouses) == propertyGame.houseMarkers-numBuildings
			assert len(freeHotels) == propertyGame.hotelMarkers
		if numBuildings == fullBuildingsNeeded:
			assert len(freeHouses) == propertyGame.houseMarkers
			assert len(freeHotels) == propertyGame.hotelMarkers-numSpacesInGroup

	# Build n houses on partly improved group
	groupId = 4
	propertyGame = PropertyGame(globalInterface, playerInterfaces)

	numSpacesInGroup = len(propertyGame.propertyGroup[groupId])
	fullHousesNeeded = 4 * len(propertyGame.propertyGroup[groupId])
	existingBuildings = 7

	for numBuildings in range(existingBuildings, fullHousesNeeded+1):

		propertyGame = PropertyGame(globalInterface, playerInterfaces)
		
		for spaceId in propertyGame.propertyGroup[groupId]:
			propertyGame.spaceOwners[spaceId] = ownerId # Assign space ownership to player 0	

		for i in range(existingBuildings): #Add buildings
			spaceId = propertyGame.propertyGroup[groupId][i % numSpacesInGroup]
			propertyGame.boardHouses[i] = spaceId
			propertyGame.boardGroupBuildOrder[groupId].append(spaceId)

		impossible, numAllowed, reasons, planCost = propertyGame.SetNumBuildingsInGroup(groupId, numBuildings)
		assert not impossible
		assert numAllowed is None 
		existingHouses, groupHouses = propertyGame.NumHousesInGroup(groupId)
		assert existingHouses == numBuildings
		freeHouses, freeHotels = propertyGame.GetFreeBuildings()

		diffHouses = max([g[1] for g in groupHouses]) - min([g[1] for g in groupHouses])
		assert diffHouses <= 1 # Add houses as evenly as possible

		if numBuildings <= 12:
			assert len(freeHouses) == propertyGame.houseMarkers-numBuildings
			assert len(freeHotels) == propertyGame.hotelMarkers

	# Try build too much
	groupId = 4
	propertyGame = PropertyGame(globalInterface, playerInterfaces)

	numSpacesInGroup = len(propertyGame.propertyGroup[groupId])
	fullHousesNeeded = 4 * len(propertyGame.propertyGroup[groupId])
	fullBuildingsNeeded = 5 * numSpacesInGroup
	existingBuildings = 4

	for numBuildings in range(fullBuildingsNeeded+1, fullBuildingsNeeded+10):

		propertyGame = PropertyGame(globalInterface, playerInterfaces)
		
		for spaceId in propertyGame.propertyGroup[groupId]:
			propertyGame.spaceOwners[spaceId] = ownerId # Assign space ownership to player 0
		propertyGame.playerMoney[ownerId] = 2000	
		
		for i in range(existingBuildings):
			spaceId = propertyGame.propertyGroup[groupId][i % numSpacesInGroup]
			propertyGame.boardHouses[i] = spaceId
			propertyGame.boardGroupBuildOrder[groupId].append(spaceId)

		impossible, numAllowed, reasons, planCost = propertyGame.SetNumBuildingsInGroup(groupId, numBuildings)
		assert impossible
		assert numAllowed == 11

		existingHouses, groupHouses = propertyGame.NumHousesInGroup(groupId)
		assert existingHouses == existingBuildings
		freeHouses, freeHotels = propertyGame.GetFreeBuildings()

		assert len(freeHouses) == propertyGame.houseMarkers-existingBuildings
		assert len(freeHotels) == propertyGame.hotelMarkers

	# Try build too expensive
	groupId = 5
	propertyGame = PropertyGame(globalInterface, playerInterfaces)

	numSpacesInGroup = len(propertyGame.propertyGroup[groupId])
	fullHousesNeeded = 4 * len(propertyGame.propertyGroup[groupId])
	fullBuildingsNeeded = 5 * numSpacesInGroup
	existingBuildings = 6

	for numBuildings in range(existingBuildings+3, fullBuildingsNeeded):

		propertyGame = PropertyGame(globalInterface, playerInterfaces)
		
		for spaceId in propertyGame.propertyGroup[groupId]:
			propertyGame.spaceOwners[spaceId] = ownerId # Assign space ownership to player 0
		propertyGame.playerMoney[ownerId] = 360	
		
		for i in range(existingBuildings):
			spaceId = propertyGame.propertyGroup[groupId][i % numSpacesInGroup]
			propertyGame.boardHouses[i] = spaceId
			propertyGame.boardGroupBuildOrder[groupId].append(spaceId)

		impossible, numAllowed, reasons, planCost = propertyGame.SetNumBuildingsInGroup(groupId, numBuildings)
		assert impossible
		assert numAllowed == 2

		existingHouses, groupHouses = propertyGame.NumHousesInGroup(groupId)
		assert existingHouses == existingBuildings
		freeHouses, freeHotels = propertyGame.GetFreeBuildings()

		assert len(freeHouses) == propertyGame.houseMarkers-existingBuildings
		assert len(freeHotels) == propertyGame.hotelMarkers

	# Try build with housing shortage
	groupId = 6
	oppenentOwnerId = 1
	propertyGame = PropertyGame(globalInterface, playerInterfaces)

	numSpacesInGroup = len(propertyGame.propertyGroup[groupId])
	fullHousesNeeded = 4 * len(propertyGame.propertyGroup[groupId])
	fullBuildingsNeeded = 5 * numSpacesInGroup
	existingBuildings = 3
	freeHouses = 2

	for numBuildings in range(existingBuildings, fullHousesNeeded):

		propertyGame = PropertyGame(globalInterface, playerInterfaces)
		shouldBePossible = (numBuildings - existingBuildings) <= freeHouses

		for spaceId, space in enumerate(propertyGame.board):
			propertyGame.spaceOwners[spaceId] = oppenentOwnerId # Give entire board to opponent
		for spaceId in propertyGame.propertyGroup[groupId]:
			propertyGame.spaceOwners[spaceId] = ownerId # Assign space ownership to player 0
		
		cursor = 0
		for i in range(propertyGame.houseMarkers-freeHouses):
			while propertyGame.board[cursor]['type'] != 'property':
				cursor += 1
				if cursor >= len(propertyGame.board): cursor = 0
			
			propertyGame.boardHouses[i] = cursor # Put one house on properties
			propertyGame.boardGroupBuildOrder[propertyGame.propertyInGroup[cursor]].append(cursor)

			cursor += 1
			if cursor >= len(propertyGame.board): cursor = 0

		impossible, numAllowed, reasons, planCost = propertyGame.SetNumBuildingsInGroup(groupId, numBuildings)
		assert impossible != shouldBePossible
		if impossible:
			assert numAllowed == freeHouses

def CheckRemoveBuildings():

	playerInterfaces = [TestInterface(0), TestInterface(1), TestInterface(2)]

	globalInterface = GlobalInterface()

	# Remove n houses from fully hotel group
	ownerId = 0
	groupId = 4
	propertyGame = PropertyGame(globalInterface, playerInterfaces)

	numSpacesInGroup = len(propertyGame.propertyGroup[groupId])
	fullHousesNeeded = 4 * len(propertyGame.propertyGroup[groupId])
	numBuildingsToFull = 5 * numSpacesInGroup

	for numBuildings in range(0, numBuildingsToFull+1):

		propertyGame = PropertyGame(globalInterface, playerInterfaces)
		
		for i, spaceId in enumerate(propertyGame.propertyGroup[groupId]):
			propertyGame.spaceOwners[spaceId] = ownerId # Assign space ownership to player 0	
			propertyGame.boardHotels[i] = spaceId # Put one hotel on properties
		costToBuild = 0
		for i in range(numBuildingsToFull):			
			spaceId = propertyGame.propertyGroup[groupId][i % len(propertyGame.propertyGroup[groupId])]
			space = propertyGame.board[spaceId]

			if i >= numBuildings:
				costToBuild += space['building_costs']
			propertyGame.boardGroupBuildOrder[groupId].append(spaceId)

		impossible, numAllowed, reasons, planCost = propertyGame.SetNumBuildingsInGroup(groupId, numBuildings)

		assert not impossible
		assert numAllowed is None 

		existingHouses, groupHouses = propertyGame.NumHousesInGroup(groupId)

		assert existingHouses == numBuildings
		freeHouses, freeHotels = propertyGame.GetFreeBuildings()

		diffHouses = max([g[1] for g in groupHouses]) - min([g[1] for g in groupHouses])
		assert diffHouses <= 1 # Add houses as evenly as possible

		if numBuildings <= 12:
			assert len(freeHouses) == propertyGame.houseMarkers-numBuildings
			assert len(freeHotels) == propertyGame.hotelMarkers
		else:
			assert len(freeHotels) == propertyGame.hotelMarkers-numBuildings+fullHousesNeeded

		assert propertyGame.playerMoney[ownerId] == 1500 + costToBuild // 2

def CheckNormalGameplay():
	playerInterfaces = [TestInterface(0), TestInterface(1), TestInterface(2)]

	globalInterface = GlobalInterface()

	propertyGame = PropertyGame(globalInterface, playerInterfaces)
	propertyGame.playerTurn = 0

	SetCardPosition(propertyGame.chanceCards, "AdvanceUtility", 0)
	SetCardPosition(propertyGame.chanceCards, "TripReadingTrainStation", 1)
	SetCardPosition(propertyGame.chanceCards, "BuildingLoadMature", 2)
	SetCardPosition(propertyGame.chanceCards, "AdvanceIllinois", 3)
	SetCardPosition(propertyGame.chanceCards, "TripBoardwalk", 4)
	SetCardPosition(propertyGame.chanceCards, "GoToJailCard", 5)
	SetCardPosition(propertyGame.chanceCards, "AdvanceToGo", 6)

	SetCardPosition(propertyGame.communityCards, "BeautyContest", 0)
	SetCardPosition(propertyGame.communityCards, "StreetRepairs", 1)

	# Based on https://www.youtube.com/watch?v=ds-8i3o1qUM
	# Turn 0
	# Player 0 
	playerInterfaces[0].optionToBuy = 1
	propertyGame.DoTurn([(3,4)])
	if propertyGame.playerPositions[0] != 12:
		raise RuntimeError()
	if propertyGame.playerMoney[0] != 1350:
		raise RuntimeError()
	if propertyGame.spaceOwners[12] != 0:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()
	
	# Player 1
	playerInterfaces[1].optionToBuy = 1
	propertyGame.DoTurn([(1,4)])
	if propertyGame.playerPositions[1] != 5:
		raise RuntimeError()
	if propertyGame.playerMoney[1] != 1300:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 2
	playerInterfaces[2].optionToBuy = 1
	propertyGame.DoTurn([(3,5)])
	if propertyGame.playerPositions[2] != 8:
		raise RuntimeError()
	if propertyGame.playerMoney[2] != 1400:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Turn 1
	# Player 0 
	playerInterfaces[0].optionToBuy = 0
	playerInterfaces[0].getAuctionBid = 0
	playerInterfaces[1].getAuctionBid = 99
	playerInterfaces[2].getAuctionBid = 100
	propertyGame.DoTurn([(0,2)]) # Hack because human players forgot this was a double
	if propertyGame.playerPositions[0] != 14:
		raise RuntimeError()
	if propertyGame.playerMoney[2] != 1300:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 1
	playerInterfaces[1].Reset()
	propertyGame.DoTurn([(3,4)])
	if propertyGame.playerPositions[1] != 12:
		raise RuntimeError()
	if propertyGame.playerMoney[1] != 1272: # Human mistake in video here! They realize later.
		raise RuntimeError()
	if propertyGame.playerMoney[0] != 1378:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 2
	playerInterfaces[2].Reset()
	playerInterfaces[2].optionToBuy = 1
	propertyGame.DoTurn([(6,4)])
	if propertyGame.playerPositions[2] != 18:
		raise RuntimeError()
	if propertyGame.playerMoney[2] != 1120:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Turn 2
	# Player 0 
	playerInterfaces[0].Reset()
	playerInterfaces[0].optionToBuy = 1
	propertyGame.DoTurn([(1,4)])
	if propertyGame.playerPositions[0] != 19:
		raise RuntimeError()
	if propertyGame.playerMoney[0] != 1178:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 1
	playerInterfaces[1].Reset()
	playerInterfaces[1].optionToBuy = 1
	propertyGame.DoTurn([(3,3), (1,2)])
	if propertyGame.playerPositions[1] != 21:
		raise RuntimeError()
	if propertyGame.playerMoney[1] != 1038: # 1272 - 14 - 220
		raise RuntimeError()
	if propertyGame.playerMoney[2] != 1134:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 2
	playerInterfaces[2].Reset()
	playerInterfaces[2].optionToBuy = 1
	propertyGame.DoTurn([(6,3)])
	if propertyGame.playerPositions[2] != 27:
		raise RuntimeError()
	if propertyGame.playerMoney[2] != 874:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Turn 2
	# Player 0 
	playerInterfaces[0].Reset()
	propertyGame.DoTurn([(1,2)])
	if propertyGame.playerPositions[0] != 5:
		raise RuntimeError()
	if propertyGame.playerMoney[0] != 1353:
		raise RuntimeError()
	if propertyGame.playerMoney[1] != 1063:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 1
	playerInterfaces[1].Reset()
	playerInterfaces[1].optionToBuy = 0
	playerInterfaces[0].getAuctionBid = 0
	playerInterfaces[1].getAuctionBid = 209
	playerInterfaces[2].getAuctionBid = 210
	propertyGame.DoTurn([(2,6)])
	if propertyGame.playerPositions[1] != 29:
		raise RuntimeError()
	if propertyGame.playerMoney[2] != 664:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 2 (buy short line)
	playerInterfaces[2].Reset()
	playerInterfaces[2].optionToBuy = 0
	playerInterfaces[0].getAuctionBid = 0
	playerInterfaces[1].getAuctionBid = 10
	playerInterfaces[2].getAuctionBid = 9
	propertyGame.DoTurn([(3,5)])
	if propertyGame.playerPositions[2] != 35:
		raise RuntimeError()
	if propertyGame.playerMoney[1] != 1053:
		raise RuntimeError()
	if propertyGame.spaceOwners[35] != 1:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Turn 3
	# Player 0 
	playerInterfaces[0].Reset()
	playerInterfaces[0].optionToBuy = 1
	propertyGame.DoTurn([(2,6)])
	if propertyGame.playerPositions[0] != 13:
		raise RuntimeError()
	if propertyGame.playerMoney[0] != 1213:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 1
	playerInterfaces[1].Reset()
	propertyGame.DoTurn([(3,6)])
	if propertyGame.playerPositions[1] != 38:
		raise RuntimeError()
	if propertyGame.playerMoney[1] != 953:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()
	
	# Player 2
	playerInterfaces[2].Reset()
	playerInterfaces[2].optionToBuy = 1
	propertyGame.DoTurn([(5,5), (1,5)])
	if propertyGame.playerPositions[2] != 11:
		raise RuntimeError()
	if propertyGame.playerMoney[1] != 1003:
		raise RuntimeError()
	if propertyGame.playerMoney[2] != 674: # Human error, this should be 664 + 200 - 50 - 140
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Turn 4
	# Player 0 
	playerInterfaces[0].Reset()
	propertyGame.DoTurn([(1,6)])
	if propertyGame.playerPositions[0] != 20:
		raise RuntimeError()
	if propertyGame.playerMoney[0] != 1213:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 1
	# Lands on go, rerolls and lands on own station.
	playerInterfaces[1].Reset()
	propertyGame.DoTurn([(1,1), (2,3)])
	if propertyGame.playerPositions[1] != 5:
		raise RuntimeError()
	if propertyGame.playerMoney[1] != 1203:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 2
	# Rolls and lands on 21 and pays rent, rerolls and lands on 29 (already owns)
	playerInterfaces[2].Reset()
	propertyGame.DoTurn([(5,5), (5,3)])
	if propertyGame.playerPositions[2] != 29:
		raise RuntimeError()
	if propertyGame.playerMoney[2] != 656:
		raise RuntimeError()
	if propertyGame.playerMoney[1] != 1221:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()
	
	# Turn 5
	# Player 0
	# Rolls and lands on 28 (buys)
	playerInterfaces[0].Reset()
	playerInterfaces[0].optionToBuy = 1
	propertyGame.DoTurn([(2,6)])
	if propertyGame.playerPositions[0] != 28:
		raise RuntimeError()
	if propertyGame.playerMoney[0] != 1063:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 1
	# Lands on 16 (buys)
	playerInterfaces[1].Reset()
	playerInterfaces[1].optionToBuy = 1
	propertyGame.DoTurn([(5,6)])
	if propertyGame.playerPositions[1] != 16:
		raise RuntimeError()
	if propertyGame.playerMoney[1] != 1041:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 2
	# Rolls and lands 38 luxury tax
	playerInterfaces[2].Reset()
	propertyGame.DoTurn([(6,3)])
	if propertyGame.playerPositions[2] != 38:
		raise RuntimeError()
	if propertyGame.playerMoney[2] != 556:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Turn 6
	# Player 0
	# Lands on 38 luxury tax, rerolls and lands on 5 (pays rent)
	playerInterfaces[0].Reset()
	playerInterfaces[0].optionToBuy = 1
	propertyGame.DoTurn([(5,5), (4,3)])
	if propertyGame.playerPositions[0] != 5:
		raise RuntimeError()
	if propertyGame.playerMoney[0] != 1063-100+200-50:
		raise RuntimeError()
	if propertyGame.playerMoney[1] != 1041+50:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 1
	# Lands on 26 (triggers auction). Player 2 gets a full set (yellow).
	playerInterfaces[1].Reset()
	playerInterfaces[1].optionToBuy = 0
	playerInterfaces[0].getAuctionBid = 199
	playerInterfaces[1].getAuctionBid = 0
	playerInterfaces[2].getAuctionBid = 200
	propertyGame.DoTurn([(4,6)])
	if propertyGame.playerPositions[1] != 26:
		raise RuntimeError()
	if propertyGame.playerMoney[2] != 356:
		raise RuntimeError()
	if propertyGame.GetGroupOwner(propertyGame.propertyInGroup[26]) != 2:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 2
	# Lands on chance, building loan matures (human player forgets he passed go)
	playerInterfaces[2].Reset()
	propertyGame.DoTurn([(6,3)])
	if propertyGame.playerPositions[2] != 7:
		raise RuntimeError()
	if propertyGame.playerMoney[2] != 706:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Turn 6
	# Player 0
	# Rolls and lands on 10
	playerInterfaces[0].Reset()
	propertyGame.DoTurn([(1,4)])
	if propertyGame.playerPositions[0] != 10:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 1
	# Lands on go to jail
	playerInterfaces[1].Reset()
	propertyGame.DoTurn([(1,3)])
	if propertyGame.playerPositions[1] != None:
		raise RuntimeError()
	if propertyGame.playerTimeInJail[1] != 0:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 2
	# Lands on 14 (already owned)
	playerInterfaces[2].Reset()
	propertyGame.DoTurn([(4,3)])
	if propertyGame.playerPositions[2] != 14:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Turn 7
	# Player 0
	# Lands on community chest (BeautyContest)
	playerInterfaces[0].Reset()
	propertyGame.DoTurn([(3,4)])
	if propertyGame.playerPositions[0] != 17:
		raise RuntimeError()
	if propertyGame.playerMoney[0] != 1123:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 1
	# Rolls to get out of jail and fails
	playerInterfaces[1].Reset()
	propertyGame.DoTurn([(1,3)])
	if propertyGame.playerPositions[1] != None:
		raise RuntimeError()
	if propertyGame.playerTimeInJail[1] != 1:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 2
	# Lands on 18 (already owned)
	playerInterfaces[2].Reset()
	propertyGame.DoTurn([(1,3)])
	if propertyGame.playerPositions[2] != 18:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Turn 8
	# Player 0
	# Lands on 24 (buys for 240)
	playerInterfaces[0].Reset()
	playerInterfaces[0].optionToBuy = 1
	propertyGame.DoTurn([(3,4)])
	if propertyGame.playerPositions[0] != 24:
		raise RuntimeError()
	if propertyGame.playerMoney[0] != 883:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 1
	# Rolls to get out of jail and fails
	playerInterfaces[1].Reset()
	propertyGame.DoTurn([(1,3)])
	if propertyGame.playerPositions[1] != None:
		raise RuntimeError()
	if propertyGame.playerTimeInJail[1] != 2:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 2
	# Lands on 26 (already owned), rerolls and lands on 31 (triggers auction, player 0 buys)
	playerInterfaces[2].Reset()
	playerInterfaces[2].optionToBuy = 0
	playerInterfaces[0].getAuctionBid = 200
	playerInterfaces[1].getAuctionBid = 199
	playerInterfaces[2].getAuctionBid = 0
	propertyGame.DoTurn([(4,4), (1,4)])
	if propertyGame.playerPositions[2] != 31:
		raise RuntimeError()
	if propertyGame.playerMoney[0] != 683:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Turn 9
	# Player 0
	# Lands on 29 (pays rent of 48)
	playerInterfaces[0].Reset()
	propertyGame.DoTurn([(1,4)])
	if propertyGame.playerPositions[0] != 29:
		raise RuntimeError()
	if propertyGame.playerMoney[0] != 683-48:
		raise RuntimeError()
	if propertyGame.playerMoney[2] != 706+48:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 1
	# Pays to get out of jail, lands on 21 (already owned)
	playerInterfaces[1].Reset()
	playerInterfaces[1].payGetOutOfJail = True
	propertyGame.DoTurn([(5,6)])
	if propertyGame.playerPositions[1] != 21:
		raise RuntimeError()
	if propertyGame.playerTimeInJail[1] != None:
		raise RuntimeError()
	if propertyGame.playerMoney[1] != 1041:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()
	
	# Player 2
	# Lands on 37 (buys for 350)
	playerInterfaces[2].Reset()
	playerInterfaces[2].optionToBuy = 1
	propertyGame.DoTurn([(4,2)])
	if propertyGame.playerPositions[2] != 37:
		raise RuntimeError()
	if propertyGame.playerMoney[2] != 404:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Turn 10
	# Player 0
	# Lands on 35 (rent is 50)
	playerInterfaces[0].Reset()
	propertyGame.DoTurn([(1,5)])
	if propertyGame.playerPositions[0] != 35:
		raise RuntimeError()
	if propertyGame.playerMoney[0] != 585:
		raise RuntimeError()
	if propertyGame.playerMoney[1] != 1091:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 1
	# Lands on 28 (rent is 70)
	playerInterfaces[1].Reset()
	propertyGame.DoTurn([(4,3)])
	if propertyGame.playerPositions[1] != 28:
		raise RuntimeError()
	if propertyGame.playerMoney[0] != 655:
		raise RuntimeError()
	if propertyGame.playerMoney[1] != 1021:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 1 takes another turn (human error)
	# Lands on 36, advances to 24 plays (rent of 20)
	propertyGame.playerTurn = 1
	playerInterfaces[1].Reset()
	propertyGame.DoTurn([(5,3)])
	if propertyGame.playerPositions[1] != 24:
		raise RuntimeError()
	if propertyGame.playerMoney[1] != 1201:
		raise RuntimeError()
	if propertyGame.playerMoney[0] != 675:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 2
	# Passes go, lands on chance 7 (TripBoardwalk) buys and gets a second group
	playerInterfaces[2].Reset()
	playerInterfaces[2].optionToBuy = 1
	propertyGame.DoTurn([(4,6)])
	if propertyGame.playerPositions[2] != 39:
		raise RuntimeError()
	if propertyGame.playerMoney[2] != 204:
		raise RuntimeError()
	if propertyGame.GetGroupOwner(propertyGame.propertyInGroup[39]) != 2:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Turn 11
	# Player 0
	# Lands on 5 (rent is 50), rerolls and lands on 12 (owned)
	playerInterfaces[0].Reset()
	propertyGame.DoTurn([(5,5), (1,6)])
	if propertyGame.playerPositions[0] != 12:
		raise RuntimeError()
	if propertyGame.playerMoney[0] != 825:
		raise RuntimeError()
	if propertyGame.playerMoney[1] != 1251:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 1
	# Lands on 29 (pays rent of 48)
	playerInterfaces[0].Reset()
	propertyGame.DoTurn([(1,4)])
	if propertyGame.playerPositions[1] != 29:
		raise RuntimeError()
	if propertyGame.playerMoney[1] != 1251-48:
		raise RuntimeError()
	if propertyGame.playerMoney[2] != 204+48:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 2
	# Lands on 15 (triggers auction, player 1 buys)
	propertyGame.playerPositions[2] = 7 # Human error, starts count from space 7
	playerInterfaces[2].Reset()
	playerInterfaces[2].optionToBuy = 0
	playerInterfaces[0].getAuctionBid = 159
	playerInterfaces[1].getAuctionBid = 160
	playerInterfaces[2].getAuctionBid = 0
	propertyGame.DoTurn([(5,3)])
	if propertyGame.playerPositions[2] != 15:
		raise RuntimeError()
	if propertyGame.playerMoney[1] != 1043:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Turn 12
	# Player 0
	# Lands on 21 (rent 18)
	playerInterfaces[0].Reset()
	propertyGame.DoTurn([(3,6)])
	if propertyGame.playerPositions[0] != 21:
		raise RuntimeError()
	if propertyGame.playerMoney[0] != 807:
		raise RuntimeError()
	if propertyGame.playerMoney[1] != 1061:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 1
	# Lands on 37 (pays rent of 70)
	playerInterfaces[0].Reset()
	propertyGame.DoTurn([(3,5)])
	if propertyGame.playerPositions[1] != 37:
		raise RuntimeError()
	if propertyGame.playerMoney[1] != 991:
		raise RuntimeError()
	if propertyGame.playerMoney[2] != 322:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 2
	# Lands on 25 (triggers auction, player 1 wins and gets the full set of stations)
	# lands on 27 (owned), rolls a third double and goes to jail
	playerInterfaces[2].Reset()
	playerInterfaces[2].optionToBuy = 0
	playerInterfaces[0].getAuctionBid = 199
	playerInterfaces[1].getAuctionBid = 200
	playerInterfaces[2].getAuctionBid = 0
	propertyGame.DoTurn([(5,5), (1,1), (2,2)])
	if propertyGame.playerPositions[2] != None:
		raise RuntimeError()
	if propertyGame.playerTimeInJail[2] != 0:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Turn 13
	# Player 0
	# Lands on 26 (rent 44)
	playerInterfaces[0].Reset()
	propertyGame.DoTurn([(1,4)])
	propertyGame.EndPlayerTurn()
	
	# Player 1
	# Passes go, Lands on 1
	playerInterfaces[1].Reset()
	playerInterfaces[1].optionToBuy = 1
	propertyGame.DoTurn([(1,3)])
	if propertyGame.playerPositions[1] != 1:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 2
	# Rolls to get out of jail and fails
	playerInterfaces[2].Reset()
	propertyGame.DoTurn([(1,3)])
	if propertyGame.playerPositions[2] != None:
		raise RuntimeError()
	if propertyGame.playerTimeInJail[2] != 1:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Turn 13
	# Player 0
	# Lands on 32 (buys), lands un luxury tax
	playerInterfaces[0].Reset()
	playerInterfaces[0].optionToBuy = 1
	propertyGame.DoTurn([(3,3), (1,5)])
	propertyGame.EndPlayerTurn()

	# Player 1
	# Lands on just visiting
	playerInterfaces[1].Reset()
	propertyGame.DoTurn([(6,3)])
	if propertyGame.playerPositions[1] != 10:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 2
	# Rolls to get out of jail and fails
	playerInterfaces[2].Reset()
	propertyGame.DoTurn([(1,3)])
	if propertyGame.playerPositions[2] != None:
		raise RuntimeError()
	if propertyGame.playerTimeInJail[2] != 2:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Turn 14
	# Player 0
	# Lands on 9 (buys)
	playerInterfaces[0].Reset()
	playerInterfaces[0].optionToBuy = 1
	propertyGame.DoTurn([(6,5)])
	if propertyGame.playerPositions[0] != 9:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 1
	# Lands on 15 (owned)
	playerInterfaces[1].Reset()
	propertyGame.DoTurn([(1,4)])
	if propertyGame.playerPositions[1] != 15:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 2
	# Rolls to get out of jail and fails (human error here as they player moves out of jail on 3rd attempt)
	playerInterfaces[2].Reset()
	propertyGame.DoTurn([(1,3)])
	if propertyGame.playerPositions[2] != 14:
		raise RuntimeError()
	if propertyGame.playerTimeInJail[2] != None:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Turn 14
	# Player 0
	# Lands on 14 (rent 12)
	playerInterfaces[0].Reset()
	propertyGame.DoTurn([(1,4)])
	if propertyGame.playerPositions[0] != 14:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 1
	# Lands on 20
	playerInterfaces[1].Reset()
	propertyGame.DoTurn([(1,4)])
	propertyGame.EndPlayerTurn()

	# Player 2
	# Rolls to get out of jail and fails (human error here: they are not in jail)
	propertyGame.GoDirectlyToJail(2)
	playerInterfaces[2].Reset()
	propertyGame.DoTurn([(1,3)])
	if propertyGame.playerPositions[2] != None:
		raise RuntimeError()
	if propertyGame.playerTimeInJail[2] != 1:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Turn 15
	# Player 0
	# Lands on 22 (GoToJailCard chance)
	playerInterfaces[0].Reset()
	propertyGame.DoTurn([(5,3)])
	if propertyGame.playerPositions[0] != None:
		raise RuntimeError()
	if propertyGame.playerTimeInJail[0] != 0:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 1
	# Lands on 30 Gotojail
	playerInterfaces[1].Reset()
	propertyGame.DoTurn([(5,5)])
	if propertyGame.playerPositions[1] != None:
		raise RuntimeError()
	if propertyGame.playerTimeInJail[1] != 0:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Omit section that they keep trying for double roll
	# Player 2
	# Rolls to get out of jail and fails
	playerInterfaces[2].Reset()
	propertyGame.DoTurn([(1,3)])
	if propertyGame.playerPositions[2] != None:
		raise RuntimeError()

	propertyGame.EndPlayerTurn()

	# Turn 16
	# Player 0
	# Rolls a double and lands on 18 (rent)
	playerInterfaces[0].Reset()
	propertyGame.DoTurn([(4,4)])
	if propertyGame.playerPositions[0] != 18:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 1
	# Rolls to get out of jail and fails
	playerInterfaces[1].Reset()
	propertyGame.DoTurn([(1,3)])
	if propertyGame.playerPositions[1] != None:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 2
	# Rolls a double and lands on 14 (owned)
	playerInterfaces[2].Reset()
	propertyGame.DoTurn([(2,2)])
	if propertyGame.playerPositions[2] != 14:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Turn 16
	# Player 0
	# Lands on 23 (buys?)
	playerInterfaces[0].Reset()
	playerInterfaces[0].optionToBuy = 1
	propertyGame.DoTurn([(1,4)])
	if propertyGame.playerPositions[0] != 23:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 1 (turn happens off screen)
	# Rolls to get out of jail and fails
	playerInterfaces[1].Reset()
	propertyGame.DoTurn([(1,4)])
	if propertyGame.playerPositions[1] != None:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 2 (turn happens off screen)
	# Lands on 19 (rent?)
	playerInterfaces[2].Reset()
	propertyGame.DoTurn([(1,4)])
	if propertyGame.playerPositions[2] != 19:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Turn 17
	# Player 0
	# Lands on 33 (community StreetRepairs), card has no effect
	propertyGame.playerTurn = 0
	playerInterfaces[0].Reset()
	propertyGame.DoTurn([(6,4)])
	if propertyGame.playerPositions[0] != 33:
		raise RuntimeError()
	if propertyGame.playerMoney[0] != 213:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 1
	# Rolls to get out of jail and fails (should move out on 3rd attempt)
	playerInterfaces[1].Reset()
	propertyGame.DoTurn([(1,4)])
	if propertyGame.playerPositions[1] != 15:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 2
	# Lands on 29 (owned) (human error: they count 11 but only move 10 spaces)
	playerInterfaces[2].Reset()
	propertyGame.DoTurn([(6,4)])
	if propertyGame.playerPositions[2] != 29:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Turn 18
	# Player 0
	# Passes go, Lands on 1 (rent)
	playerInterfaces[0].Reset()
	propertyGame.DoTurn([(5,3)])
	if propertyGame.playerPositions[0] != 1:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 1
	# Rolls to get out of jail (error: not actually in jail)
	propertyGame.GoDirectlyToJail(1)
	playerInterfaces[1].Reset()
	propertyGame.DoTurn([(1,4)])
	if propertyGame.playerPositions[1] != None:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 2
	# Lands on 36 (chance AdvanceToGo)
	playerInterfaces[2].Reset()
	propertyGame.DoTurn([(3,4)])
	if propertyGame.playerPositions[2] != 0:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Turn 19
	# Player 0
	# Lands on just visiting
	playerInterfaces[0].Reset()
	propertyGame.DoTurn([(6,3)])
	if propertyGame.playerPositions[0] != 10:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 1
	# Rolls to get out of jail and fails
	playerInterfaces[1].Reset()
	propertyGame.DoTurn([(1,4)])
	if propertyGame.playerPositions[1] != None:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 2 (timestamp 32:35)
	# Lands on 9 (rent)
	playerInterfaces[2].Reset()
	propertyGame.DoTurn([(4,5)])
	if propertyGame.playerPositions[2] != 9:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	

def CheckAdvanceToGo():

	# Check advance to go awards correct money
	playerInterfaces = [TestInterface(0), TestInterface(1), TestInterface(2)]

	globalInterface = GlobalInterface()

	propertyGame = PropertyGame(globalInterface, playerInterfaces)
	propertyGame.playerTurn = 0

	SetCardPosition(propertyGame.chanceCards, "AdvanceToGo", 0)

	propertyGame.DoTurn([(2,5)])
	assert propertyGame.playerMoney[0] == 1700

	# Check passing go multiple times in a turn (four times)
	# Inspired by https://www.quora.com/How-many-times-can-a-player-pass-Go-and-collect-200-during-his-her-turn-in-the-game-of-Monopoly
	playerInterfaces = [TestInterface(0), TestInterface(1), TestInterface(2)]
	playerInterfaces[0].optionToBuy = 1

	globalInterface = GlobalInterface()

	propertyGame = PropertyGame(globalInterface, playerInterfaces)
	propertyGame.playerTurn = 0
	propertyGame.playerPositions[0] = 39

	SetCardPosition(propertyGame.chanceCards, "TripBoardwalk", 0)
	SetCardPosition(propertyGame.chanceCards, "AdvanceToGo", 1)
	SetCardPosition(propertyGame.chanceCards, "TripReadingTrainStation", 2)

	propertyGame.DoTurn([(4,4), (4,4), (1,6)])
	assert propertyGame.playerMoney[0] == 1500 + 4*200 - 400 - 200

def Test():

	CheckBuildingCode()
	CheckRemoveBuildings()
	CheckNormalGameplay()
	CheckAdvanceToGo()

if __name__=="__main__":
	Test()

