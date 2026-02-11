const API = {
    getBaseUrl() {
        return window.CONFIG.API_URL.replace(/\/$/, '');
    },

    async fetchStock(ticker, startYear, endYear) {
        const url = `${this.getBaseUrl()}/api/stock/${encodeURIComponent(ticker)}?start_year=${startYear}&end_year=${endYear}`;

        const response = await fetch(url);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || `HTTP ${response.status}`);
        }

        return data;
    },

    async getTickers() {
        const url = `${this.getBaseUrl()}/api/tickers`;

        const response = await fetch(url);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || `HTTP ${response.status}`);
        }

        return data.tickers || [];
    },

    async addTicker(ticker) {
        const url = `${this.getBaseUrl()}/api/tickers`;

        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticker: ticker.toUpperCase() })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || `HTTP ${response.status}`);
        }

        return data;
    },

    async deleteTicker(ticker) {
        const url = `${this.getBaseUrl()}/api/tickers/${encodeURIComponent(ticker)}`;

        const response = await fetch(url, { method: 'DELETE' });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || `HTTP ${response.status}`);
        }

        return data;
    }
};
