(function() {
    'use strict';

    // DOM elements
    const dropdown = document.getElementById('company-dropdown');
    const customTickerInput = document.getElementById('custom-ticker');
    const addTickerBtn = document.getElementById('add-ticker-btn');
    const rangeMin = document.getElementById('range-min');
    const rangeMax = document.getElementById('range-max');
    const sliderRange = document.querySelector('.slider-range');
    const rangeTicksContainer = document.getElementById('range-ticks');
    const loadingEl = document.getElementById('loading');
    const errorEl = document.getElementById('error');

    const MIN_YEAR = 2000;
    const MAX_YEAR = new Date().getFullYear();

    async function init() {
        rangeMin.min = MIN_YEAR;
        rangeMin.max = MAX_YEAR;
        rangeMax.min = MIN_YEAR;
        rangeMax.max = MAX_YEAR;

        rangeMin.value = MAX_YEAR - 3;
        rangeMax.value = MAX_YEAR;
        State.setYearRange(MAX_YEAR - 3, MAX_YEAR);

        createTickMarks();
        updateSliderRange();
        await loadTickers();

        dropdown.addEventListener('change', onTickerChange);
        addTickerBtn.addEventListener('click', onAddTicker);
        customTickerInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') onAddTicker();
        });

        rangeMin.addEventListener('input', onRangeChange);
        rangeMax.addEventListener('input', onRangeChange);
        rangeMin.addEventListener('change', onRangeChangeEnd);
        rangeMax.addEventListener('change', onRangeChangeEnd);

        const sliderContainer = document.querySelector('.range-slider');
        sliderContainer.addEventListener('click', onSliderTrackClick);

        if (State.currentTicker) {
            await loadStockData();
        }
    }

    /** Tick marks for each year, labels every 5. */
    function createTickMarks() {
        rangeTicksContainer.innerHTML = '';
        const totalYears = MAX_YEAR - MIN_YEAR;

        for (let year = MIN_YEAR; year <= MAX_YEAR; year++) {
            const tick = document.createElement('div');
            tick.className = 'range-tick';

            const isMajor = year % 5 === 0;
            if (isMajor) {
                tick.classList.add('major');
            }

            const percent = ((year - MIN_YEAR) / totalYears) * 100;
            tick.style.left = `${percent}%`;

            const dot = document.createElement('div');
            dot.className = 'dot';
            tick.appendChild(dot);
            if (isMajor) {
                const label = document.createElement('span');
                label.className = 'label';
                label.textContent = year;
                tick.appendChild(label);
            }

            rangeTicksContainer.appendChild(tick);
        }
    }

    function updateSliderRange() {
        const min = parseInt(rangeMin.value);
        const max = parseInt(rangeMax.value);
        const totalRange = MAX_YEAR - MIN_YEAR;

        const minPercent = ((min - MIN_YEAR) / totalRange) * 100;
        const maxPercent = ((max - MIN_YEAR) / totalRange) * 100;

        sliderRange.style.left = `${minPercent}%`;
        sliderRange.style.width = `${maxPercent - minPercent}%`;
    }

    /** Click on track moves whichever handle is closer. */
    function onSliderTrackClick(e) {
        const rect = e.currentTarget.getBoundingClientRect();
        const clickPercent = (e.clientX - rect.left) / rect.width;
        const clickYear = Math.round(MIN_YEAR + clickPercent * (MAX_YEAR - MIN_YEAR));

        const minVal = parseInt(rangeMin.value);
        const maxVal = parseInt(rangeMax.value);

        const distToMin = Math.abs(clickYear - minVal);
        const distToMax = Math.abs(clickYear - maxVal);

        if (distToMin <= distToMax) {
            rangeMin.value = Math.min(clickYear, maxVal);
        } else {
            rangeMax.value = Math.max(clickYear, minVal);
        }

        updateSliderRange();
        onRangeChangeEnd();
    }

    /** Fires continuously while dragging — prevents handles from crossing. */
    function onRangeChange() {
        let min = parseInt(rangeMin.value);
        let max = parseInt(rangeMax.value);

        if (min > max) {
            if (this === rangeMin) {
                rangeMin.value = max;
                min = max;
            } else {
                rangeMax.value = min;
                max = min;
            }
        }

        updateSliderRange();
    }

    /** Fires on mouseup — commits range and re-renders charts. */
    function onRangeChangeEnd() {
        const min = parseInt(rangeMin.value);
        const max = parseInt(rangeMax.value);

        State.setYearRange(min, max);

        if (State.stockData) {
            Charts.renderAll(State.stockData, min, max);
        }
    }

    async function loadTickers() {
        try {
            const tickers = await API.getTickers();
            State.setTickers(tickers);
            populateDropdown();
        } catch (error) {
            console.error('Failed to load tickers:', error);
            State.setTickers(['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']);
            populateDropdown();
        }
    }

    function populateDropdown() {
        dropdown.innerHTML = State.tickers.map(ticker =>
            `<option value="${ticker}" ${ticker === State.currentTicker ? 'selected' : ''}>${ticker}</option>`
        ).join('');
    }

    async function onTickerChange() {
        State.setCurrentTicker(dropdown.value);
        await loadStockData();
    }

    async function onAddTicker() {
        const ticker = customTickerInput.value.trim().toUpperCase();
        if (!ticker) return;

        if (!/^[A-Z0-9\-\.]{1,10}$/.test(ticker)) {
            showError('Invalid ticker format');
            return;
        }

        addTickerBtn.disabled = true;

        try {
            await API.addTicker(ticker);
            State.addTicker(ticker);
            State.setCurrentTicker(ticker);
            populateDropdown();
            dropdown.value = ticker;
            customTickerInput.value = '';
            await loadStockData();
        } catch (error) {
            showError(`Failed to add ticker: ${error.message}`);
        } finally {
            addTickerBtn.disabled = false;
        }
    }

    async function loadStockData() {
        if (State.isLoading) return;

        const ticker = State.currentTicker;
        if (!ticker) return;

        State.setLoading(true);
        showLoading(true);
        hideError();

        try {
            // Fetch full range, year filtering happens client-side
            const data = await API.fetchStock(ticker, MIN_YEAR, MAX_YEAR);

            State.setStockData(data);
            Charts.renderAll(data, State.startYear, State.endYear);

        } catch (error) {
            console.error('Failed to load stock data:', error);
            showError(error.message);
            Charts.showError(error.message);
        } finally {
            State.setLoading(false);
            showLoading(false);
        }
    }

    function showLoading(show) {
        loadingEl.classList.toggle('hidden', !show);
    }

    function showError(message) {
        errorEl.textContent = message;
        errorEl.classList.remove('hidden');
    }

    function hideError() {
        errorEl.classList.add('hidden');
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
