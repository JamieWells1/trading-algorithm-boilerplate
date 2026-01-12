import utils.convert as convert
import pandas as pd
import core.Account as order
import utils.indicator as indicator
import api.fetch as api
from core.Rules import Rules
import core.strategies as strategies
from core.StopLossTakeProfit import StopLossTakeProfit


def indicators(account, data):
    config = api.get_settings()
    entries = {}  # datetime: close price
    exits = {}  # datetime: close price
    log = [-1]

    stoploss_takeprofit = StopLossTakeProfit()

    datetimes, opens, closes, highs, lows = convert.series_to_lists(data)

    """
    Here is a list of the data you have access to:

    - datetimes: A list of all datetimes.
    - opens: A list of opening prices.
    - closes: A list of closing prices.
    - highs: A list of high prices.
    - lows: A list of low prices.
    - data.rsi: A list of RSI values.
    - data.sma: A list of SMA values.
    - data.atr: A list of ATR values.
    - data.std_dev: A list of standard deviation values.

    All these values line up for each of your candles. For example, if you took datetimes[6], 
    closes[6] and account.rsi[6], each value would correlate to the same candle; the 7th candle.
    """

    candles = []
    for i in range(len(data.closes)):
        candle = {}
        candle["datetime"] = datetimes[i]
        candle["open"] = opens[i]
        candle["close"] = closes[i]
        candle["high"] = highs[i]
        candle["low"] = lows[i]
        candle["sma"] = data.sma[i]
        candle["rsi"] = data.rsi[i]
        candle["atr"] = data.atr[i]
        candle["std_dev"] = data.std_dev[i]

        candles.append(candle)

    def buy(entries, amount, price):
        entries = indicator.add(entries, candles[i]["datetime"], price)
        account.buy_order(candles[i]["datetime"], amount, price)
        log.append("BUY")

    def sell(exits, price):
        exits = indicator.add(exits, candles[i]["datetime"], price)
        account.sell_order(candles[i]["datetime"], price)
        log.append("SELL")

    initial_buy_amount = (
        config["account"]["baseOrderValue"] * config["multipliers"]["buyMultiplier"]
    )
    payload = {
        "z": 0,
        "initial_buy_amount": 0,
        "account": account,
    }
    rules = Rules(payload)

    strategy_1_period = 7

    for i in range(strategy_1_period, len(candles)):

        payload = {
            "initial_buy_amount": initial_buy_amount,
            "uninvested_balance": account.uninvested_balance,
            "account": account,
        }
        rules.payload = payload

        validate_response = rules.validate()
        can_buy = all(validate_response.values())

        if can_buy:
            strategy_1_response = strategies.bearish_comeback(
                candles[i - strategy_1_period : i + 1], strategy_1_period
            )
            if strategy_1_response["buy"]:
                buy(
                    entries, strategy_1_response["amount"], strategy_1_response["price"]
                )
                stoploss_takeprofit.update(
                    strategy_1_response["price"],
                    candles[i]["atr"],
                    candles[i]["datetime"],
                )

        if stoploss_takeprofit.values_set:
            sltp_response = stoploss_takeprofit.exit(candles[i])
            if sltp_response["sell"]:
                sell(exits, sltp_response["price"])
                stoploss_takeprofit.remove()

        current_close = candles[i]["close"]
        account.open_position_amount = account.shares_owned * current_close
        account.balance_absolute = (
            account.uninvested_balance + account.open_position_amount
        )
        account.profit = account.balance_absolute - config["account"]["initialBalance"]
        data.ongoing_balance.append(account.balance_absolute)

    entries = pd.Series(entries.values(), index=entries.keys())
    exits = pd.Series(exits.values(), index=exits.keys())

    return (
        entries,
        exits,
        stoploss_takeprofit.stoploss_regions,
        stoploss_takeprofit.takeprofit_regions,
    )
