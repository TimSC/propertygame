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
	if propertyGame.playerMoney[1] != 1272: # Human mistake in video here!
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
	playerInterfaces[1].Reset()
	propertyGame.DoTurn([(1,1), (2,3)])
	if propertyGame.playerPositions[1] != 5:
		raise RuntimeError()
	if propertyGame.playerMoney[1] != 1203:
		raise RuntimeError()
	propertyGame.EndPlayerTurn()


def Test():

	CheckBuildingCode()
	CheckRemoveBuildings()
	CheckNormalGameplay()

if __name__=="__main__":
	Test()

