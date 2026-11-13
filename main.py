from drafter import *
from bakery import assert_equal
from dataclasses import dataclass
from statistics import mean, stdev
from math import sqrt
 
 
@dataclass
class Stock:
    ticker: str
    name: str
    prices: list[float]          # monthly closing prices (made-up sample data)
 
@dataclass
class Metrics:
    ticker: str
    total_return: float          # percent
    volatility: float            # annualized, percent
    max_drawdown: float          # percent (negative)
    sharpe: float
 
@dataclass
class State:
    stocks: list[Stock]
    selected: str
    risk_free: float             # annual risk-free rate, percent
    results: list[Metrics]
    message: str
 
 
SAMPLE_STOCKS = [
    Stock("AAA", "Alpha Tech",
          [100, 104, 103, 110, 115, 112, 120, 118, 125, 130, 127, 135, 140]),
    Stock("BBB", "Beta Energy",
          [50, 48, 52, 47, 45, 49, 53, 50, 44, 46, 51, 55, 54]),
    Stock("CCC", "Gamma Foods",
          [80, 81, 82, 82, 83, 84, 83, 85, 86, 86, 87, 88, 89]),
    Stock("DDD", "Delta Mining",
          [30, 36, 28, 33, 40, 31, 27, 35, 42, 38, 29, 34, 37]),
]
 
 
def monthly_returns(prices: list[float]) -> list[float]:
    """
    Calculate the month-over-month return for each consecutive pair of prices
    Args:
        prices: Monthly closing prices, oldest first
    Returns:
        A list of returns as decimal fractions (10 percent is one tenth), one fewer than prices
    """
    return [(prices[i] / prices[i - 1]) - 1 for i in range(1, len(prices))]
 
def total_return(prices: list[float]) -> float:
    """
    Calculate the percent change from the first price to the last price
    Args:
        prices: Monthly closing prices, oldest first
    Returns:
        The total return as a percent
    """
    return (prices[-1] / prices[0] - 1) * 100
 
def annual_volatility(prices: list[float]) -> float:
    """
    Calculate annualized volatility: the standard deviation of monthly
    returns multiplied by the square root of 12
    Args:
        prices: Monthly closing prices, oldest first
    Returns:
        The annualized volatility as a percent, or zero if there are
        fewer than two monthly returns
    """
    returns = monthly_returns(prices)
    if len(returns) < 2:
        return 0.0
    return stdev(returns) * sqrt(12) * 100
 
def max_drawdown(prices: list[float]) -> float:
    """
    Find the largest peak-to-trough drop in the price history
    Args:
        prices: Monthly closing prices, oldest first
    Returns:
        The worst drop as a negative percent, or zero if the price never fell
    """
    peak = prices[0]
    worst = 0.0
    for price in prices:
        if price > peak:
            peak = price
        drop = (price / peak - 1) * 100
        if drop < worst:
            worst = drop
    return worst
 
def sharpe_ratio(prices: list[float], risk_free_pct: float) -> float:
    """
    Calculate the Sharpe ratio: (annual return - risk-free rate) divided
    by annualized volatility
    Args:
        prices: Monthly closing prices, oldest first
        risk_free_pct: The annual risk-free rate as a percent
    Returns:
        The Sharpe ratio, or zero if volatility is zero or there are
        fewer than two monthly returns
    """
    returns = monthly_returns(prices)
    if len(returns) < 2:
        return 0.0
    volatility = stdev(returns) * sqrt(12)
    if volatility == 0:
        return 0.0
    annual_return = mean(returns) * 12
    return (annual_return - risk_free_pct / 100) / volatility
 
def compute_metrics(stock: Stock, risk_free: float) -> Metrics:
    """
    Compute all four risk metrics for one stock, rounded to 2 decimal places
    Args:
        stock: The stock to analyze
        risk_free: The annual risk-free rate as a percent
    Returns:
        A Metrics object holding the stock's ticker and its results
    """
    return Metrics(
        stock.ticker,
        round(total_return(stock.prices), 2),
        round(annual_volatility(stock.prices), 2),
        round(max_drawdown(stock.prices), 2),
        round(sharpe_ratio(stock.prices, risk_free), 2),
    )
 
 
