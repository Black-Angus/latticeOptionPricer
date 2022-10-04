from datetime import datetime, timedelta
from enum import Enum
from math import exp, sqrt

class Node:
    def __init__(self) :
        self.stock_price = 0
        self.proba_down = 0
        self.proba_up = 0
        self.proba_mid = 0

    stock_price:float
    proba_up:float
    proba_mid:float
    proba_down:float
    next_up = None
    next_mid = None
    next_down = None
    previous = None
    above = None
    below = None

class Market:
    def __init__(self, interest_rate, volatility, dividend, dividend_date, initial_stock_price):
        self.dividend = dividend
        self.dividend_date = dividend_date
        self.initial_stock_price = initial_stock_price
        self.volatility = volatility
        self.interest_rate = interest_rate

    interest_rate:float
    volatility:float
    dividend:float
    dividend_date:timedelta
    initial_stock_price:float

class Option_Type(Enum):
    American = 1
    European = 2

class Option:
    def __init__(self, maturity_date, pricing_date, option_type, strike, is_call) :
        self.is_call = is_call
        self.maturity_date = maturity_date
        self.pricing_date = pricing_date
        self.option_type = option_type
        self.strike = strike

    maturity_date:datetime
    pricing_date:datetime
    option_type:Option_Type
    strike:float
    is_call:bool
    price:float

class Tree:
    def __init__(self, steps_number, market, option):
        self.multiplicator = sqrt(3)
        self.steps_number = steps_number
        self.option = option
        self.time_delta = (option.maturity_date - option.pricing_date).days / (self.steps_number * 365)
        self.market = market
        self.root = Node()
        self.root.stock_price = self.market.initial_stock_price
        self.alpha = exp((market.interest_rate * self.time_delta) + (market.volatility * self.multiplicator * sqrt(self.time_delta)))

    market:Market
    steps_number:int
    alpha:float
    time_delta:float
    root:Node
    multiplicator:float
    option:Option

    def variance(self, node):
        return (node.stock_price**2)*exp(2*self.market.interest_rate*self.time_delta)*(exp((self.market.volatility**2)*self.time_delta)-1)
    
    def compute_probas(self, node):
        variance = self.variance(node)
        node.proba_down = (((node.next_mid.stock_price)**(-2)) * (variance + node.next_mid.stock_price**2) - 1 - ((self.alpha+1) * ((node.next_mid.stock_price**(-1))*node.next_mid.stock_price-1))) / ((1-self.alpha) * (self.alpha **(-2) - 1))  # à modifier pour ajouter les dividendes
        node.proba_up = (node.next_mid.stock_price **(-1) * node.next_mid.stock_price - 1 - (self.alpha**(-1) - 1)*node.proba_down) / (self.alpha - 1)
        node.proba_mid = 1 - node.proba_down - node.proba_up

        print(f"For node {node.stock_price}")
        print(f"Proba up {node.proba_up}")
        print(f"Proba mid {node.proba_mid}")
        print(f"Proba down {node.proba_down}")
        return

    def build_next(self, node):
        # node creation
        node.next_mid = Node()

        # previous assignation
        node.next_mid.previous = node

        # links if the node is on top or bottom of the tree
        if node.above == None :
            node.next_up = Node()
            node.next_up.stock_price = node.stock_price * self.alpha # WIP
            node.next_up.below = node.next_mid
            node.next_mid.above = node.next_up
            # calcul prix stock next_up

        if node.below == None :
            node.next_down = Node()
            node.next_down = node.stock_price * self.alpha
            node.next_down.above = node.next_mid
            node.next_mid.below = node.next_down
            # calcul prix stock next_down

        # stock price computation
        node.next_mid.stock_price = node.stock_price * exp(self.market.interest_rate * self.time_delta)
        return
    
    def build_above(self, node):
        if node.previous == None:
            print("Building up done")
            return
        
        node.above = Node()
        node.above.below = node
        node.above.previous = node.previous.above
        node.previous.next_up = node.above
        if node.previous.above != None:
            node.previous.above.next_mid = node.above
            if node.previous.above.above != None:
                node.previous.above.above.next_down = node.above
        node.above.stock_price = node.stock_price*self.alpha
        print(f"Building up {node.above.stock_price}")
        
        self.build_above(node.above)

        self.compute_probas(node.previous)

        return

    def build_below(self, node):
        if node.previous == None:
            print("Building down done")
            return
        
        node.below = Node()
        node.below.above = node
        node.below.previous = node.previous.below
        node.previous.next_down = node.below
        if node.previous.below != None:
            node.previous.below.next_mid = node.below
            if node.previous.below.below != None:
                node.previous.below.below.next_up = node.below
        node.below.stock_price = node.stock_price/self.alpha
        print(f"Building down {node.below.stock_price}")

        self.build_below(node.below)

        self.compute_probas(node.previous)
        
        return 

    def build(self, node, steps_left):
        if steps_left == 0:
            return
        
        self.build_next(node)
        self.build_above(node.next_mid)
        self.build_below(node.next_mid)
        #self.compute_probas(node)
        return self.build(node.next_mid, steps_left-1)
    


option = Option(datetime(2023,2,23), datetime(2022,9,29), Option_Type.European, 120, True)
market = Market(0.03, 0.25, 2, datetime(2023,5,15), 100)
tree = Tree(2, market, option)
tree.build(tree.root, tree.steps_number)
