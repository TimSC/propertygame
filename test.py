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

	# Turn 19
	# Player 0
	# Lands on 15 (rent 200)
	playerInterfaces[0].Reset()
	propertyGame.DoTurn([(3,2)])
	if propertyGame.playerPositions[0] != 15:
		raise RuntimeError()
	if propertyGame.playerMoney[0] != 219:
		raise RuntimeError()
	if propertyGame.playerMoney[1] != 1083:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 1
	# Rolls to get out of jail and fails (released on 3rd turn)
	playerInterfaces[1].Reset()
	propertyGame.DoTurn([(1,4)])
	if propertyGame.playerPositions[1] != 15:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 2
	# Lands on 12 (rent)
	playerInterfaces[2].Reset()
	propertyGame.DoTurn([(1,2)])
	if propertyGame.playerPositions[2] != 12:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Turn 20
	# Player 0
	# Lands on 19 (owned), then 24
	playerInterfaces[0].Reset()
	propertyGame.DoTurn([(2,2), (1,4)])
	if propertyGame.playerPositions[0] != 24:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 1
	# Rolls to get out of jail, fails and pays $50 (humans finally figured out that rule!)
	propertyGame.GoDirectlyToJail(1)
	propertyGame.playerTimeInJail[1] = 2 # Last chance to roll double
	playerInterfaces[1].Reset()
	propertyGame.DoTurn([(5,4)])
	if propertyGame.playerPositions[1] != 19:
		raise RuntimeError()
	if propertyGame.playerMoney[1] != 967:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 2 builds first house (cost 150)
	pm = propertyGame.playerMoney[2]
	propertyGame.SetNumBuildingsInGroup(propertyGame.propertyInGroup[29], 1)
	if propertyGame.playerMoney[2] != pm - 150:
		raise RuntimeError()

	# Player 2
	# Lands on 23 (rent)
	playerInterfaces[2].Reset()
	propertyGame.DoTurn([(5,6)])
	if propertyGame.playerPositions[2] != 23:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Turn 21
	# Player 0
	# Lands on 27 (rent double rate 44)
	pm = propertyGame.playerMoney[0]
	pm2 = propertyGame.playerMoney[2]
	playerInterfaces[0].Reset()
	propertyGame.DoTurn([(1,2)])
	if propertyGame.playerPositions[0] != 27:
		raise RuntimeError()
	if propertyGame.playerMoney[0] != pm - 44:
		raise RuntimeError()
	if propertyGame.playerMoney[2] != pm2 + 44:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 1
	# Lands on 29 (1 house rent)
	pm = propertyGame.playerMoney[1]
	pm2 = propertyGame.playerMoney[2]
	playerInterfaces[1].Reset()
	propertyGame.DoTurn([(6,4)])
	if propertyGame.playerPositions[1] != 29:
		raise RuntimeError()
	if propertyGame.playerMoney[1] != pm - 120:
		raise RuntimeError()
	if propertyGame.playerMoney[2] != pm2 + 120:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Player 2
	# Lands on go to jail (timestamp 37:00)
	playerInterfaces[2].Reset()
	propertyGame.DoTurn([(3,4)])
	if propertyGame.playerPositions[2] != None:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()

	# Skip some routine play
	propertyGame.spaceOwners[6] = 1
	propertyGame.spaceOwners[34] = 1
	# Give get chance out of jail to player 0

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

def SeriousTurn(propertyGame, playerInterfaces, row, player, rolls, expectedPos, moneyChange, optionToBuy=None, auctionBids=None, useJailCard=False):
	# Play one scripted turn. Players are numbered 1-3 as in serious-turns.md.
	playerId = player - 1
	while propertyGame.playerBankrupt[propertyGame.playerTurn]:
		propertyGame.EndPlayerTurn()
	if propertyGame.playerTurn != playerId:
		raise RuntimeError("Row {}: expected player {} to have the turn".format(row, player))

	for pl in playerInterfaces:
		pl.Reset()
	playerInterfaces[playerId].optionToBuy = optionToBuy
	playerInterfaces[playerId].useGetOutOfJailCard = useJailCard
	if auctionBids is not None:
		for bidder, bid in auctionBids.items():
			playerInterfaces[bidder - 1].getAuctionBid = bid

	before = propertyGame.playerMoney[:]
	propertyGame.DoTurn(rolls)

	if propertyGame.playerPositions[playerId] != expectedPos:
		raise RuntimeError("Row {}: player {} ended on {}".format(row, player, propertyGame.playerPositions[playerId]))
	for i in range(propertyGame.numPlayers):
		change = propertyGame.playerMoney[i] - before[i]
		if change != moneyChange.get(i + 1, 0):
			raise RuntimeError("Row {}: player {} money changed by {}".format(row, i + 1, change))

	propertyGame.EndPlayerTurn()

