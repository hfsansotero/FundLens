import pandas as pd


def static_correlation(returns_df: pd.DataFrame) -> pd.DataFrame:
    """Pearson correlation matrix from a wide DataFrame (cols = tickers, rows = dates)."""
    return returns_df.corr()


def rolling_correlation(returns_df: pd.DataFrame, window: int = 60) -> dict[tuple[str, str], pd.Series]:
    """Pairwise rolling correlations. Returns dict keyed by (ticker_a, ticker_b)."""
    tickers = returns_df.columns.tolist()
    result = {}
    for i, a in enumerate(tickers):
        for b in tickers[i + 1:]:
            result[(a, b)] = returns_df[a].rolling(window).corr(returns_df[b])
    return result
