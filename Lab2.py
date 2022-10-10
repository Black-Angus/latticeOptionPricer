from datetime import datetime, timedelta
from enum import Enum
from math import exp, sqrt

class Node:
    def __init__(self, stock_price:float) :
        self.stock_price = stock_price
        self.proba_down = 0
        self.proba_up = 0
        self.proba_mid = 0
        self.payoff = 0
        self.proba_node = 0

    stock_price:float
    proba_up:float
    proba_mid:float
    proba_down:float
    proba_node:float
    payoff:float
    next_up = None
    next_mid = None
    next_down = None
    above = None
    below = None

class Trunk_node(Node):
    def __init__(self, stock_price:float):
        super().__init__(stock_price)
    
    previous = None

class Market:
    def __init__(self, interest_rate:float, volatility:float, dividend:float, dividend_date:datetime, initial_stock_price:float):
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
    def __init__(self, maturity_date:datetime, pricing_date:datetime, option_type:Option_Type, strike_price:float, is_call:bool) :
        self.is_call = is_call
        self.maturity_date = maturity_date
        self.pricing_date = pricing_date
        self.option_type = option_type
        self.strike_price = strike_price

    maturity_date:datetime
    pricing_date:datetime
    option_type:Option_Type
    strike_price:float
    is_call:bool
    price:float

