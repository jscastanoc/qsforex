__author__ = 'jscastanoc'
import os
import copy
from collections import deque
import logging

import numpy as np
import pandas as pd

from qsforex.event.event import SignalEvent

class BollingerBands(object):
    """
    Basic Bollinger Bands strategy.
    It computes buy and sell signals depending on whether the value of a moving average
    is below or above the corresponding moving standard deviation
    """
    def __init__(self, pairs, events, win_size=30, std_factor=2, backtest_dir=""):
        """
        :param pairs: list of strings containing the currency pairs to consider
        :param events:
        :param win_size: integer. number of samples with which the moving average
            and moving standard deviation are computed
        :return:
            --
        """
        # set buy/sell signal logger
        self.logger_signals = logging.getLogger(__name__)
        self.logger_signals.setLevel(logging.DEBUG)

        logfile_name = os.path.join(backtest_dir, "loguito.log")
        log_handlerFile = logging.FileHandler(logfile_name)
        log_handlerFile.setLevel(logging.DEBUG)
        self.logger_signals.addHandler(log_handlerFile)

        log_handlerStream = logging.StreamHandler()
        log_handlerStream.setLevel(logging.DEBUG)
        self.logger_signals.addHandler(log_handlerStream)

        # set hyperparameters of the algorithm
        self.pairs = pairs
        self.pairs_dict = self.create_pairs_dict()
        self.events = events
        self.win_size = win_size
        self.std_factor = std_factor

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
            self.logger_signals.debug("Applying bollinger bands in pair %s",p)
        return pairs_dict

    def calculate_signals(self, event):
        """
        compute buy/sell signals for events of type TICK
        :param event: event (queue) containing the formation of the signal
         sent by the backtester when a line of the .csv is read
        :return:n/a
        """
        if event.type == 'TICK':
            """
            TICK events are sent every time for each currency pair and for each
            time sample.
            it also contains the bid/ask value of the pair
            """
            pair = event.instrument
            price = event.bid
            pd = self.pairs_dict[pair]
            pd["price_buffer"].append(price)

            if pd["ticks"] >= self.win_size:
                mvg_avg = np.mean(pd["price_buffer"])
                mvg_std = np.std(pd["price_buffer"])

                upper_bound = (mvg_avg+self.std_factor*mvg_std)
                lower_bound = (mvg_avg-self.std_factor*mvg_std)

                # generate the sell/buy signals according to the bollinger rules
                if price > upper_bound and pd["invested"]:
                    type = "sell"
                    signal = SignalEvent(pair, "market", type, event.time)
                    print(signal)
                    self.events.put(signal)
                    pd["invested"] = False
                    self.logger_signals.info("Pair:%s Type:%s Time:%s",pair
                                             ,type,event.time)
                if price < lower_bound and not pd["invested"]:
                    type = "buy"
                    signal = SignalEvent(pair, "market", type, event.time )
                    self.events.put(signal)
                    pd["invested"] = True
                    self.logger_signals.info("Pair:%s Type:%s Time:%s",pair
                                             ,type,event.time)
                pd["price_buffer"].popleft()

            pd["ticks"] +=1
            # TODO how to visualize strategy-specific parameters for a backtest validation