def find_stock(state: State, ticker: str) -> Stock:
    """
    Look up a stock by its ticker
    Args:
        state: The current state, holding the list of stocks
        ticker: The ticker to look for
    Returns:
        The matching Stock, or the first stock in the list if none match
    """
    for stock in state.stocks:
        if stock.ticker == ticker:
            return stock
    return state.stocks[0]
 
def tickers(state: State) -> list[str]:
    """
    Get the ticker of every stock in the state
    Args:
        state: The current state, holding the list of stocks
    Returns:
        A list of ticker strings, in the same order as the stocks
    """
    return [stock.ticker for stock in state.stocks]
 
def ticker_exists(state: State, ticker: str) -> bool:
    """
    Check whether a ticker is already in the stock list
    Args:
        state: The current state, holding the list of stocks
        ticker: The ticker to look for
    Returns:
        True if a stock with that ticker exists, otherwise False
    """
    for stock in state.stocks:
        if stock.ticker == ticker:
            return True
    return False
 
def find_best_sharpe(results: list[Metrics]) -> Metrics:
    """
    Find the Metrics with the highest Sharpe ratio
    Args:
        results: A non-empty list of Metrics objects
    Returns:
        The Metrics with the highest Sharpe ratio (the first one if tied)
    """
    best = results[0]
    for metrics in results:
        if metrics.sharpe > best.sharpe:
            best = metrics
    return best
 
def is_valid_number(text: str) -> bool:
    """
    Check whether text is a non-negative number such as 4 or 35 with an optional decimal point
    Args:
        text: The text typed by the user
    Returns:
        True if the text (ignoring outer spaces) is a non-negative number
        with at most one decimal point, otherwise False
    """
    text = text.strip()
    if text.count(".") > 1:
        return False
    digits_only = text.replace(".", "")
    return digits_only.isdigit()
 
 
@route
def index(state: State) -> Page:
    """
    Show the home page with the stock picker and navigation buttons
    Args:
        state: The current state
    Returns:
        The home page
    """
    return Page(state, [
        Header("Market & Risk Dashboard"),
        "Analyze return, volatility, max drawdown, and Sharpe ratio "
        "on sample stocks.",
        LineBreak(),
        state.message,
        LineBreak(),
        "Pick a stock:",
        SelectBox("ticker", tickers(state), state.selected),
        Button("Analyze Stock", stock_detail),
        LineBreak(),
        Button("Compare All Stocks", compare),
        Button("Settings", settings),
        Button("Add a Stock", add_stock_page),
        Button("Glossary", glossary),
    ])
 
@route
def stock_detail(state: State, ticker: str) -> Page:
    """
    Show the four risk metrics and the monthly prices for one stock
    Args:
        state: The current state
        ticker: The ticker chosen in the stock picker
    Returns:
        The detail page for that stock
    """
    state.message = ""
    state.selected = ticker
    stock = find_stock(state, ticker)
    metrics = compute_metrics(stock, state.risk_free)
    return Page(state, [
        Header(stock.name + " (" + stock.ticker + ")"),
        "Total return: " + str(metrics.total_return) + "%",
        "Annualized volatility: " + str(metrics.volatility) + "%",
        "Max drawdown: " + str(metrics.max_drawdown) + "%",
        "Sharpe ratio: " + str(metrics.sharpe)
        + " (risk-free rate " + str(state.risk_free) + "%)",
        LineBreak(),
        "Monthly prices: " + ", ".join(str(price) for price in stock.prices),
        LineBreak(),
        Button("Remove This Stock", remove_stock),
        Button("Back", index),
    ])
 