class Tree:
    def __init__(self, steps_number:int, market:Market, option:Option):
        self.multiplicator = sqrt(3)
        self.steps_number = steps_number
        self.option = option
        self.time_delta = (option.maturity_date - option.pricing_date).days / (self.steps_number * 365)
        self.market = market
        self.discount_factor = exp((market.interest_rate * self.time_delta))
        self.root = Trunk_node(self.market.initial_stock_price)
        self.root.proba_node = 1
        self.alpha = exp((market.interest_rate * self.time_delta) + (market.volatility * self.multiplicator * sqrt(self.time_delta)))
    market:Market
    steps_number:int
    alpha:float
    time_delta:float
    root:Node
    multiplicator:float
    option:Option
    discount_factor:float

    def variance(self, node:Node):
        return (node.stock_price**2)*(exp((self.market.volatility**2)*self.time_delta)-1)*(self.discount_factor**2)
    
    def compute_transition_probas(self, node:Node):
        variance = self.variance(node)
        node.proba_down = (((node.next_mid.stock_price)**(-2)) * variance) / ((1-self.alpha) * (self.alpha **(-2) - 1))  # à modifier pour ajouter les dividendes
        #node.proba_down = (((node.next_mid.stock_price)**(-2)) * (variance + node.next_mid.stock_price**2) - 1 - ((self.alpha+1) * ((node.next_mid.stock_price**(-1))*node.next_mid.stock_price-1))) / ((1-self.alpha) * (self.alpha **(-2) - 1))  # à modifier pour ajouter les dividendes
        node.proba_up = (node.next_mid.stock_price **(-1) * node.next_mid.stock_price - 1 - (self.alpha**(-1) - 1)*node.proba_down) / (self.alpha - 1)
        node.proba_mid = 1 - node.proba_down - node.proba_up

        if node.proba_down < 0 or node.proba_mid < 0 or node.proba_up < 0:
            raise ValueError(f"Negative probability found for node {node.stock_price}")

        # print(f"For node {node.stock_price}")
        # print(f"Variance: {variance}")
        # print(f"Proba up {node.proba_up}")
        # print(f"Proba mid {node.proba_mid}")
        # print(f"Proba down {node.proba_down}")
        return
    
    def find_closest_node(self, node:Node, node_price:Node):
        node_up = node
        node_down = node
        closest_node_up = node
        closest_node_down = node
        min_delta_up = node_price
        min_delta_down = node_price
        while (node_up != None and node_up.stock_price < 1.2*node.stock_price * self.alpha):
            if (abs(node_up.stock_price - node_price) < min_delta_up):
                closest_node_up = node_up
                min_delta_up = abs(node_up.stock_price - node_price)
            node_up = node_up.above
        while (node_down != None and node_down.stock_price > 0.8*node.stock_price / self.alpha):
            if (abs(node_down.stock_price - node_price) < min_delta_down):
                closest_node_down = node_down
                min_delta_down = abs(node_down.stock_price - node_price)
            node_down = node_down.below

        if(min_delta_down > min_delta_up):
            return closest_node_up
        else:
            return closest_node_down        
    
    def build_next_trunk(self, node:Node):
        # node creation
        node.next_mid = Trunk_node(node.stock_price * self.discount_factor)
        node.payoff = self.european_payoff(node)

        # previous assignation
        node.next_mid.previous = node

        # links
        node.next_up = Node(node.next_mid.stock_price*self.alpha)
        node.next_up.payoff = self.european_payoff(node.next_up)
        node.next_mid.above = node.next_up
        node.next_up.below = node.next_mid
        node.next_down = Node(node.next_mid.stock_price/self.alpha)
        node.next_down.payoff = self.european_payoff(node.next_down)
        node.next_mid.below = node.next_down
        node.next_down.above = node.next_mid
        #print(f"Trunk built {node.next_mid.stock_price}")
        return

    def european_payoff(self, node:Node):
        if self.option.is_call:
            return max(0, node.stock_price - self.option.strike_price)
        else:
            return max(0, self.option.strike_price - node.stock_price)

    def link_and_build(self, node:Node, start_node:Node):
        node.next_mid = self.find_closest_node(start_node, node.stock_price)
        if (node.next_mid.above == None):
            node.next_mid.above = Node(node.next_mid.stock_price * self.alpha)
            node.next_mid.above.payoff = self.european_payoff(node.next_mid.above)
            node.next_mid.above.below = node.next_mid
        
        if (node.next_mid.below == None):
            node.next_mid.below = Node(node.next_mid.stock_price / self.alpha)
            node.next_mid.below.payoff = self.european_payoff(node.next_mid.below)
            node.next_mid.below.above = node.next_mid
        node.next_up = node.next_mid.above
        node.next_down = node.next_mid.below

    def build_above(self, node:Node):
        if node == None:
            #print("Building up done")
            return
        
        self.link_and_build(node, node.below.next_mid)

        self.compute_transition_probas(node)

        self.compute_probas(node)

        self.build_above(node.above)

        return

    def build_below(self, node:Node):
        if node == None:
            #print("Building down done")
            return
        
        self.link_and_build(node, node.above.next_mid)

        self.compute_transition_probas(node)

        self.compute_probas(node)

        self.build_below(node.below)
        
        return 

    def build(self, node:Node, steps_left:int):
        if steps_left == 0:
            return
        
        self.build_next_trunk(node)
        self.compute_transition_probas(node)
        self.compute_probas(node)
        self.build_above(node.above)
        self.build_below(node.below)
        return self.build(node.next_mid, steps_left-1)

    def compute_probas(self, node):
        node.next_up.proba_node += node.proba_node*node.proba_up
        node.next_mid.proba_node += node.proba_node*node.proba_mid
        node.next_down.proba_node += node.proba_node*node.proba_down
    
    def price_european(self):
        node = self.root
        while(node.next_mid != None):
            node = node.next_mid
        
        node_down = node.below
        sum = 0
        while(node != None):
            sum += node.payoff * node.proba_node
            node = node.above
        while(node_down != None):
            sum += node_down.payoff * node_down.proba_node
            node_down = node_down.below
        return sum

    def price(self, node:Node):
        if self.option.option_type == Option_Type.European:
            return self.price_european()
        else:
            if node.next_mid == None:
                return node.payoff
            else:
                return self.price(node.next_up) * node.proba_up * self.discount_factor + self.price(node.next_mid) * node.proba_mid * self.discount_factor + self.price(node.next_down) * node.proba_down * self.discount_factor
    
    

pricing_date = datetime(2022,9,29)
mat_date = datetime(2023,9,29)
stock_price = 100
interest_rate = 0.03
vol = 0.25
nb_steps = 200
dividend_date = datetime(2023,5,15)
dividend = 2



call = Option(mat_date, pricing_date, Option_Type.European, 120, True)
put = Option(mat_date, pricing_date, Option_Type.European, 110, False)
market = Market(interest_rate, vol, dividend, dividend_date, stock_price)
tree = Tree(nb_steps, market, put)
tree.build(tree.root, tree.steps_number)
print(tree.price(tree.root))