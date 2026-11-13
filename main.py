from drafter import *
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
    Stock("AAA", "Alpha Tech", [100, 104, 103, 110, 115, 112, 120, 118, 125, 130, 127, 135, 140]),
    Stock("BBB", "Beta Energy", [50, 48, 52, 47, 45, 49, 53, 50, 44, 46, 51, 55, 54]),
    Stock("CCC", "Gamma Foods", [80, 81, 82, 82, 83, 84, 83, 85, 86, 86, 87, 88, 89]),
    Stock("DDD", "Delta Mining", [30, 36, 28, 33, 40, 31, 27, 35, 42, 38, 29, 34, 37]),
]


def monthly_returns(prices: list[float]) -> list[float]:
    return [(prices[i] / prices[i - 1]) - 1 for i in range(1, len(prices))]

def total_return(prices: list[float]) -> float:
    return (prices[-1] / prices[0] - 1) * 100

def annual_volatility(prices: list[float]) -> float:
    rets = monthly_returns(prices)
    if len(rets) < 2:
        return 0.0
    return stdev(rets) * sqrt(12) * 100

def max_drawdown(prices: list[float]) -> float:
    peak = prices[0]
    worst = 0.0
    for p in prices:
        if p > peak:
            peak = p
        drop = (p / peak - 1) * 100
        if drop < worst:
            worst = drop
    return worst

def sharpe_ratio(prices: list[float], risk_free_pct: float) -> float:
    rets = monthly_returns(prices)
    if len(rets) < 2:
        return 0.0
    vol = stdev(rets) * sqrt(12)
    if vol == 0:
        return 0.0
    annual_return = mean(rets) * 12
    return (annual_return - risk_free_pct / 100) / vol

def compute_metrics(stock: Stock, risk_free: float) -> Metrics:
    return Metrics(
        stock.ticker,
        round(total_return(stock.prices), 2),
        round(annual_volatility(stock.prices), 2),
        round(max_drawdown(stock.prices), 2),
        round(sharpe_ratio(stock.prices, risk_free), 2),
    )

def find_stock(state: State, ticker: str) -> Stock:
    for s in state.stocks:
        if s.ticker == ticker:
            return s
    return state.stocks[0]

def tickers(state: State) -> list[str]:
    return [s.ticker for s in state.stocks]

# ---------- Routes ----------

@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Market & Risk Dashboard"),
        "Analyze return, volatility, max drawdown, and Sharpe ratio on sample stocks.",
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
    state.selected = ticker
    stock = find_stock(state, ticker)
    m = compute_metrics(stock, state.risk_free)
    return Page(state, [
        Header(stock.name + " (" + stock.ticker + ")"),
        "Total return: " + str(m.total_return) + "%",
        "Annualized volatility: " + str(m.volatility) + "%",
        "Max drawdown: " + str(m.max_drawdown) + "%",
        "Sharpe ratio: " + str(m.sharpe) + " (risk-free rate " + str(state.risk_free) + "%)",
        LineBreak(),
        "Monthly prices: " + ", ".join(str(p) for p in stock.prices),
        LineBreak(),
        Button("Remove This Stock", remove_stock),
        Button("Back", index),
    ])

@route
def compare(state: State) -> Page:
    state.results = [compute_metrics(s, state.risk_free) for s in state.stocks]
    rows = [["Ticker", "Return %", "Volatility %", "Max Drawdown %", "Sharpe"]]
    for m in state.results:
        rows.append([m.ticker, str(m.total_return), str(m.volatility),
                     str(m.max_drawdown), str(m.sharpe)])
    best = max(state.results, key=lambda m: m.sharpe)
    return Page(state, [
        Header("Comparison"),
        Table(rows),
        LineBreak(),
        "Best risk-adjusted return (highest Sharpe): " + best.ticker,
        Button("Back", index),
    ])

@route
def settings(state: State) -> Page:
    return Page(state, [
        Header("Settings"),
        "Annual risk-free rate (%):",
        TextBox("risk_free", str(state.risk_free)),
        Button("Save", save_settings),
        Button("Back", index),
    ])

@route
def save_settings(state: State, risk_free: str) -> Page:
    try:
        value = float(risk_free)
        if value < 0 or value > 20:
            state.message = "Rate must be between 0 and 20."
        else:
            state.risk_free = value
            state.message = "Risk-free rate set to " + str(value) + "%."
    except ValueError:
        state.message = "Please enter a number."
    return index(state)

@route
def add_stock_page(state: State) -> Page:
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
    try:
        values = [float(p.strip()) for p in prices.split(",")]
    except ValueError:
        state.message = "Prices must be numbers separated by commas."
        return index(state)
    if len(values) < 4 or min(values) <= 0 or ticker.strip() == "":
        state.message = "Need a ticker and at least 4 positive prices."
        return index(state)
    state.stocks.append(Stock(ticker.strip().upper(), name.strip(), values))
    state.selected = ticker.strip().upper()
    state.message = "Added " + state.selected + "."
    return index(state)

@route
def remove_stock(state: State) -> Page:
    if len(state.stocks) > 1:
        state.stocks = [s for s in state.stocks if s.ticker != state.selected]
        state.selected = state.stocks[0].ticker
        state.message = "Stock removed."
    else:
        state.message = "Can't remove the last stock."
    return index(state)

@route
def glossary(state: State) -> Page:
    return Page(state, [
        Header("Glossary"),
        "Total return: percent change from first to last price.",
        "Volatility: standard deviation of monthly returns, annualized (x sqrt(12)).",
        "Max drawdown: largest peak-to-trough drop.",
        "Sharpe ratio: (annual return - risk-free rate) / annualized volatility.",
        Button("Back", index),
    ])

start_server(State(SAMPLE_STOCKS, SAMPLE_STOCKS[0].ticker, 4.0, [], ""))
