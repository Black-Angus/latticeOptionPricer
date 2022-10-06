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
        # créer un attribut qui contient la valeur exp(r*dt)
    market:Market
    steps_number:int
    alpha:float
    time_delta:float
    root:Node
    multiplicator:float
    option:Option

    def variance(self, node):
        return (node.stock_price**2)*exp(2*self.market.interest_rate*self.time_delta)*(exp((self.market.volatility**2)*self.time_delta)-1)
    
    def build_next_trunk(self, node):
        # node creation
        node.next_mid = Node()

        # previous assignation
        node.next_mid.previous = node

        # links
        node.next_up = Node()
        node.next_mid.above = node.next_up
        node.next_up.below = node.next_mid
        node.next_down = Node()
        node.next_mid.below = node.next_down
        node.next_down.above = node.next_mid
        # stock price computation
        node.next_mid.stock_price = node.stock_price * exp(self.market.interest_rate * self.time_delta)
        node.next_up.stock_price = node.next_mid.stock_price*self.alpha
        node.next_down.stock_price = node.next_mid.stock_price/self.alpha
        print(f"Trunk built {node.next_mid.stock_price}")
        return
    
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

    def find_closest_node(self, node, node_price):
        node_up = node
        closest_node = node
        min_delta = node_price
        node_down = node
        while (node_up != None):
            if (abs(node_up.stock_price - node_price) < min_delta):
                closest_node = node_up
            node_up = node_up.above
        while (node_down != None):
            if (abs(node_down.stock_price - node_price) < min_delta):
                closest_node = node_down
            node_down = node_down.below
        return closest_node

    def build_above(self, node):
        if node == None:
            print("Building up done")
            return
        
        node.next_mid = self.find_closest_node(node.below.next_mid, node.stock_price)
        if (node.next_mid.above == None): # isoler dans une méthode
            node.next_mid.above = Node()
            node.next_mid.above.below = node.next_mid
            node.next_mid.above.stock_price = node.next_mid.stock_price * self.alpha
        
        if (node.next_mid.below == None):
            node.next_mid.below = Node()
            node.next_mid.below.above = node.next_mid
            node.next_mid.below.stock_price = node.next_mid.stock_price / self.alpha
        node.next_up = node.next_mid.above
        node.next_down = node.next_mid.below

        #print(f"Building up {node.above.stock_price}")
        
        self.build_above(node.above)

        self.compute_probas(node)

        return

    def build_below(self, node):
        if node == None:
            print("Building down done")
            return
        
        node.next_mid = self.find_closest_node(node.above.next_mid, node.stock_price)
        if (node.next_mid.above == None): # isoler dans une méthode
            node.next_mid.above = Node()
            node.next_mid.above.below = node.next_mid
            node.next_mid.above.stock_price = node.next_mid.stock_price * self.alpha
        
        if (node.next_mid.below == None):
            node.next_mid.below = Node()
            node.next_mid.below.above = node.next_mid
            node.next_mid.below.stock_price = node.next_mid.stock_price / self.alpha
        node.next_up = node.next_mid.above
        node.next_down = node.next_mid.below
        #print(f"Building down {node.below.stock_price}")

        self.build_below(node.below)

        self.compute_probas(node)
        
        return 

    def build(self, node, steps_left):
        if steps_left == 0:
            return
        
        self.build_next_trunk(node)
        self.compute_probas(node)
        self.build_above(node.above)
        self.build_below(node.below)
        #self.compute_probas(node)
        return self.build(node.next_mid, steps_left-1)
    
pricing_date = datetime(2022,9,29)
mat_date = datetime(2023,2,23)
stock_price = 100
interest_rate = 0.02
vol = 0.2
nb_steps = 2
dividend_date = datetime(2023,1,25)
dividend = 2



option = Option(mat_date, pricing_date, Option_Type.European, 120, True)
market = Market(interest_rate, vol, dividend, dividend_date, stock_price)
tree = Tree(2, market, option)
tree.build(tree.root, tree.steps_number)
