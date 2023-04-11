class Node:

 def __init__(self):
   self.address = 900

 def sell(self):
   print('Selling Price: {}'.format(self.__maxprice))

 def setMaxPrice(self, price):
   self.__maxprice = price

c = Node()