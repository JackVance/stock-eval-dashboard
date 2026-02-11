/** Plotly charts matching the legacy Dash "Buffalo Stone" theme. */
const Charts = {
    theme: {
        paper_bgcolor: '#696969',
        plot_bgcolor: '#696969',
        font: { color: '#ffffff' },
        gridcolor: '#696969',
        zerolinecolor: '#ffffff'
    },

    colors: {
        white: '#ffffff',
        blue: '#83B0D6',
        blueDark: '#4A85BE',
        red: '#DE3B3E',
        redLight: '#EC6C5B',
        green: '#00CC96',
        greenLight: '#B2C7AD'
    },

    getBaseLayout(title) {
        return {
            title: title,
            paper_bgcolor: this.theme.paper_bgcolor,
            plot_bgcolor: this.theme.plot_bgcolor,
            font: this.theme.font,
            xaxis: {
                gridcolor: this.theme.gridcolor,
                zerolinecolor: this.theme.zerolinecolor
            },
            yaxis: {
                gridcolor: this.theme.gridcolor,
                zerolinecolor: this.theme.zerolinecolor
            },
            margin: { t: 50, r: 20, b: 50, l: 60 }
        };
    },

    filterPrices(prices, startYear, endYear) {
        const startDate = `${startYear}-01-01`;
        const endDate = `${endYear}-12-31`;

        const indices = [];
        prices.dates.forEach((date, i) => {
            if (date >= startDate && date <= endDate) {
                indices.push(i);
            }
        });

        return {
            dates: indices.map(i => prices.dates[i]),
            open: indices.map(i => prices.open[i]),
            high: indices.map(i => prices.high[i]),
            low: indices.map(i => prices.low[i]),
            close: indices.map(i => prices.close[i]),
            volume: indices.map(i => prices.volume[i]),
            ma50: indices.map(i => prices.ma50[i]),
            ma200: indices.map(i => prices.ma200[i])
        };
    },

    filterFinancials(financials, startYear, endYear) {
        return financials.filter(f => {
            const year = parseInt(f.date.substring(0, 4));
            return year >= startYear && year <= endYear;
        });
    },

    /** Price + volume as two vertically stacked subplots. */
    renderPriceChart(containerId, prices, info) {
        if (!prices.dates || prices.dates.length === 0) {
            document.getElementById(containerId).innerHTML = '<p style="text-align:center;padding:50px;">No price data for selected range</p>';
            return;
        }

        // Green for up days, red for down
        const volumeColors = prices.close.map((close, i) => {
            if (i === 0) return this.colors.blue;
            return close > prices.close[i - 1] ? this.colors.green : this.colors.redLight;
        });

        const traces = [
            // Close price
            {
                x: prices.dates,
                y: prices.close,
                name: 'Close Price',
                type: 'scatter',
                mode: 'markers',
                marker: { color: this.colors.white, size: 2 },
                xaxis: 'x',
                yaxis: 'y'
            },
            // 50-day MA
            {
                x: prices.dates,
                y: prices.ma50,
                name: '50-day Moving Average',
                type: 'scatter',
                mode: 'lines',
                xaxis: 'x',
                yaxis: 'y'
            },
            // 200-day MA
            {
                x: prices.dates,
                y: prices.ma200,
                name: '200-day Moving Average',
                type: 'scatter',
                mode: 'lines',
                xaxis: 'x',
                yaxis: 'y'
            },
            // Volume bars
            {
                x: prices.dates,
                y: prices.volume,
                name: 'Daily Volume',
                type: 'bar',
                marker: { color: volumeColors },
                xaxis: 'x2',
                yaxis: 'y2',
                showlegend: false
            }
        ];

        const layout = {
            ...this.getBaseLayout(`${info.shortName} (${info.symbol})`),
            grid: { rows: 2, columns: 1, pattern: 'independent', roworder: 'top to bottom' },
            xaxis: { ...this.getBaseLayout().xaxis, domain: [0, 1], anchor: 'y' },
            yaxis: { ...this.getBaseLayout().yaxis, domain: [0.3, 1], title: 'Close Price (USD)' },
            xaxis2: { ...this.getBaseLayout().xaxis, domain: [0, 1], anchor: 'y2', title: 'Date' },
            yaxis2: { ...this.getBaseLayout().yaxis, domain: [0, 0.25], title: 'Volume' },
            showlegend: true,
            legend: { x: 0, y: 1.1, orientation: 'h' }
        };

        Plotly.newPlot(containerId, traces, layout, { responsive: true });
    },

    renderFinancialsChart(containerId, financials) {
        if (!financials || financials.length === 0) {
            document.getElementById(containerId).innerHTML = '<p style="text-align:center;padding:50px;">No financial data available</p>';
            return;
        }

        const sorted = [...financials].sort((a, b) => a.date.localeCompare(b.date));
        const dates = sorted.map(f => f.date);

        const colorMap = {
            'Total Revenue': this.colors.white,
            'Cost of Revenue': this.colors.red,
            'Operating Expense': this.colors.redLight,
            'Operating Income': this.colors.greenLight,
            'Net Income': this.colors.green,
            'R&D': this.colors.blue
        };

        const traces = [
            { name: 'Total Revenue', y: sorted.map(f => f.totalRevenue), color: colorMap['Total Revenue'] },
            { name: 'Cost of Revenue', y: sorted.map(f => f.costOfRevenue), color: colorMap['Cost of Revenue'] },
            { name: 'Operating Expense', y: sorted.map(f => f.operatingExpense), color: colorMap['Operating Expense'] },
            { name: 'Operating Income', y: sorted.map(f => f.operatingIncome), color: colorMap['Operating Income'] },
            { name: 'Net Income', y: sorted.map(f => f.netIncome), color: colorMap['Net Income'] },
            { name: 'R&D', y: sorted.map(f => f.researchAndDevelopment), color: colorMap['R&D'] }
        ].filter(t => t.y.some(v => v != null)).map(t => ({
            x: dates,
            y: t.y,
            name: t.name,
            type: 'scatter',
            mode: 'lines+markers',
            line: { color: t.color },
            connectgaps: true,  // Connect lines across null/missing values
            hovertemplate: '%{y:,.0f}<br>%{x}<extra></extra>'
        }));

        const layout = {
            ...this.getBaseLayout('Annual Financials (SEC EDGAR)'),
            xaxis: { ...this.getBaseLayout().xaxis, title: 'Date' },
            yaxis: { ...this.getBaseLayout().yaxis, title: 'USD' },
            legend: { title: { text: '' } }
        };

        Plotly.newPlot(containerId, traces, layout, { responsive: true });
    },

    renderInfoPanel(containerId, info) {
        const formatNumber = (n) => {
            if (n == null) return 'N/A';
            if (n >= 1e12) return `$${(n / 1e12).toFixed(2)}T`;
            if (n >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
            if (n >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
            return `$${n.toLocaleString()}`;
        };

        const formatPE = (pe) => pe != null ? pe.toFixed(2) : 'N/A';

        const debtToEbitda = (info.totalDebt && info.ebitda)
            ? (info.totalDebt / info.ebitda).toFixed(3)
            : 'N/A';

        const html = `
            <h4>${info.name}</h4>
            <p><a href="${info.website}" target="_blank" style="color: #83B0D6;">${info.website}</a></p>
            <p><span class="label">Sector:</span> <span class="value">${info.sector}</span> |
               <span class="label">Industry:</span> <span class="value">${info.industry}</span></p>
            <p><span class="label">Current Price:</span> <span class="value">$${info.currentPrice?.toFixed(2) || 'N/A'}</span> |
               <span class="label">Market Cap:</span> <span class="value">${formatNumber(info.marketCap)}</span></p>
            <p><span class="label">Trailing P/E:</span> <span class="value">${formatPE(info.trailingPe)}</span> |
               <span class="label">Forward P/E:</span> <span class="value">${formatPE(info.forwardPe)}</span></p>
            <p><span class="label">Debt to EBITDA:</span> <span class="value">${debtToEbitda}</span></p>
            <div class="summary">${info.summary || ''}</div>
        `;

        document.getElementById(containerId).innerHTML = html;
    },

    /** Stacked bar: current vs non-current for assets and liabilities. */
    renderBalanceBarChart(containerId, balanceSheets) {
        if (!balanceSheets || balanceSheets.length === 0) {
            document.getElementById(containerId).innerHTML = '<p style="text-align:center;padding:50px;">No balance sheet data available</p>';
            return;
        }

        const bs = balanceSheets[0];  // most recent period
        const hasCurrentNonCurrent = bs.currentAssets != null && bs.nonCurrentAssets != null;

        let traces;
        if (hasCurrentNonCurrent) {
            traces = [
                {
                    name: 'Non-Current Assets',
                    x: ['Assets'],
                    y: [bs.nonCurrentAssets],
                    type: 'bar',
                    marker: { color: this.colors.blue },
                    hovertemplate: '<b>Non-Current Assets:</b> $%{y:,.0f}<extra></extra>'
                },
                {
                    name: 'Current Assets',
                    x: ['Assets'],
                    y: [bs.currentAssets],
                    type: 'bar',
                    marker: { color: this.colors.blueDark },
                    hovertemplate: '<b>Current Assets:</b> $%{y:,.0f}<extra></extra>'
                },
                {
                    name: 'Non-Current Liabilities',
                    x: ['Liabilities'],
                    y: [bs.nonCurrentLiabilities],
                    type: 'bar',
                    marker: { color: this.colors.redLight },
                    hovertemplate: '<b>Non-Current Liabilities:</b> $%{y:,.0f}<extra></extra>'
                },
                {
                    name: 'Current Liabilities',
                    x: ['Liabilities'],
                    y: [bs.currentLiabilities],
                    type: 'bar',
                    marker: { color: this.colors.red },
                    hovertemplate: '<b>Current Liabilities:</b> $%{y:,.0f}<extra></extra>'
                }
            ];
        } else {
            traces = [
                {
                    name: 'Total Assets',
                    x: ['Assets'],
                    y: [bs.totalAssets],
                    type: 'bar',
                    marker: { color: this.colors.blue },
                    hovertemplate: '<b>Total Assets:</b> $%{y:,.0f}<extra></extra>'
                },
                {
                    name: 'Total Liabilities',
                    x: ['Liabilities'],
                    y: [bs.totalLiabilities],
                    type: 'bar',
                    marker: { color: this.colors.red },
                    hovertemplate: '<b>Total Liabilities:</b> $%{y:,.0f}<extra></extra>'
                }
            ];
        }

        const layout = {
            ...this.getBaseLayout('Assets vs Liabilities'),
            barmode: 'stack',
            yaxis: { ...this.getBaseLayout().yaxis, title: 'USD' },
            showlegend: true,
            legend: { orientation: 'h', y: -0.15 }
        };

        Plotly.newPlot(containerId, traces, layout, { responsive: true });
    },

    /** Hierarchical asset/liability breakdown. */
    renderBalanceSunburstChart(containerId, balanceSheets) {
        if (!balanceSheets || balanceSheets.length === 0) {
            document.getElementById(containerId).innerHTML = '<p style="text-align:center;padding:50px;">No balance sheet data available</p>';
            return;
        }

        const bs = balanceSheets[0];

        // Hierarchy matches the legacy Dash sunburst layout
        const parentDict = {
            'Total Assets': '',
            'Current Assets': 'Total Assets',
            'Inventory': 'Current Assets',
            'Receivables': 'Current Assets',
            'Cash And Cash Equivalents': 'Current Assets',
            'Short Term Investments': 'Current Assets',
            'Other Current Assets': 'Current Assets',
            'Non-Current Assets': 'Total Assets',
            'Net PPE': 'Non-Current Assets',
            'Investments And Advances': 'Non-Current Assets',
            'Goodwill And Intangibles': 'Non-Current Assets',
            'Other Non-Current Assets': 'Non-Current Assets',
            'Total Liabilities': '',
            'Current Liabilities': 'Total Liabilities',
            'Payables': 'Current Liabilities',
            'Current Deferred Liabilities': 'Current Liabilities',
            'Current Debt': 'Current Liabilities',
            'Other Current Liabilities': 'Current Liabilities',
            'Non-Current Liabilities': 'Total Liabilities',
            'Long Term Debt': 'Non-Current Liabilities',
            'Other Non-Current Liabilities': 'Non-Current Liabilities'
        };

        const valueMap = {
            'Total Assets': bs.totalAssets,
            'Current Assets': bs.currentAssets,
            'Inventory': bs.inventory,
            'Receivables': bs.receivables,
            'Cash And Cash Equivalents': bs.cashAndEquivalents,
            'Short Term Investments': bs.shortTermInvestments,
            'Other Current Assets': bs.otherCurrentAssets,
            'Non-Current Assets': bs.nonCurrentAssets,
            'Net PPE': bs.netPpe,
            'Investments And Advances': bs.investmentsAndAdvances,
            'Goodwill And Intangibles': bs.goodwillAndIntangibles,
            'Other Non-Current Assets': bs.otherNonCurrentAssets,
            'Total Liabilities': bs.totalLiabilities,
            'Current Liabilities': bs.currentLiabilities,
            'Payables': bs.payables,
            'Current Deferred Liabilities': bs.currentDeferredLiabilities,
            'Current Debt': bs.currentDebt,
            'Other Current Liabilities': bs.otherCurrentLiabilities,
            'Non-Current Liabilities': bs.nonCurrentLiabilities,
            'Long Term Debt': bs.longTermDebt,
            'Other Non-Current Liabilities': bs.otherNonCurrentLiabilities
        };

        const colorMap = {
            'Total Assets': '#669aca',
            'Current Assets': this.colors.blueDark,
            'Non-Current Assets': this.colors.blue,
            'Total Liabilities': '#e5544c',
            'Current Liabilities': this.colors.red,
            'Non-Current Liabilities': this.colors.redLight
        };

        const labels = [];
        const parents = [];
        const values = [];
        const colors = [];

        for (const [label, parent] of Object.entries(parentDict)) {
            const value = valueMap[label];
            if (value != null && value > 0) {
                labels.push(label);
                parents.push(parent);
                values.push(Math.abs(value));

                // Inherit parent color for leaf nodes
                let color = this.colors.white;
                if (colorMap[label]) {
                    color = colorMap[label];
                } else if (colorMap[parent]) {
                    color = colorMap[parent];
                }
                colors.push(color);
            }
        }

        const trace = {
            type: 'sunburst',
            labels: labels,
            parents: parents,
            values: values,
            branchvalues: 'total',
            marker: { colors: colors },
            hovertemplate: '%{label}<br>$%{value:,.0f}<extra></extra>'
        };

        const layout = {
            ...this.getBaseLayout('Balance Sheet Breakdown'),
            margin: { t: 50, r: 0, b: 10, l: 50 }
        };

        Plotly.newPlot(containerId, [trace], layout, { responsive: true });
    },

    renderAll(data, startYear, endYear) {
        const filteredPrices = this.filterPrices(data.prices, startYear, endYear);
        const filteredFinancials = this.filterFinancials(data.financials, startYear, endYear);

        this.renderPriceChart('price-chart', filteredPrices, data.info);
        this.renderFinancialsChart('financials-chart', filteredFinancials);
        this.renderInfoPanel('info-text', data.info);
        // Balance sheets always show most recent (not filtered by year)
        this.renderBalanceBarChart('balance-bar-chart', data.balanceSheets);
        this.renderBalanceSunburstChart('balance-sunburst-chart', data.balanceSheets);
    },

    showError(message) {
        const errorHtml = `<p style="text-align:center;padding:50px;color:#DE3B3E;">Error: ${message}</p>`;
        ['price-chart', 'financials-chart', 'balance-bar-chart', 'balance-sunburst-chart'].forEach(id => {
            document.getElementById(id).innerHTML = errorHtml;
        });
        document.getElementById('info-text').innerHTML = errorHtml;
    }
};