@route
def compare(state: State) -> Page:
    """
    Show a table comparing every stock's metrics and name the best Sharpe
    Args:
        state: The current state
    Returns:
        The comparison page, or a short message if there are no stocks
    """
    state.message = ""
    state.results = [compute_metrics(stock, state.risk_free)
                     for stock in state.stocks]
 
    if len(state.results) == 0:
        return Page(state, [
            Header("Comparison"),
            "Nothing to compare yet. Add some stocks first.",
            Button("Back", index),
        ])
 
    rows = [["Ticker", "Return %", "Volatility %", "Max Drawdown %", "Sharpe"]]
    for metrics in state.results:
        rows.append([metrics.ticker, str(metrics.total_return),
                     str(metrics.volatility), str(metrics.max_drawdown),
                     str(metrics.sharpe)])
 
    best = find_best_sharpe(state.results)
 
    return Page(state, [
        Header("Comparison"),
        Table(rows),
        LineBreak(),
        "Best risk-adjusted return (highest Sharpe): " + best.ticker,
        Button("Back", index),
    ])
 
@route
def settings(state: State) -> Page:
    """
    Show the settings page for changing the risk-free rate
    Args:
        state: The current state
    Returns:
        The settings page
    """
    state.message = ""
    return Page(state, [
        Header("Settings"),
        "Annual risk-free rate (%):",
        TextBox("risk_free", str(state.risk_free)),
        Button("Save", save_settings),
        Button("Back", index),
    ])
 
@route
def save_settings(state: State, risk_free: str) -> Page:
    """
    Validate and save the risk-free rate, then return to the home page
    Args:
        state: The current state
        risk_free: The rate typed by the user, as text
    Returns:
        The home page, showing a success or error message
    """
    if not is_valid_number(risk_free):
        state.message = "Please enter a non-negative number."
    else:
        value = float(risk_free)
        if value > 20:
            state.message = "Rate must be between 0 and 20."
        else:
            state.risk_free = value
            state.message = "Risk-free rate set to " + str(value) + "%."
    return index(state)
 
@route
def add_stock_page(state: State) -> Page:
    """
    Show the form for adding a new stock
    Args:
        state: The current state
    Returns:
        The add-stock page
    """
    state.message = ""
    return Page(state, [
        Header("Add a Stock"),
        "Ticker:", TextBox("ticker", ""),
        "Name:", TextBox("name", ""),
        "Monthly prices, comma-separated (at least 4):",
        TextBox("prices", ""),
        Button("Add", add_stock),
        Button("Back", index),
    ])
 
@route
def add_stock(state: State, ticker: str, name: str, prices: str) -> Page:
    """
    Validate the form, add the new stock, then return to the home page
    Args:
        state: The current state
        ticker: The ticker typed by the user
        name: The company name typed by the user
        prices: Comma-separated monthly prices, as text
    Returns:
        The home page, showing a success or error message
    """
    pieces = prices.split(",")
 
    for piece in pieces:
        if not is_valid_number(piece):
            state.message = "Prices must be numbers separated by commas."
            return index(state)
 
    values = [float(piece.strip()) for piece in pieces]
 
    if len(values) < 4 or min(values) <= 0 or ticker.strip() == "":
        state.message = "Need a ticker and at least 4 positive prices."
        return index(state)
 
    clean_ticker = ticker.strip().upper()
    if ticker_exists(state, clean_ticker):
        state.message = clean_ticker + " is already in the list."
        return index(state)
 
    state.stocks.append(Stock(clean_ticker, name.strip(), values))
    state.selected = clean_ticker
    state.message = "Added " + clean_ticker + "."
    return index(state)
 
@route
def remove_stock(state: State) -> Page:
    """
    Remove the selected stock (unless it is the last one), then go home
    Args:
        state: The current state
    Returns:
        The home page, showing a success or error message
    """
    if len(state.stocks) > 1:
        state.stocks = [stock for stock in state.stocks
                        if stock.ticker != state.selected]
        state.selected = state.stocks[0].ticker
        state.message = "Stock removed."
    else:
        state.message = "Can't remove the last stock."
    return index(state)
 
@route
def glossary(state: State) -> Page:
    """
    Show definitions of the four risk metrics
    Args:
        state: The current state
    Returns:
        The glossary page
    """
    state.message = ""
    return Page(state, [
        Header("Glossary"),
        "Total return: percent change from first to last price.",
        "Volatility: standard deviation of monthly returns, "
        "annualized (x sqrt(12)).",
        "Max drawdown: largest peak-to-trough drop.",
        "Sharpe ratio: (annual return - risk-free rate) "
        "/ annualized volatility.",
        Button("Back", index),
    ])
 

