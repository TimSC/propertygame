import random
from propertygame import PropertyGame, GlobalInterface

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


def SetCardPosition(deck, cardName, position):
	
	ind = None
	for i, card in enumerate(deck):
		if card['name'] == cardName:
			ind = i
			break

	card = deck.pop(ind)
	deck.insert(position, card)

def Test():

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

if __name__=="__main__":
	Test()

