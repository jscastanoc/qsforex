__author__ = 'jscastanoc'
import copy
from collections import deque

import numpy as np

class BollingerBands(object):
    """
    Basic Bollinger Bands strategy.
    It computes buy and sell signals depending on whether the value of a moving average
    is below or above the corresponding moving standard deviation
    """
    def __init__(self, pairs, events, win_size=30):
        """
        :param pairs: list of strings containing the currency pairs to consider
        :param events:
        :param win_size: integer. number of samples with which the moving average
            and moving standard deviation are computed
        :return:
            --
        """
        self.pairs = pairs
        self.pairs_dict = self.create_pairs_dict()
        self.events = events
        self.win_size = win_size

    def create_pairs_dict(self):
        """
        :return: a dictionary containing the current state of the strategy
        """
        attr_dict = {
            "ticks": 0,
            "invested": False,
            "price_buffer":deque([]),
        }
        pairs_dict = {}
        for p in self.pairs:
            pairs_dict[p] = copy.deepcopy(attr_dict)
        return pairs_dict

    def calculate_signals(self, event):
        if event.type == 'TICK':
            pair = event.instrument # to which currency pair corresponds the event
            price = event.bid
            pd = self.pairs_dict[pair]

            pd["price_buffer"].append(price)

            if pd["ticks"] >= self.win_size:
                mvg_avg = np.mean(pd["price_buffer"])
                mvg_std = np.std(pd["price_buffer"])

                upper_bound = (mvg_avg+self.std_factor*mvg_std)
                lower_bound = (mvg_avg-self.std_factor*mvg_std)
                if price > upper_bound and pd["invested"]:
                    signal = SignalEvent(pair, "market", "sell", event.time)
                    self.events.put(signal)
                    pd["invested"] = False
                if price < lower_bound and not pd["invested"]:
                    signal = SignalEvent(pair, "market", "buy", event.time )
                    self.event.put(signal)
                    pd["invested"] = True

                pd["price_buffer"].popleft()
                pd["ticks"] +=1