def make_test_state() -> State:
    """
    Build a small, fresh State for tests so tests never share mutations
    Returns:
        A State with stocks AAA (prices 100, 200, 100) and CCC (flat at 100),
        a zero risk-free rate, no results, and an empty message
    """
    return State(
        [Stock("AAA", "Alpha", [100, 200, 100]),
         Stock("CCC", "Gamma", [100, 100, 100, 100])],
        "AAA", 0.0, [], "")
 
assert_equal(monthly_returns([100, 200, 100]), [1.0, -0.5])
assert_equal(monthly_returns([100, 100]), [0.0])
 
assert_equal(total_return([100, 150]), 50.0)
assert_equal(total_return([100, 50]), -50.0)
 
assert_equal(round(annual_volatility([100, 200, 100]), 2), 367.42)
assert_equal(annual_volatility([100, 100, 100]), 0.0)
assert_equal(annual_volatility([100, 110]), 0.0)
 
assert_equal(max_drawdown([100, 120, 90, 110]), -25.0)
assert_equal(max_drawdown([100, 110, 120]), 0.0)
 
assert_equal(round(sharpe_ratio([100, 200, 100], 0.0), 2), 0.82)
assert_equal(sharpe_ratio([100, 100, 100], 4.0), 0.0)
assert_equal(sharpe_ratio([100, 110], 4.0), 0.0)
 
assert_equal(compute_metrics(Stock("AAA", "Alpha", [100, 200, 100]), 0.0), Metrics("AAA", 0.0, 367.42, -50.0, 0.82))
 
assert_equal(find_stock(make_test_state(), "CCC"), Stock("CCC", "Gamma", [100, 100, 100, 100]))
assert_equal(find_stock(make_test_state(), "ZZZ"), Stock("AAA", "Alpha", [100, 200, 100]))


assert_equal(tickers(make_test_state()), ["AAA", "CCC"])
 
assert_equal(ticker_exists(make_test_state(), "AAA"), True)
assert_equal(ticker_exists(make_test_state(), "ZZZ"), False)
 

LOW_SHARPE = Metrics("LOW", 0.0, 1.0, -1.0, 0.5)
HIGH_SHARPE = Metrics("HIGH", 0.0, 1.0, -1.0, 1.5)
MID_SHARPE = Metrics("MID", 0.0, 1.0, -1.0, 0.9)
assert_equal(find_best_sharpe([LOW_SHARPE, HIGH_SHARPE, MID_SHARPE]),
             HIGH_SHARPE)
assert_equal(find_best_sharpe([LOW_SHARPE]), LOW_SHARPE)
 

assert_equal(is_valid_number("4"), True)
assert_equal(is_valid_number(" 3.5 "), True)
assert_equal(is_valid_number("abc"), False)
assert_equal(is_valid_number(""), False)
assert_equal(is_valid_number("-2"), False)
assert_equal(is_valid_number("1.2.3"), False)
 
assert_equal(
    index(make_test_state()),
    Page(make_test_state(), [
        Header("Market & Risk Dashboard"),
        "Analyze return, volatility, max drawdown, and Sharpe ratio "
        "on sample stocks.",
        LineBreak(),
        "",
        LineBreak(),
        "Pick a stock:",
        SelectBox("ticker", ["AAA", "CCC"], "AAA"),
        Button("Analyze Stock", stock_detail),
        LineBreak(),
        Button("Compare All Stocks", compare),
        Button("Settings", settings),
        Button("Add a Stock", add_stock_page),
        Button("Glossary", glossary),
    ]))
 
# stock_detail
assert_equal(
    stock_detail(make_test_state(), "AAA"),
    Page(make_test_state(), [
        Header("Alpha (AAA)"),
        "Total return: 0.0%",
        "Annualized volatility: 367.42%",
        "Max drawdown: -50.0%",
        "Sharpe ratio: 0.82 (risk-free rate 0.0%)",
        LineBreak(),
        "Monthly prices: 100, 200, 100",
        LineBreak(),
        Button("Remove This Stock", remove_stock),
        Button("Back", index),
    ]))
 
