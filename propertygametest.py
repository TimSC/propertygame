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

	

if __name__=="__main__":
	Test()

