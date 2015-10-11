from __future__ import print_function

from qsforex.backtest.backtest import Backtest
from qsforex.execution.execution import SimulatedExecution
from qsforex.portfolio.portfolio import Portfolio
from qsforex import settings
from qsforex.strategy.bollinger import BollingerBands
from qsforex.data.price import HistoricCSVPriceHandler


if __name__ == "__main__":
    # Trade on GBP/USD and EUR/USD
    pairs = ["GBPUSD", "EURUSD"]
    
    # Create the strategy parameters for the
    # MovingAverageCrossStrategy
    strategy_params = {"win_size": 50,
                       "std_factor": 2}
   
    # Create and execute the backtest
    backtest = Backtest(
        pairs, HistoricCSVPriceHandler, 
        BollingerBands, strategy_params,
        Portfolio, SimulatedExecution, 
        equity=settings.EQUITY
    )
    backtest.simulate_trading()