__author__ = 'jscastanoc'
import os
import copy
from collections import deque
import logging
import csv

import numpy as np



from qsforex.event.event import SignalEvent
from qsforex.settings import OUTPUT_RESULTS_DIR

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

        self.set_executionLogger()
        self.set_signalLogger()


        fields = ["time_stamp", "ticks","mvg_avg", "mvg_std", "signal"]
        self.set_algorithmTracker(pairs,fields)

        # set hyperparameters of the algorithm and the object
        self.pairs = pairs
        self.pairs_dict = self.create_pairs_dict()
        self.events = events
        self.win_size = win_size
        self.std_factor = std_factor

    def __del__(self):
        for p in self.alg_trackerHandler.keys():
            self.logger_exec.debug("closing logging file %s",self.alg_trackerHandler[p].name)
            self.alg_trackerHandler[p].close()

    def set_executionLogger(self):
        # set execution logger
        self.logger_exec = logging.getLogger(__name__)
        self.logger_exec.setLevel(logging.DEBUG)
        logfile_name = os.path.join(OUTPUT_RESULTS_DIR, "exec.log")
        log_handlerFileExec = logging.FileHandler(logfile_name)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        log_handlerFileExec.setFormatter(formatter)
        self.logger_exec.addHandler(log_handlerFileExec)


    def set_signalLogger(self):
        # set signal logger
        self.logger_signals = logging.getLogger(__name__)
        self.logger_signals.setLevel(logging.DEBUG)

        logfile_name = os.path.join(OUTPUT_RESULTS_DIR, "signals.log")
        log_handlerFile = logging.FileHandler(logfile_name)
        log_handlerFile.setLevel(logging.DEBUG)
        self.logger_signals.addHandler(log_handlerFile)

        log_handlerStream = logging.StreamHandler()
        log_handlerStream.setLevel(logging.DEBUG)
        self.logger_signals.addHandler(log_handlerStream)

    def set_algorithmTracker(self,pairs,fields):
        """
        set  paradigm/specific tracker of parameters and hyperparameters
        fields contains the information logged:
          time_stamp: real time of the tick
          ticks: indexing of the time stamp
          mvg_avg: current value of the moving average (bollinger-band specific)
          mvg_std: current value of the moving standard deviation (bb specific)
          signal: string indicating sell/buy signals
        :param pairs: string coding the currency pair, e.g., EURUSD
        :return: n/a
        """
        # set signal logger
        self.alg_trackerHandler = {}
        self.alg_trackerData = {}
        for p in pairs:
            fname = os.path.join(OUTPUT_RESULTS_DIR, "alg_tracker"+p+".csv")
            self.logger_exec.debug("opening logging file %s",fname)
            self.alg_trackerHandler[p] = open(fname, 'wb')
            self.alg_trackerData[p] = csv.writer(self.alg_trackerHandler[p], delimiter=',')
            self.alg_trackerData[p].writerow(fields)


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
            p_data = self.pairs_dict[pair]
            p_data["price_buffer"].append(price)

            # pre initialize parameters for the alg_tracker
            mvg_avg = np.nan
            mvg_std = np.nan
            sig_type = "n/a"
            if p_data["ticks"] >= self.win_size:
                mvg_avg = np.mean(p_data["price_buffer"])
                mvg_std = np.std(p_data["price_buffer"])

                upper_bound = (mvg_avg+self.std_factor*mvg_std)
                lower_bound = (mvg_avg-self.std_factor*mvg_std)

                # generate the sell/buy signals according to the bollinger rules
                if price > upper_bound and p_data["invested"]:
                    sig_type = "sell"
                    signal = SignalEvent(pair, "market", sig_type, event.time)
                    self.events.put(signal)
                    p_data["invested"] = False
                    self.logger_signals.info("Pair:%s Type:%s Time:%s",pair
                                             ,sig_type,event.time)
                if price < lower_bound and not p_data["invested"]:
                    sig_type = "buy"
                    signal = SignalEvent(pair, "market", sig_type, event.time )
                    self.events.put(signal)
                    p_data["invested"] = True
                    self.logger_signals.info("Pair:%s Type:%s Time:%s",pair
                                             ,sig_type,event.time)
                p_data["price_buffer"].popleft()

            self.alg_trackerData[pair].writerow([event.time,
                                                p_data["ticks"],
                                                price,
                                                mvg_avg,
                                                mvg_std,
                                                sig_type])

            p_data["ticks"] +=1
            # TODO how to visualize strategy-specific parameters for a backtest validation
