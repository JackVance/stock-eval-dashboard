const State = {
    currentTicker: 'AAPL',
    startYear: new Date().getFullYear() - 3,
    endYear: new Date().getFullYear(),

    tickers: [],
    isLoading: false,
    stockData: null,

    setTickers(tickers) {
        this.tickers = tickers.sort();
    },

    addTicker(ticker) {
        const upperTicker = ticker.toUpperCase().trim();
        if (upperTicker && !this.tickers.includes(upperTicker)) {
            this.tickers.push(upperTicker);
            this.tickers.sort();
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