def SeriousTrade(propertyGame, playerInterfaces, row, proposer, recipient, proposerSpaces, recipientSpaces, proposerMoney=0, recipientMoney=0):
	offer = propertyGame.NewTrade(proposer - 1, recipient - 1)
	offer.spaces = [proposerSpaces, recipientSpaces]
	offer.money = [proposerMoney, recipientMoney]
	playerInterfaces[recipient - 1].acceptTrade = True
	if not propertyGame.ProposeTrade(offer):
		raise RuntimeError("Row {}: trade failed {}".format(row, propertyGame.TradeProblems(offer)))
	playerInterfaces[recipient - 1].acceptTrade = False

def SeriousTopUp(propertyGame, row, player, amount):
	# Rule deviation: gives a player cash so they stay in the game (see serious-turns.md)
	propertyGame.globalInterface.Log("Row {}: player {} topped up by {} (rule deviation)".format(row, player, amount))
	propertyGame.playerMoney[player - 1] += amount

def SeriousBuild(propertyGame, row, player, groupId, numBuildings, expectedSpaceId, expectedCost):
	before = propertyGame.playerMoney[player - 1]
	impossible, numAllowed, reasons, planCost = propertyGame.BuildBuildings(player - 1, groupId, numBuildings)
	if impossible:
		raise RuntimeError("Row {}: build failed {}".format(row, reasons))
	if propertyGame.NumHousesOnSpace(expectedSpaceId) < 1:
		raise RuntimeError("Row {}: house not on space {}".format(row, expectedSpaceId))
	if before - propertyGame.playerMoney[player - 1] != expectedCost:
		raise RuntimeError("Row {}: house cost {}".format(row, before - propertyGame.playerMoney[player - 1]))