#compare (normal case and empty case) 
compare_state = make_test_state()
compare_state.results = [Metrics("AAA", 0.0, 367.42, -50.0, 0.82),
                         Metrics("CCC", 0.0, 0.0, 0.0, 0.0)]
assert_equal(
    compare(make_test_state()),
    Page(compare_state, [
        Header("Comparison"),
        Table([["Ticker", "Return %", "Volatility %", "Max Drawdown %",
                "Sharpe"],
               ["AAA", "0.0", "367.42", "-50.0", "0.82"],
               ["CCC", "0.0", "0.0", "0.0", "0.0"]]),
        LineBreak(),
        "Best risk-adjusted return (highest Sharpe): AAA",
        Button("Back", index),
    ]))
assert_equal(
    compare(State([], "", 0.0, [], "")),
    Page(State([], "", 0.0, [], ""), [
        Header("Comparison"),
        "Nothing to compare yet. Add some stocks first.",
        Button("Back", index),
    ]))
 
#settings
assert_equal(
    settings(make_test_state()),
    Page(make_test_state(), [
        Header("Settings"),
        "Annual risk-free rate (%):",
        TextBox("risk_free", "0.0"),
        Button("Save", save_settings),
        Button("Back", index),
    ]))
 
# save_settings (valid, not a number, too large)
saved_state = make_test_state()
saved_state.risk_free = 3.5
saved_state.message = "Risk-free rate set to 3.5%."
assert_equal(save_settings(make_test_state(), "3.5"), index(saved_state))
 
not_number_state = make_test_state()
not_number_state.message = "Please enter a non-negative number."
assert_equal(save_settings(make_test_state(), "abc"), index(not_number_state))
 
too_large_state = make_test_state()
too_large_state.message = "Rate must be between 0 and 20."
assert_equal(save_settings(make_test_state(), "25"), index(too_large_state))
 
# add_stock_page
assert_equal(
    add_stock_page(make_test_state()),
    Page(make_test_state(), [
        Header("Add a Stock"),
        "Ticker:", TextBox("ticker", ""),
        "Name:", TextBox("name", ""),
        "Monthly prices, comma-separated (at least 4):",
        TextBox("prices", ""),
        Button("Add", add_stock),
        Button("Back", index),
    ]))
 
# add_stock (success, bad prices, too few prices, duplicate)
added_state = make_test_state()
added_state.stocks.append(Stock("DDD", "Delta", [1.0, 2.0, 3.0, 4.0]))
added_state.selected = "DDD"
added_state.message = "Added DDD."
assert_equal(add_stock(make_test_state(), "ddd", "Delta", "1,2,3,4"),
             index(added_state))
 
bad_prices_state = make_test_state()
bad_prices_state.message = "Prices must be numbers separated by commas."
assert_equal(add_stock(make_test_state(), "DDD", "Delta", "1,x,3,4"),
             index(bad_prices_state))
 
too_few_state = make_test_state()
too_few_state.message = "Need a ticker and at least 4 positive prices."
assert_equal(add_stock(make_test_state(), "DDD", "Delta", "1,2,3"),
             index(too_few_state))
 
duplicate_state = make_test_state()
duplicate_state.message = "AAA is already in the list."
assert_equal(add_stock(make_test_state(), "aaa", "Alpha", "1,2,3,4"),
             index(duplicate_state))
 
 
# glossary
assert_equal(
    glossary(make_test_state()),
    Page(make_test_state(), [
        Header("Glossary"),
        "Total return: percent change from first to last price.",
        "Volatility: standard deviation of monthly returns, "
        "annualized (x sqrt(12)).",
        "Max drawdown: largest peak-to-trough drop.",
        "Sharpe ratio: (annual return - risk-free rate) "
        "/ annualized volatility.",
        Button("Back", index),
    ]))
 
start_server(State(SAMPLE_STOCKS, SAMPLE_STOCKS[0].ticker, 4.0, [], ""))
