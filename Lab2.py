from datetime import datetime, timedelta
from enum import Enum
from math import exp, sqrt
from time import perf_counter

# TODO
# DIVIDENDES

class Node:
    counter = 0
    def __init__(self, stock_price:float) :
        self.stock_price = stock_price
        self.proba_down = 0
        self.proba_up = 0
        self.proba_mid = 0
        self.payoff = 0
        self.proba_node = 0
        Node.counter += 1

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
    Call = 1
    Put = 2

class Contract_Type(Enum):
    American = 1
    European = 2

class Option:
    def __init__(self, maturity_date:datetime, pricing_date:datetime, contract_type:Contract_Type, strike_price:float, option_type:Option_Type) :
        self.option_type = option_type
        self.maturity_date = maturity_date
        self.pricing_date = pricing_date
        self.contract_type = contract_type
        self.strike_price = strike_price

    maturity_date:datetime
    pricing_date:datetime
    option_type:Option_Type
    strike_price:float
    is_call:bool
    price:float

class Tree:
    def __init__(self, steps_number:int, market:Market, option:Option, pruning:bool):
        self.multiplicator = sqrt(3)
        self.steps_number = steps_number
        self.option = option
        self.time_delta = (option.maturity_date - option.pricing_date).days / ((self.steps_number)*365)
        self.market = market
        self.discount_factor = exp((market.interest_rate * self.time_delta))
        self.root = Trunk_node(self.market.initial_stock_price)
        self.root.proba_node = 1
        self.alpha = exp((market.interest_rate * self.time_delta) + (market.volatility * self.multiplicator * sqrt(self.time_delta)))
        self.counter = 0
        self.proba_threshold = 0.0000001
        self.pruning = pruning
    market:Market
    steps_number:int
    alpha:float
    time_delta:float
    root:Trunk_node
    multiplicator:float
    option:Option
    discount_factor:float
    counter:int
    proba_threshold:float
    pruning:bool

    def Variance(self, node:Node):
        return (exp((self.market.volatility**2)*self.time_delta)-1)*((self.discount_factor*node.stock_price)**2)
    
    def Compute_transition_probas(self, node:Node):
        variance = self.Variance(node)
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
    
    def Find_closest_node(self, node:Node, node_price:Node):
        node_up = node
        node_down = node
        closest_node_up = node
        closest_node_down = node
        min_delta_up = node_price
        min_delta_down = node_price
        while (node_up != None and node_up.stock_price < (node_price * (1 + self.alpha))/2):
            if (abs(node_up.stock_price - node_price) < min_delta_up):
                closest_node_up = node_up
                min_delta_up = abs(node_up.stock_price - node_price)
            node_up = node_up.above
        while (node_down != None and node_down.stock_price > (node_price * (1 + (1 / self.alpha)))/2):
            if (abs(node_down.stock_price - node_price) < min_delta_down):
                closest_node_down = node_down
                min_delta_down = abs(node_down.stock_price - node_price)
            node_down = node_down.below

        if(min_delta_down > min_delta_up):
            return closest_node_up
        else:
            return closest_node_down        
    
    def Build_next_trunk(self, node:Node):
        # node creation
        node.next_mid = Trunk_node(node.stock_price * self.discount_factor)
        node.payoff = self.Exercice_payoff(node)

        # previous assignation
        node.next_mid.previous = node

        # links
        node.next_up = Node(node.next_mid.stock_price*self.alpha)
        node.next_up.payoff = self.Exercice_payoff(node.next_up)
        node.next_mid.above = node.next_up
        node.next_up.below = node.next_mid
        node.next_down = Node(node.next_mid.stock_price/self.alpha)
        node.next_down.payoff = self.Exercice_payoff(node.next_down)
        node.next_mid.below = node.next_down
        node.next_down.above = node.next_mid
        self.counter += 2
        return

    def Exercice_payoff(self, node:Node):
        if self.option.option_type == Option_Type.Call:
            return max(0, node.stock_price - self.option.strike_price)
        else:
            return max(0, self.option.strike_price - node.stock_price)

    def Link_and_build(self, node:Node, start_node:Node):
        node.next_mid = self.Find_closest_node(start_node, node.stock_price)
        if (node.next_mid.above == None):
            node.next_mid.above = Node(node.next_mid.stock_price * self.alpha)
            node.next_mid.above.payoff = self.Exercice_payoff(node.next_mid.above)
            node.next_mid.above.below = node.next_mid
        
        if (node.next_mid.below == None):
            node.next_mid.below = Node(node.next_mid.stock_price / self.alpha)
            node.next_mid.below.payoff = self.Exercice_payoff(node.next_mid.below)
            node.next_mid.below.above = node.next_mid
        node.next_up = node.next_mid.above
        node.next_down = node.next_mid.below

    def Build_above(self, node:Node):
        while (node != None):
            self.Link_and_build(node, node.below.next_mid)
            self.Compute_transition_probas(node)
            self.Compute_probas(node)
            if (self.pruning):
                if (node.proba_node < self.proba_threshold):
                    node = None
                    return
            node = node.above

        return

    def Build_below(self, node:Node):
        while (node != None):
            self.Link_and_build(node, node.above.next_mid)
            self.Compute_transition_probas(node)
            self.Compute_probas(node)
            if (self.pruning):
                if (node.proba_node < self.proba_threshold):
                    node = None
                    return
            node = node.below

        return 

    def Build(self, node:Node, steps_left:int):
        #dividend_step = (self.market.dividend_date - self.option.pricing_date).days
        while(steps_left != 0):
            self.Build_next_trunk(node)
            self.Compute_transition_probas(node)
            self.Compute_probas(node)
            self.Build_above(node.above)
            self.Build_below(node.below)
            node = node.next_mid
            steps_left = steps_left-1

    def Compute_probas(self, node:Node):
        node.next_up.proba_node += node.proba_node*node.proba_up
        node.next_mid.proba_node += node.proba_node*node.proba_mid
        node.next_down.proba_node += node.proba_node*node.proba_down
    
    def Price_european(self):
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
        return sum/self.discount_factor**self.steps_number
    
    def Price_american(self):
        try:
            node = self.root
            while(node.next_mid != None): # going to the last node on the trunk
                node = node.next_mid
            
            while (node.previous != None):
                # iterate over every day
                node = node.previous
                node_up = node
                node_down = node.below
                while (node_up != None):
                    # iterate above
                    exercice_later = (node_up.proba_up * node_up.next_up.payoff) + (node_up.proba_mid * node_up.next_mid.payoff) + (node_up.proba_down * node_up.next_down.payoff)
                    node_up.payoff = max(self.Exercice_payoff(node_up), exercice_later / self.discount_factor)
                    node_up = node_up.above

                while (node_down != None):
                    # iterate below
                    exercice_later = (node_down.proba_up * node_down.next_up.payoff) + (node_down.proba_mid * node_down.next_mid.payoff) + (node_down.proba_down * node_down.next_down.payoff)
                    node_down.payoff = max(self.Exercice_payoff(node_down), exercice_later / self.discount_factor)
                    node_down = node_down.below

            return node.payoff
        except:
            return
    def Price(self):
        if self.option.contract_type == Contract_Type.European:
            return self.Price_european()
        else:
            return self.Price_american()
    
    

pricing_date = datetime(2021,9,1)
mat_date = datetime(2022,9,1)
stock_price = 100
interest_rate = -0.02
vol = 0.3
nb_steps = 100
dividend_date = datetime(2023,5,15)
dividend = 0
pruning = False

toc = perf_counter()
call = Option(mat_date, pricing_date, Contract_Type.American, 99, Option_Type.Call)
put = Option(mat_date, pricing_date, Contract_Type.European, 110, Option_Type.Put)
market = Market(interest_rate, vol, dividend, dividend_date, stock_price)
tree = Tree(nb_steps, market, call, pruning)
tree.Build(tree.root, tree.steps_number)
print(f"Price : {tree.Price():0.4f}")
tic = perf_counter()
print(f"Nodes : {Node.counter}")
print(f"Time : {tic-toc:0.4f} seconds")