def CheckSeriousGameplay():

	# Replays "Monopoly, But SERIOUS" (No Rolls Barred), UK board.
	# https://www.youtube.com/watch?v=cDmxXT2o9sE
	# Row numbers and players (1-3) refer to serious-turns.md. Where only a dice total
	# was visible, a non-double pair with that total is used.
	playerInterfaces = [TestInterface(0), TestInterface(1), TestInterface(2)]
	globalInterface = GlobalInterface()
	propertyGame = PropertyGame(globalInterface, playerInterfaces, "property-board-uk.txt")
	propertyGame.playerTurn = 2 # Player 3 rolled highest to start

	for i, cardName in enumerate(["GetOutJailFree", "AdvancePallMall", "AdvanceMayfair", "BuildingLoanMatures",
		"AdvanceTrafalgarSquare", "Chairperson", "GoBack3Spaces", "SpeedingFine"]):
		SetCardPosition(propertyGame.chanceCards, cardName, i)
	for i, cardName in enumerate(["BankError", "IncomeTaxRefund", "AdvanceToGo", "GoToJailCard", "Birthday", "GetOutJailFree"]):
		SetCardPosition(propertyGame.communityCards, cardName, i)

	pg, pi = propertyGame, playerInterfaces

	SeriousTurn(pg, pi, 2, 3, [(1,3)], 4, {3:-200}) # Income Tax
	SeriousTurn(pg, pi, 3, 1, [(1,5)], 6, {1:-100}, optionToBuy=1) # Buys The Angel Islington
	SeriousTurn(pg, pi, 4, 2, [(4,2)], 6, {2:-6, 1:+6}) # Rent on The Angel Islington
	SeriousTurn(pg, pi, 5, 3, [(6,1)], 11, {3:-140}, optionToBuy=1) # Buys Pall Mall
	SeriousTurn(pg, pi, 6, 1, [(6,2)], 14, {1:-160}, optionToBuy=1) # Buys Northumberland Avenue
	SeriousTurn(pg, pi, 7, 2, [(3,4)], 13, {2:-145}, optionToBuy=0, auctionBids={1:0, 2:145, 3:0}) # Whitehall auctioned
	SeriousTurn(pg, pi, 8, 3, [(5,6)], 22, {}) # Chance: get out of jail free
	if len(pg.playerGetOutOfJailCards[2]) != 1:
		raise RuntimeError()
	SeriousTurn(pg, pi, 9, 1, [(5,4)], 23, {1:-220}, optionToBuy=1) # Buys Fleet Street
	SeriousTurn(pg, pi, 10, 2, [(5,3)], 21, {2:-220}, optionToBuy=1) # Buys Strand
	SeriousTurn(pg, pi, 11, 3, [(6,4)], 32, {3:-300}, optionToBuy=1) # Buys Oxford Street
	SeriousTurn(pg, pi, 12, 1, [(6,3)], 32, {1:-26, 3:+26}) # Rent on Oxford Street
	SeriousTurn(pg, pi, 13, 2, [(1,2)], 24, {2:-240}, optionToBuy=1) # Buys Trafalgar Square
	SeriousTurn(pg, pi, 14, 3, [(5,6)], 3, {3:+200-60}, optionToBuy=1) # Passes Go, buys Whitechapel Road
	SeriousTurn(pg, pi, 15, 1, [(1,4)], 37, {1:-350}, optionToBuy=1) # Buys Park Lane

	# Player 2 buys Fleet Street from player 1 for 50 + Whitehall, completing the reds
	SeriousTrade(pg, pi, 16, 2, 1, [13], [23], proposerMoney=50)
	if pg.GetGroupOwner(4) != 1:
		raise RuntimeError()
	SeriousBuild(pg, 17, 2, 4, 1, 24, 150) # One house, on Trafalgar Square

	SeriousTurn(pg, pi, 18, 2, [(5,1)], None, {}) # Go To Jail
	SeriousTurn(pg, pi, 19, 3, [(6,2)], 11, {}) # Own property
	SeriousTurn(pg, pi, 20, 1, [(1,3)], 1, {1:+200-60}, optionToBuy=1) # Passes Go, buys Old Kent Road
	SeriousTurn(pg, pi, 21, 2, [(2,2)], 14, {2:-12, 1:+12}) # Double to leave jail, no second roll
	SeriousTurn(pg, pi, 22, 3, [(1,1), (6,1)], 20, {3:-10, 1:+10}) # Rent on Whitehall, then Free Parking
	SeriousTurn(pg, pi, 23, 1, [(1,2)], 4, {1:-200}) # Income Tax
	SeriousTurn(pg, pi, 24, 2, [(6,4)], 24, {}) # Own property
	SeriousTurn(pg, pi, 25, 3, [(1,1), (6,1)], 18, {3:+200-180}, optionToBuy=1) # Chance to Pall Mall, then buys Marlborough Street
	SeriousTurn(pg, pi, 26, 1, [(1,2)], 39, {1:-400}, optionToBuy=1) # Chance to Mayfair, buys it
	SeriousTurn(pg, pi, 27, 2, [(5,4)], 33, {2:+200}) # Community chest: +200
	SeriousTurn(pg, pi, 28, 3, [(6,3)], 27, {3:-260}, optionToBuy=1) # Buys Coventry Street
	SeriousTurn(pg, pi, 29, 1, [(6,2)], 7, {1:+200+150}) # Passes Go, chance: building loan matures
	SeriousTurn(pg, pi, 30, 2, [(4,2)], 39, {2:-100, 1:+100}) # Double rent on Mayfair (full set)
	SeriousTurn(pg, pi, 31, 3, [(5,2)], 34, {3:-320}, optionToBuy=1) # Buys Bond Street
	SeriousTurn(pg, pi, 32, 1, [(4,1)], 12, {1:-150}, optionToBuy=1) # Buys Electric Company
	SeriousTurn(pg, pi, 33, 2, [(6,4)], 9, {2:+200-120}, optionToBuy=1) # Passes Go, buys Pentonville Road
	SeriousTurn(pg, pi, 34, 3, [(1,3)], 38, {3:-100}) # Super Tax
	# Player 1 proposes a trade that player 3 rejects (no effect)

	SeriousBuild(pg, 36, 1, 7, 1, 39, 200) # One house, on Mayfair
	SeriousTurn(pg, pi, 37, 1, [(6,4)], 24, {1:-100, 2:+100}) # Chance to Trafalgar Square, rent with 1 house
	SeriousBuild(pg, 38, 2, 4, 2, 23, 150) # Second red house, on Fleet Street

	SeriousTurn(pg, pi, 39, 2, [(4,4), (6,4)], 27, {2:+20-22, 3:+22}) # Community chest +20, then rent on Coventry Street
	SeriousTurn(pg, pi, 40, 3, [(6,5)], 9, {3:+200-8, 2:+8}) # Passes Go, rent on Pentonville Road
	SeriousTurn(pg, pi, 41, 1, [(6,3)], 0, {1:+200}) # Community chest: advance to Go
	SeriousTurn(pg, pi, 42, 2, [(6,3)], 36, {2:-100, 1:+50, 3:+50}) # Chance: chairperson pays each player 50
	SeriousTurn(pg, pi, 43, 3, [(3,2)], 14, {3:-12, 1:+12}) # Rent on Northumberland Avenue
	SeriousTurn(pg, pi, 44, 1, [(6,4)], 10, {}) # Just visiting
	SeriousTurn(pg, pi, 45, 2, [(6,2)], 4, {2:+200-200}) # Passes Go, Income Tax
	SeriousTurn(pg, pi, 46, 3, [(4,3)], 21, {3:-36, 2:+36}) # Double rent on Strand (unimproved, full set)
	SeriousTurn(pg, pi, 47, 1, [(4,2)], 16, {3:-193}, optionToBuy=0, auctionBids={1:0, 2:0, 3:193}) # Bow Street auctioned
	SeriousTurn(pg, pi, 48, 2, [(4,2)], 10, {}) # Just visiting
	SeriousTurn(pg, pi, 49, 3, [(4,1)], 26, {3:-260}, optionToBuy=1) # Buys Leicester Square
	SeriousTurn(pg, pi, 50, 1, [(4,2)], 19, {1:-200}, optionToBuy=1) # Chance: back 3 to Vine Street, buys it
	SeriousTurn(pg, pi, 51, 2, [(6,2)], 18, {2:-14, 3:+14}) # Rent on Marlborough Street

	# Player 1 trades Vine Street for player 3's Pall Mall, completing orange and pink
	SeriousTrade(pg, pi, 52, 1, 3, [19], [11])
	if pg.GetGroupOwner(3) != 2 or pg.GetGroupOwner(2) != 0:
		raise RuntimeError()

	if pg.playerMoney != [324, 735, 133]:
		raise RuntimeError()

	noBids = {1:0, 2:0, 3:0}
	SeriousTurn(pg, pi, 53, 3, [(6,2)], 34, {}) # Own property
	SeriousTurn(pg, pi, 54, 1, [(5,1)], 25, {1:-200}, optionToBuy=1) # Buys Fenchurch Street Station
	SeriousTurn(pg, pi, 55, 2, [(5,1)], 24, {}) # Own property
	SeriousTurn(pg, pi, 56, 3, [(5,3)], None, {3:+200}) # Passes Go, community chest: go to jail

	# Two houses on orange. The video puts them on Bow Street and Vine Street, which is legal
	# but not the engine's choice, so move the Marlborough Street house to Bow Street.
	SeriousBuild(pg, 57, 3, 3, 2, 19, 200)
	pg.boardHouses[pg.boardHouses.index(18)] = 16
	pg.boardGroupBuildOrder[3] = [19, 16]

	SeriousTurn(pg, pi, 58, 1, [(5,1)], 31, {}, auctionBids=noBids) # Can't afford Regent Street. Rule deviation: the banker keeps it off the market, so nobody bids
	SeriousTurn(pg, pi, 59, 2, [(2,4)], None, {}) # Go To Jail
	SeriousTurn(pg, pi, 60, 3, [(6,3)], 19, {}, useJailCard=True) # Uses get out of jail free, own property
	SeriousTurn(pg, pi, 61, 1, [(5,1)], 37, {}) # Own property
	SeriousTurn(pg, pi, 62, 2, [(6,6)], 22, {2:-15}) # Double to leave jail, chance: speeding fine
	SeriousTurn(pg, pi, 63, 3, [(6,2)], 27, {}) # Own property
	SeriousTurn(pg, pi, 64, 1, [(5,1)], 3, {1:+200-4, 3:+4}) # Passes Go, rent on Whitechapel Road
	SeriousTurn(pg, pi, 65, 2, [(5,3)], None, {}) # Go To Jail
	SeriousTurn(pg, pi, 66, 3, [(5,3)], 35, {1:-160}, auctionBids={1:160, 2:0, 3:0}) # Can't afford Liverpool Street Station, auctioned
	SeriousTurn(pg, pi, 67, 1, [(4,2)], 9, {1:-8, 2:+8}) # Rent on Pentonville Road, owner is in jail
	SeriousTurn(pg, pi, 68, 2, [(5,6)], None, {}) # Fails to leave jail
	SeriousTurn(pg, pi, 69, 3, [(1,2)], 38, {3:-100}) # Super Tax
	SeriousTurn(pg, pi, 70, 1, [(6,3)], 18, {1:-28, 3:+28}) # Double rent on unimproved Marlborough Street
	SeriousTurn(pg, pi, 71, 2, [(6,4)], None, {}) # Fails to leave jail
	SeriousTurn(pg, pi, 72, 3, [(6,6), (4,2)], 16, {3:+200}) # Passes Go, own property

	# Rule deviation: the video builds Bow 2 / Marlborough 0 / Vine 2, which is uneven.
	# Use the engine's legal placement (Bow 1 / Marlborough 1 / Vine 2), so orange rents differ from the video.
	SeriousBuild(pg, 73, 3, 3, 4, 18, 200)

	SeriousTurn(pg, pi, 74, 1, [(5,3)], 26, {1:-22, 3:+22}) # Rent on Leicester Square

	# Row 75, rule deviation: third failed roll, pays 50 but the video does not move them
	# (the rules would move them 3 to Whitehall and charge 20 rent)
	if pg.playerTurn != 1:
		raise RuntimeError()
	pg.EnsurePlayment(1, 50)
	pg.ReleaseFromJail(1)
	pg.EndPlayerTurn()

	# Water Works: rule deviation, the banker keeps it off the market. Doubles, then rent on Liverpool Street Station.
	SeriousTurn(pg, pi, 76, 3, [(6,6), (6,1)], 35, {3:-50, 1:+50}, optionToBuy=0, auctionBids=noBids)
	SeriousTurn(pg, pi, 77, 1, [(5,4)], 35, {}) # Own property
	SeriousTurn(pg, pi, 78, 2, [(4,2)], 16, {2:-70, 3:+70}) # Bow Street, 1 house (video: 2 houses, 200)
	SeriousTurn(pg, pi, 79, 3, [(6,3)], 4, {3:+200-200}) # Passes Go, Income Tax
	SeriousTurn(pg, pi, 80, 1, [(5,2)], 2, {1:+200+20, 2:-10, 3:-10}) # Passes Go, community chest: street party
	SeriousTurn(pg, pi, 81, 2, [(2,1)], 19, {2:-220, 3:+220}) # Vine Street, 2 houses

	# The video buys four buildings (hotel on Bow Street), which is uneven. Legal placement is
	# Bow 2 / Marlborough 3 / Vine 3. Rule deviation: top up 83, as the model's orange rents were lower.
	SeriousTopUp(pg, 82, 3, 83)
	SeriousBuild(pg, 82, 3, 3, 8, 19, 400)

	pg.playerTurn = 0 # Row 83, rule deviation: player 3 misses a turn

	SeriousTurn(pg, pi, 84, 1, [(3,4)], 9, {1:-8, 2:+8}) # Rent on Pentonville Road
	SeriousTurn(pg, pi, 85, 2, [(3,2)], 24, {}) # Own property
	SeriousBuild(pg, 86, 2, 4, 3, 21, 150) # Third red house, on Strand
	SeriousTurn(pg, pi, 87, 3, [(4,2)], 10, {}) # Just visiting

	# Vine Street, 3 houses: 600 (video: 2 houses, 220). Rule deviation: top up 236 so player 1 can pay.
	SeriousTopUp(pg, 88, 1, 236)
	SeriousTurn(pg, pi, 88, 1, [(6,4)], 19, {1:-600, 3:+600})

	# Rule deviation: the banker's hotels on Regent Street eliminate player 2. Here it is still unowned,
	# so nobody bids, then player 2 goes bankrupt to the bank and their property goes unsold.
	SeriousTurn(pg, pi, 89, 2, [(3,4)], 31, {}, auctionBids=noBids)
	for pl in pi:
		pl.getAuctionBid = 0
	pg.PlayerGoesBankrupt(1, 'bank')

	SeriousTurn(pg, pi, 90, 3, [(6,1)], 17, {}) # Community chest: get out of jail free
	if len(pg.playerGetOutOfJailCards[2]) != 1:
		raise RuntimeError()
	SeriousBuild(pg, 91, 3, 3, 10, 19, 200) # Legal placement Bow 3 / Marlborough 3 / Vine 4 (video: 4 on Vine)

	SeriousTopUp(pg, 92, 1, 22) # Rule deviation: player 1 was emptied by the higher Vine Street rent
	SeriousTurn(pg, pi, 92, 1, [(5,3)], 27, {1:-22, 3:+22}) # Rent on Coventry Street

	if pg.playerMoney != [0, 0, 422] or pg.playerBankrupt != [False, True, False]:
		raise RuntimeError()

def Test():

	CheckBuildingCode()
	CheckRemoveBuildings()
	CheckNormalGameplay()
	CheckAdvanceToGo()
	CheckSeriousGameplay()

if __name__=="__main__":
	Test()

