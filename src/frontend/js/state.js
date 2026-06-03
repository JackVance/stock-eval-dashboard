const State = {
    currentTicker: 'AAPL',
    startYear: new Date().getFullYear() - 3,
    endYear: new Date().getFullYear(),

    tickers: [],
    isLoading: false,
    stockData: null,

    setTickers(tickers) {
        // Preserve server-side order: auto top-N comes back in market-cap descending,
        // followed by user-added tickers alphabetically.
        this.tickers = [...tickers];
    },

    addTicker(ticker) {
        const upperTicker = ticker.toUpperCase().trim();
        if (upperTicker && !this.tickers.includes(upperTicker)) {
            this.tickers.push(upperTicker);
            return true;
        }
        return false;
    },

    setCurrentTicker(ticker) {
        this.currentTicker = ticker.toUpperCase().trim();
    },

    setYearRange(start, end) {
        this.startYear = parseInt(start, 10);
        this.endYear = parseInt(end, 10);
    },

    setStockData(data) {
        this.stockData = data;
    },

    setLoading(loading) {
        this.isLoading = loading;
    }
};
