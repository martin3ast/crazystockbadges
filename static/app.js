// Crazy Stock Badges - Frontend JavaScript

class BadgeGenerator {
    constructor() {
        this.currentSessionId = null;
        this.progressInterval = null;
        this.fitnessChart = null;
        this.threejsViewer = null;
        
        this.initializeEventListeners();
        this.initializeTickerSuggestions();
    }
    
    initializeEventListeners() {
        // Form submission
        const form = document.getElementById('badge-form');
        form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        
        // Tab switching
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });
        
        // Download buttons
        document.getElementById('download-scad').addEventListener('click', () => {
            this.downloadFile('scad');
        });
        
        document.getElementById('download-stl').addEventListener('click', () => {
            this.downloadFile('stl');
        });
        
        document.getElementById('download-report').addEventListener('click', () => {
            this.downloadFile('report');
        });
    }
    
    initializeTickerSuggestions() {
        const tickerInput = document.getElementById('ticker');
        const suggestions = document.getElementById('ticker-suggestions');
        
        // Show suggestions on focus
        tickerInput.addEventListener('focus', () => {
            suggestions.classList.add('show');
        });
        
        // Hide suggestions on blur (with delay for clicks)
        tickerInput.addEventListener('blur', () => {
            setTimeout(() => {
                suggestions.classList.remove('show');
            }, 200);
        });
        
        // Filter suggestions on input
        tickerInput.addEventListener('input', (e) => {
            this.filterSuggestions(e.target.value);
        });
        
        // Handle suggestion clicks
        document.querySelectorAll('.suggestion-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const ticker = e.target.dataset.ticker;
                tickerInput.value = ticker;
                suggestions.classList.remove('show');
                tickerInput.focus();
            });
        });
    }
    
    filterSuggestions(query) {
        const suggestions = document.querySelectorAll('.suggestion-item');
        const searchTerm = query.toLowerCase();
        
        suggestions.forEach(item => {
            const text = item.textContent.toLowerCase();
            if (text.includes(searchTerm)) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    }
    
    async handleFormSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const data = {
            ticker: formData.get('ticker').toUpperCase(),
            period: formData.get('period'),
            generations: parseInt(formData.get('generations'))
        };
        
        // Basic length validation only - let server handle format validation
        if (data.ticker.length === 0 || data.ticker.length > 15) {
            this.showError('Please enter a ticker symbol (1-15 characters)');
            return;
        }
        
        try {
            // Validate ticker with server
            const validationResponse = await fetch('/api/validate-ticker', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ticker: data.ticker})
            });
            
            const validationResult = await validationResponse.json();
            
            if (!validationResult.valid) {
                this.showError(validationResult.error || 'Invalid ticker symbol');
                return;
            }
            
            // Show company name if available
            if (validationResult.name && validationResult.name !== data.ticker) {
                this.showSuccess(`Found: ${validationResult.name} (${data.ticker})`);
            }
            
            await this.startGeneration(data);
        } catch (error) {
            this.showError('Failed to start generation: ' + error.message);
        }
    }
    
    async startGeneration(data) {
        // Update UI
        this.showSection('progress-section');
        this.hideSection('results-section');
        this.disableForm();
        
        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            this.currentSessionId = result.session_id;
            
            // Start progress monitoring
            this.startProgressMonitoring();
            
        } catch (error) {
            this.enableForm();
            throw error;
        }
    }
    
    startProgressMonitoring() {
        this.progressInterval = setInterval(async () => {
            try {
                await this.updateProgress();
            } catch (error) {
                console.error('Progress update failed:', error);
                this.stopProgressMonitoring();
                this.showError('Lost connection to server');
            }
        }, 1000);
    }
    
    stopProgressMonitoring() {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
    }
    
    async updateProgress() {
        if (!this.currentSessionId) return;
        
        const response = await fetch(`/api/progress/${this.currentSessionId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Update progress bar
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');
        const statusText = document.getElementById('status-text');
        const generationInfo = document.getElementById('generation-info');
        
        progressFill.style.width = `${data.progress}%`;
        progressText.textContent = `${data.progress}%`;
        statusText.textContent = this.getStatusText(data.status);
        
        if (data.current_generation > 0) {
            generationInfo.textContent = `Generation ${data.current_generation} of ${data.total_generations}`;
        }
        
        // Update fitness chart if data available
        if (data.fitness_stats && data.fitness_stats.generation.length > 0) {
            this.updateFitnessChart(data.fitness_stats);
        }
        
        // Handle completion or error
        if (data.status === 'completed') {
            this.stopProgressMonitoring();
            this.onGenerationComplete();
        } else if (data.status === 'error') {
            this.stopProgressMonitoring();
            this.showError(data.error || 'Generation failed');
            this.enableForm();
        }
    }
    
    getStatusText(status) {
        const statusMap = {
            'initializing': 'Initializing...',
            'fetching_data': 'Fetching stock data...',
            'generating_report': 'Generating stock report...',
            'running_genetic_algorithm': 'Running genetic algorithm...',
            'completed': 'Generation completed!',
            'error': 'Error occurred'
        };
        
        return statusMap[status] || status;
    }
    
    async onGenerationComplete() {
        this.enableForm();
        this.showSection('results-section');
        
        // Load results
        await this.loadResults();
        
        // Initialize 3D viewer
        await this.initialize3DViewer();
        
        // Show success message
        this.showSuccess('Badge generation completed successfully!');
    }
    
    async loadResults() {
        if (!this.currentSessionId) return;
        
        try {
            const response = await fetch(`/api/report/${this.currentSessionId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Populate report tab
            document.getElementById('stock-report').textContent = data.report || 'No report available';
            
            // Populate sentiment tab
            this.populateSentimentData(data.sentiment);
            
            // Populate stats tab
            this.populateStatsData(data.stats);
            
        } catch (error) {
            console.error('Failed to load results:', error);
            this.showError('Failed to load results');
        }
    }
    
    populateSentimentData(sentiment) {
        const container = document.getElementById('sentiment-analysis');
        container.innerHTML = '';
        
        if (!sentiment || Object.keys(sentiment).length === 0) {
            container.innerHTML = '<p>No sentiment analysis available</p>';
            return;
        }
        
        // Create main sentiment visualization container
        const vizContainer = document.createElement('div');
        vizContainer.className = 'sentiment-viz-container';
        
        // Overall sentiment gauge
        this.createSentimentGauge(sentiment, vizContainer);
        
        // Individual metrics with visual indicators
        this.createSentimentMetrics(sentiment, vizContainer);
        
        // Word cloud or key insights
        this.createSentimentInsights(sentiment, vizContainer);
        
        container.appendChild(vizContainer);
    }
    
    createSentimentGauge(sentiment, container) {
        // Calculate overall sentiment score
        let overallScore = 0;
        let scoreCount = 0;
        
        Object.entries(sentiment).forEach(([key, value]) => {
            if (typeof value === 'number' && value >= -1 && value <= 1) {
                overallScore += value;
                scoreCount++;
            }
        });
        
        if (scoreCount > 0) {
            overallScore = overallScore / scoreCount;
        }
        
        const gaugeContainer = document.createElement('div');
        gaugeContainer.className = 'sentiment-gauge-container';
        
        const gaugeTitle = document.createElement('h3');
        gaugeTitle.textContent = 'Overall Sentiment';
        gaugeTitle.className = 'sentiment-gauge-title';
        
        const gauge = document.createElement('div');
        gauge.className = 'sentiment-gauge';
        
        const needle = document.createElement('div');
        needle.className = 'sentiment-needle';
        
        const scoreText = document.createElement('div');
        scoreText.className = 'sentiment-score-text';
        scoreText.textContent = overallScore.toFixed(3);
        
        const label = document.createElement('div');
        label.className = 'sentiment-label';
        label.textContent = this.getSentimentLabel(overallScore);
        
        gauge.appendChild(needle);
        gaugeContainer.appendChild(gaugeTitle);
        gaugeContainer.appendChild(gauge);
        gaugeContainer.appendChild(scoreText);
        gaugeContainer.appendChild(label);
        
        container.appendChild(gaugeContainer);
        
        // Animate needle
        setTimeout(() => {
            const rotation = (overallScore + 1) * 90; // -1 to 1 maps to 0 to 180 degrees
            needle.style.transform = `rotate(${rotation}deg)`;
        }, 500);
    }
    
    createSentimentMetrics(sentiment, container) {
        const metricsContainer = document.createElement('div');
        metricsContainer.className = 'sentiment-metrics-container';
        
        Object.entries(sentiment).forEach(([key, value]) => {
            const metric = document.createElement('div');
            metric.className = 'sentiment-metric';
            
            const label = document.createElement('div');
            label.className = 'sentiment-metric-label';
            label.textContent = this.formatLabel(key);
            
            const valueContainer = document.createElement('div');
            valueContainer.className = 'sentiment-metric-value';
            
            if (typeof value === 'number') {
                // Create animated progress bar for numeric values
                const progressBar = document.createElement('div');
                progressBar.className = 'sentiment-progress-bar';
                
                const progressFill = document.createElement('div');
                progressFill.className = 'sentiment-progress-fill';
                
                const valueText = document.createElement('span');
                valueText.className = 'sentiment-progress-text';
                valueText.textContent = value.toFixed(3);
                
                progressBar.appendChild(progressFill);
                valueContainer.appendChild(progressBar);
                valueContainer.appendChild(valueText);
                
                // Animate progress bar
                setTimeout(() => {
                    let fillWidth;
                    let fillColor;
                    
                    if (value >= -1 && value <= 1) {
                        // Sentiment score (-1 to 1)
                        fillWidth = ((value + 1) / 2) * 100;
                        fillColor = value > 0.1 ? '#68d391' : value < -0.1 ? '#fc8181' : '#f1c40f';
                    } else {
                        // Other numeric values
                        fillWidth = Math.min(Math.abs(value) * 100, 100);
                        fillColor = '#667eea';
                    }
                    
                    progressFill.style.width = `${fillWidth}%`;
                    progressFill.style.backgroundColor = fillColor;
                }, 600 + Math.random() * 400);
                
            } else if (typeof value === 'object') {
                // Create a mini chart for object values
                const objectViz = document.createElement('div');
                objectViz.className = 'sentiment-object-viz';
                
                if (Array.isArray(value)) {
                    // Handle arrays - show first few items
                    if (value.length === 0) {
                        objectViz.innerHTML = `<div class="sentiment-array-count">Empty array</div>`;
                    } else {
                        const maxItems = 5;
                        value.slice(0, maxItems).forEach((item, index) => {
                            const itemDiv = document.createElement('div');
                            itemDiv.className = 'sentiment-object-item';
                            let displayValue = String(item);
                            if (displayValue.length > 40) {
                                displayValue = displayValue.substring(0, 37) + '...';
                            }
                            itemDiv.innerHTML = `<span class="key">${index + 1}:</span> <span class="value">${displayValue}</span>`;
                            objectViz.appendChild(itemDiv);
                        });
                        if (value.length > maxItems) {
                            const more = document.createElement('div');
                            more.className = 'sentiment-more';
                            more.textContent = `+${value.length - maxItems} more items (${value.length} total)`;
                            objectViz.appendChild(more);
                        }
                    }
                } else {
                    const entries = Object.entries(value);
                    const maxEntries = 5;
                    entries.slice(0, maxEntries).forEach(([k, v]) => {
                        const item = document.createElement('div');
                        item.className = 'sentiment-object-item';
                        let displayKey = String(k);
                        let displayValue = String(v);
                        
                        // Truncate long keys and values
                        if (displayKey.length > 20) {
                            displayKey = displayKey.substring(0, 17) + '...';
                        }
                        if (displayValue.length > 30) {
                            displayValue = displayValue.substring(0, 27) + '...';
                        }
                        
                        item.innerHTML = `<span class="key">${displayKey}:</span> <span class="value">${displayValue}</span>`;
                        objectViz.appendChild(item);
                    });
                    if (entries.length > maxEntries) {
                        const more = document.createElement('div');
                        more.className = 'sentiment-more';
                        more.textContent = `+${entries.length - maxEntries} more (${entries.length} total)`;
                        objectViz.appendChild(more);
                    }
                }
                
                valueContainer.appendChild(objectViz);
            } else {
                // String values
                const textValue = document.createElement('div');
                textValue.className = 'sentiment-text-value';
                let displayText = String(value);
                // For very long strings, add line breaks at reasonable points
                if (displayText.length > 100) {
                    displayText = displayText.replace(/(.{50,80}\s)/g, '$1\n');
                }
                textValue.textContent = displayText;
                valueContainer.appendChild(textValue);
            }
            
            metric.appendChild(label);
            metric.appendChild(valueContainer);
            metricsContainer.appendChild(metric);
        });
        
        container.appendChild(metricsContainer);
    }
    
    createSentimentInsights(sentiment, container) {
        const insightsContainer = document.createElement('div');
        insightsContainer.className = 'sentiment-insights-container';
        
        const title = document.createElement('h4');
        title.textContent = '📊 Sentiment Insights';
        title.className = 'sentiment-insights-title';
        
        const insights = document.createElement('div');
        insights.className = 'sentiment-insights';
        
        // Generate insights based on sentiment data
        const insightItems = this.generateSentimentInsights(sentiment);
        insightItems.forEach(insight => {
            const item = document.createElement('div');
            item.className = 'sentiment-insight-item';
            item.innerHTML = `
                <div class="insight-icon">${insight.icon}</div>
                <div class="insight-text">${insight.text}</div>
            `;
            insights.appendChild(item);
        });
        
        insightsContainer.appendChild(title);
        insightsContainer.appendChild(insights);
        container.appendChild(insightsContainer);
    }
    
    getSentimentLabel(score) {
        if (score > 0.3) return '😊 Very Positive';
        if (score > 0.1) return '🙂 Positive';
        if (score > -0.1) return '😐 Neutral';
        if (score > -0.3) return '😕 Negative';
        return '😢 Very Negative';
    }
    
    generateSentimentInsights(sentiment) {
        const insights = [];
        
        // Analyze sentiment data to generate insights
        Object.entries(sentiment).forEach(([key, value]) => {
            if (typeof value === 'number') {
                if (key.toLowerCase().includes('positive') && value > 0.5) {
                    insights.push({
                        icon: '📈',
                        text: `Strong positive sentiment detected (${value.toFixed(2)})`
                    });
                } else if (key.toLowerCase().includes('negative') && value > 0.5) {
                    insights.push({
                        icon: '📉',
                        text: `High negative sentiment present (${value.toFixed(2)})`
                    });
                } else if (key.toLowerCase().includes('neutral') && value > 0.5) {
                    insights.push({
                        icon: '⚖️',
                        text: `Predominantly neutral sentiment (${value.toFixed(2)})`
                    });
                }
            }
        });
        
        if (insights.length === 0) {
            insights.push({
                icon: '🔍',
                text: 'Sentiment analysis completed - review metrics above for details'
            });
        }
        
        return insights;
    }
    
    populateStatsData(stats) {
        const container = document.getElementById('market-stats');
        container.innerHTML = '';
        
        console.log('Market stats data received:', stats);
        
        if (!stats || Object.keys(stats).length === 0) {
            container.innerHTML = '<div class="stats-error">📊 No market statistics available</div>';
            return;
        }
        
        // Create comprehensive market stats display
        const statsHTML = `
            <div class="market-stats-container">
                ${this.createPriceActionSection(stats)}
                ${this.createTechnicalIndicatorsSection(stats)}
                ${this.createTradingSignalsSection(stats)}
                ${this.createVolumeSection(stats)}
            </div>
        `;
        
        container.innerHTML = statsHTML;
    }
    
    createPriceActionSection(stats) {
        const priceChangeClass = stats.price_change_pct >= 0 ? 'positive' : 'negative';
        const priceChangeIcon = stats.price_change_pct >= 0 ? '📈' : '📉';
        const trendIcon = this.getTrendIcon(stats.overall_trend);
        
        return `
            <div class="stats-section">
                <h3>💰 Price Action</h3>
                <div class="stats-grid">
                    <div class="stat-card primary">
                        <div class="stat-label">Current Price</div>
                        <div class="stat-value">$${this.formatNumber(stats.latest_price, 2)}</div>
                        <div class="stat-change ${priceChangeClass}">
                            ${priceChangeIcon} ${this.formatNumber(stats.price_change_pct, 2)}%
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">High</div>
                        <div class="stat-value">$${this.formatNumber(stats.high, 2)}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Low</div>
                        <div class="stat-value">$${this.formatNumber(stats.low, 2)}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Volatility</div>
                        <div class="stat-value">${this.formatNumber(stats.volatility_pct, 1)}%</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Overall Trend</div>
                        <div class="stat-value trend-${stats.overall_trend?.toLowerCase()}">${trendIcon} ${stats.overall_trend || 'N/A'}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Support</div>
                        <div class="stat-value">$${this.formatNumber(stats.support_level, 2)}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Resistance</div>
                        <div class="stat-value">$${this.formatNumber(stats.resistance_level, 2)}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Price Position</div>
                        <div class="stat-value">${this.formatNumber(stats.price_position, 1)}%</div>
                        <div class="position-bar">
                            <div class="position-fill" style="width: ${stats.price_position}%"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    createTechnicalIndicatorsSection(stats) {
        return `
            <div class="stats-section">
                <h3>📊 Technical Indicators</h3>
                <div class="stats-grid">
                    ${this.createRSICard(stats)}
                    ${this.createMACDCard(stats)}
                    ${this.createMovingAveragesCard(stats)}
                    ${this.createBollingerBandsCard(stats)}
                </div>
            </div>
        `;
    }
    
    createRSICard(stats) {
        if (!stats.rsi) return '';
        
        const rsiColor = this.getRSIColor(stats.rsi);
        const rsiIcon = this.getRSIIcon(stats.rsi_signal);
        
        return `
            <div class="stat-card indicator-card">
                <div class="stat-label">RSI (14)</div>
                <div class="stat-value ${rsiColor}">${this.formatNumber(stats.rsi, 1)}</div>
                <div class="stat-signal ${stats.rsi_signal?.toLowerCase()}">${rsiIcon} ${stats.rsi_signal}</div>
                <div class="rsi-bar">
                    <div class="rsi-fill ${rsiColor}" style="width: ${stats.rsi}%"></div>
                    <div class="rsi-zones">
                        <span class="oversold-line" style="left: 30%"></span>
                        <span class="overbought-line" style="left: 70%"></span>
                    </div>
                </div>
            </div>
        `;
    }
    
    createMACDCard(stats) {
        if (!stats.macd) return '';
        
        const macdSignal = stats.macd_signal || 'Neutral';  // This is the "Bullish"/"Bearish" string
        const macdSignalLine = stats.macd_signal_line;  // This is the numeric MACD signal line value
        const macdColor = macdSignal === 'Bullish' ? 'positive' : 'negative';
        const macdIcon = macdSignal === 'Bullish' ? '🟢' : '🔴';
        
        return `
            <div class="stat-card indicator-card">
                <div class="stat-label">MACD</div>
                <div class="stat-value">${this.formatNumber(stats.macd, 3)}</div>
                <div class="stat-signal ${macdColor}">${macdIcon} ${macdSignal}</div>
                <div class="macd-details">
                    <small>Signal: ${this.formatNumber(macdSignalLine, 3)}</small>
                    <small>Hist: ${this.formatNumber(stats.macd_histogram, 3)}</small>
                </div>
            </div>
        `;
    }
    
    createMovingAveragesCard(stats) {
        const ma20Color = stats.price_vs_sma20 >= 0 ? 'positive' : 'negative';
        const ma50Color = stats.price_vs_sma50 >= 0 ? 'positive' : 'negative';
        const trendIcon = this.getTrendIcon(stats.ma_trend);
        
        return `
            <div class="stat-card indicator-card">
                <div class="stat-label">Moving Averages</div>
                <div class="ma-grid">
                    <div class="ma-item">
                        <span>SMA 20:</span>
                        <span class="${ma20Color}">$${this.formatNumber(stats.sma_20, 2)}</span>
                        <small class="${ma20Color}">(${this.formatNumber(stats.price_vs_sma20, 1)}%)</small>
                    </div>
                    <div class="ma-item">
                        <span>SMA 50:</span>
                        <span class="${ma50Color}">$${this.formatNumber(stats.sma_50, 2)}</span>
                        <small class="${ma50Color}">(${this.formatNumber(stats.price_vs_sma50, 1)}%)</small>
                    </div>
                    <div class="ma-item">
                        <span>EMA 20:</span>
                        <span>$${this.formatNumber(stats.ema_20, 2)}</span>
                    </div>
                </div>
                <div class="stat-signal trend-${stats.ma_trend?.toLowerCase()}">${trendIcon} ${stats.ma_trend}</div>
            </div>
        `;
    }
    
    createBollingerBandsCard(stats) {
        if (!stats.bb_upper) return '';
        
        const bbPosition = stats.bb_position || 50;
        const bbColor = bbPosition > 80 ? 'negative' : bbPosition < 20 ? 'positive' : 'neutral';
        
        return `
            <div class="stat-card indicator-card">
                <div class="stat-label">Bollinger Bands</div>
                <div class="bb-grid">
                    <div class="bb-item">
                        <span>Upper:</span>
                        <span>$${this.formatNumber(stats.bb_upper, 2)}</span>
                    </div>
                    <div class="bb-item">
                        <span>Middle:</span>
                        <span>$${this.formatNumber(stats.bb_middle, 2)}</span>
                    </div>
                    <div class="bb-item">
                        <span>Lower:</span>
                        <span>$${this.formatNumber(stats.bb_lower, 2)}</span>
                    </div>
                </div>
                <div class="bb-position">
                    <span>Position: </span>
                    <span class="${bbColor}">${this.formatNumber(bbPosition, 1)}%</span>
                </div>
                <div class="bb-bar">
                    <div class="bb-fill" style="width: ${bbPosition}%"></div>
                </div>
            </div>
        `;
    }
    
    createTradingSignalsSection(stats) {
        const overallSignal = this.calculateOverallSignal(stats);
        const signalColor = overallSignal.type === 'BUY' ? 'buy-signal' : 
                           overallSignal.type === 'SELL' ? 'sell-signal' : 'hold-signal';
        
        return `
            <div class="stats-section">
                <h3>🎯 Trading Signals</h3>
                <div class="trading-signals">
                    <div class="overall-signal ${signalColor}">
                        <div class="signal-icon">${overallSignal.icon}</div>
                        <div class="signal-content">
                            <div class="signal-type">${overallSignal.type}</div>
                            <div class="signal-strength">${overallSignal.strength}</div>
                            <div class="signal-desc">${overallSignal.description}</div>
                        </div>
                    </div>
                    
                    <div class="signal-breakdown">
                        <div class="signal-item">
                            <span class="signal-name">RSI Signal:</span>
                            <span class="signal-value ${stats.rsi_signal?.toLowerCase()}">${stats.rsi_signal}</span>
                        </div>
                        <div class="signal-item">
                            <span class="signal-name">MACD Signal:</span>
                            <span class="signal-value ${stats.macd_signal?.toLowerCase()}">${stats.macd_signal}</span>
                        </div>
                        <div class="signal-item">
                            <span class="signal-name">MA Trend:</span>
                            <span class="signal-value ${stats.ma_trend?.toLowerCase()}">${stats.ma_trend}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    createVolumeSection(stats) {
        if (!stats.latest_volume) return '';
        
        const volumeRatio = stats.volume_avg ? (stats.latest_volume / stats.volume_avg) : 1;
        const volumeColor = volumeRatio > 1.5 ? 'high-volume' : volumeRatio < 0.5 ? 'low-volume' : 'normal-volume';
        
        return `
            <div class="stats-section">
                <h3>📊 Volume Analysis</h3>
                <div class="volume-stats">
                    <div class="volume-card">
                        <div class="stat-label">Latest Volume</div>
                        <div class="stat-value">${this.formatVolume(stats.latest_volume)}</div>
                    </div>
                    <div class="volume-card">
                        <div class="stat-label">Average Volume</div>
                        <div class="stat-value">${this.formatVolume(stats.volume_avg)}</div>
                    </div>
                    <div class="volume-card">
                        <div class="stat-label">Volume Ratio</div>
                        <div class="stat-value ${volumeColor}">${this.formatNumber(volumeRatio, 2)}x</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Helper functions for formatting and indicators
    formatNumber(value, decimals = 2) {
        if (value === null || value === undefined) return 'N/A';
        return Number(value).toFixed(decimals);
    }
    
    formatVolume(volume) {
        if (!volume) return 'N/A';
        if (volume >= 1e9) return (volume / 1e9).toFixed(1) + 'B';
        if (volume >= 1e6) return (volume / 1e6).toFixed(1) + 'M';
        if (volume >= 1e3) return (volume / 1e3).toFixed(1) + 'K';
        return volume.toLocaleString();
    }
    
    getTrendIcon(trend) {
        switch(trend?.toLowerCase()) {
            case 'bullish': return '🟢 ↗️';
            case 'bearish': return '🔴 ↘️';
            case 'mixed': return '🟡 ↔️';
            default: return '⚪ ➡️';
        }
    }
    
    getRSIColor(rsi) {
        if (rsi > 70) return 'overbought';
        if (rsi < 30) return 'oversold';
        if (rsi > 60) return 'bullish';
        if (rsi < 40) return 'bearish';
        return 'neutral';
    }
    
    getRSIIcon(signal) {
        switch(signal?.toLowerCase()) {
            case 'overbought': return '🔴';
            case 'oversold': return '🟢';
            case 'bullish': return '🟢';
            case 'bearish': return '🔴';
            default: return '🟡';
        }
    }
    
    calculateOverallSignal(stats) {
        let bullishSignals = 0;
        let bearishSignals = 0;
        
        // Count signals
        if (stats.rsi_signal === 'Bullish' || stats.rsi_signal === 'Oversold') bullishSignals++;
        if (stats.rsi_signal === 'Bearish' || stats.rsi_signal === 'Overbought') bearishSignals++;
        
        if (stats.macd_signal === 'Bullish') bullishSignals++;
        if (stats.macd_signal === 'Bearish') bearishSignals++;
        
        if (stats.ma_trend === 'Bullish') bullishSignals++;
        if (stats.ma_trend === 'Bearish') bearishSignals++;
        
        if (stats.overall_trend === 'Bullish') bullishSignals++;
        if (stats.overall_trend === 'Bearish') bearishSignals++;
        
        // Determine overall signal
        if (bullishSignals >= 3) {
            return {
                type: 'BUY',
                strength: bullishSignals >= 4 ? 'Strong' : 'Moderate',
                icon: '🟢',
                description: 'Multiple indicators suggest upward momentum'
            };
        } else if (bearishSignals >= 3) {
            return {
                type: 'SELL',
                strength: bearishSignals >= 4 ? 'Strong' : 'Moderate',
                icon: '🔴',
                description: 'Multiple indicators suggest downward pressure'
            };
        } else {
            return {
                type: 'HOLD',
                strength: 'Mixed',
                icon: '🟡',
                description: 'Mixed signals, consider waiting for clearer trend'
            };
        }
    }
    
    formatLabel(key) {
        return key.replace(/_/g, ' ')
                 .replace(/\b\w/g, l => l.toUpperCase());
    }
    
    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');
    }
    
    updateFitnessChart(fitnessStats) {
        const chartContainer = document.getElementById('fitness-chart-container');
        const canvas = document.getElementById('fitness-chart');
        
        if (!this.fitnessChart) {
            chartContainer.style.display = 'block';
            
            const ctx = canvas.getContext('2d');
            this.fitnessChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: fitnessStats.generation,
                    datasets: [
                        {
                            label: 'Best Fitness',
                            data: fitnessStats.best,
                            borderColor: '#48bb78',
                            backgroundColor: 'rgba(72, 187, 120, 0.1)',
                            tension: 0.4
                        },
                        {
                            label: 'Mean Fitness',
                            data: fitnessStats.mean,
                            borderColor: '#667eea',
                            backgroundColor: 'rgba(102, 126, 234, 0.1)',
                            tension: 0.4
                        },
                        {
                            label: 'Max Fitness',
                            data: fitnessStats.max,
                            borderColor: '#ed8936',
                            backgroundColor: 'rgba(237, 137, 54, 0.1)',
                            tension: 0.4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Genetic Algorithm Fitness Evolution'
                        },
                        legend: {
                            position: 'top'
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Generation'
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Fitness Score'
                            }
                        }
                    }
                }
            });
        } else {
            // Update existing chart
            this.fitnessChart.data.labels = fitnessStats.generation;
            this.fitnessChart.data.datasets[0].data = fitnessStats.best;
            this.fitnessChart.data.datasets[1].data = fitnessStats.mean;
            this.fitnessChart.data.datasets[2].data = fitnessStats.max;
            this.fitnessChart.update();
        }
    }
    
    async downloadFile(fileType) {
        if (!this.currentSessionId) {
            this.showError('No active session');
            return;
        }
        
        try {
            const response = await fetch(`/api/download/${this.currentSessionId}/${fileType}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = response.headers.get('Content-Disposition')?.split('filename=')[1] || `file.${fileType}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
        } catch (error) {
            console.error('Download failed:', error);
            this.showError('Download failed: ' + error.message);
        }
    }
    
    showSection(sectionId) {
        document.getElementById(sectionId).style.display = 'block';
    }
    
    hideSection(sectionId) {
        document.getElementById(sectionId).style.display = 'none';
    }
    
    disableForm() {
        document.getElementById('generate-btn').disabled = true;
        document.getElementById('generate-btn').innerHTML = '<div class="loading"></div> Generating...';
    }
    
    enableForm() {
        document.getElementById('generate-btn').disabled = false;
        document.getElementById('generate-btn').innerHTML = '🚀 Generate Badge';
    }
    
    showError(message) {
        this.showMessage(message, 'error');
    }
    
    showSuccess(message) {
        this.showMessage(message, 'success');
    }
    
    async initialize3DViewer() {
        const loadingEl = document.getElementById('loading-3d');
        
        // Show appropriate loading message
        loadingEl.innerHTML = `
            <div class="loading">⏳</div>
            <p>Generating 3D model... This may take up to 5 minutes.</p>
        `;
        
        // Start polling for STL availability
        this.pollForSTL();
    }
    
    async pollForSTL() {
        const maxPolls = 30; // Poll for up to 5 minutes (30 * 10 seconds)
        let pollCount = 0;
        
        const poll = async () => {
            try {
                const response = await fetch(`/api/stl-status/${this.currentSessionId}`);
                const data = await response.json();
                
                if (data.ready) {
                    // STL is ready, reload the 3D viewer
                    await this.load3DModel();
                    return;
                }
                
                pollCount++;
                if (pollCount < maxPolls) {
                    setTimeout(poll, 10000); // Poll every 10 seconds
                } else {
                    console.log('STL polling timeout');
                    const loadingEl = document.getElementById('loading-3d');
                    if (loadingEl) {
                        loadingEl.innerHTML = `
                            <div class="model-error">
                                <h4>⏱️ 3D Model Generation In Progress</h4>
                                <p>The model is still being generated in the background.<br>
                                You can download the SCAD file and convert it manually.</p>
                            </div>
                        `;
                    }
                }
            } catch (error) {
                console.error('Error polling for STL:', error);
            }
        };
        
        // Start polling after a short delay
        setTimeout(poll, 5000);
    }
    
    async load3DModel() {
        const container = document.getElementById('threejs-container');
        const loadingEl = document.getElementById('loading-3d');
        
        // Clean up existing viewer if any
        if (this.threejsViewer) {
            this.threejsViewer.cleanup();
        }
        
        try {
            // Create Three.js scene
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x0a1a2e);
            
            // Create camera
            const camera = new THREE.PerspectiveCamera(
                75,
                container.clientWidth / container.clientHeight,
                0.1,
                1000
            );
            
            // Create renderer
            const renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(container.clientWidth, container.clientHeight);
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            
            // Add enhanced lighting setup
            // Ambient light for overall illumination
            const ambientLight = new THREE.AmbientLight(0x404040, 0.8);
            scene.add(ambientLight);
            
            // Main directional light (key light)
            const directionalLight1 = new THREE.DirectionalLight(0xffffff, 1.8);
            directionalLight1.position.set(10, 10, 5);
            directionalLight1.castShadow = true;
            directionalLight1.shadow.mapSize.width = 2048;
            directionalLight1.shadow.mapSize.height = 2048;
            scene.add(directionalLight1);
            
            // Fill light from opposite side
            const directionalLight2 = new THREE.DirectionalLight(0xffffff, 1.2);
            directionalLight2.position.set(-10, 5, -5);
            scene.add(directionalLight2);
            
            // Top light for better detail visibility
            const directionalLight3 = new THREE.DirectionalLight(0xffffff, 1.4);
            directionalLight3.position.set(0, 15, 0);
            scene.add(directionalLight3);
            
            // Rim light for edge definition
            const directionalLight4 = new THREE.DirectionalLight(0xf1c40f, 0.6);
            directionalLight4.position.set(-5, -5, 10);
            scene.add(directionalLight4);
            
            // Add simple mouse controls (no OrbitControls dependency)
            let mouseX = 0, mouseY = 0;
            let isMouseDown = false;
            let rotationX = 0, rotationY = 0;
            let zoom = 1;
            let mesh = null;
            // Use global autorotate variables
            
            function addMouseControls(container) {
                let lastMouseX = 0, lastMouseY = 0;
                
                container.addEventListener('mousedown', function(event) {
                    isMouseDown = true;
                    lastMouseX = event.clientX;
                    lastMouseY = event.clientY;
                });
                
                container.addEventListener('mouseup', function() {
                    isMouseDown = false;
                });
                
                container.addEventListener('mousemove', function(event) {
                    if (isMouseDown) {
                        const deltaX = event.clientX - lastMouseX;
                        const deltaY = event.clientY - lastMouseY;
                        
                        rotationY += deltaX * 0.01;
                        rotationX += deltaY * 0.01;
                        
                        rotationX = Math.max(-Math.PI/2, Math.min(Math.PI/2, rotationX));
                        
                        lastMouseX = event.clientX;
                        lastMouseY = event.clientY;
                    }
                });
                
                container.addEventListener('wheel', function(event) {
                    event.preventDefault();
                    zoom += event.deltaY * -0.001;
                    zoom = Math.max(0.1, Math.min(5, zoom));
                });
            }
            
            function updateCamera() {
                if (mesh) {
                    // Auto-rotate when not manually controlling
                    if (globalAutoRotate && !isMouseDown) {
                        rotationY += globalAutoRotateSpeed;
                    }
                    
                    const distance = 150 / zoom;
                    camera.position.x = distance * Math.cos(rotationX) * Math.cos(rotationY);
                    camera.position.y = distance * Math.sin(rotationX);
                    camera.position.z = distance * Math.cos(rotationX) * Math.sin(rotationY);
                    camera.lookAt(0, 0, 0);
                }
            }
            
            addMouseControls(container);
            
            // Load STL model
            const modelUrl = `/api/model/${this.currentSessionId}`;
            console.log('Loading STL from:', modelUrl);
            
            fetch(modelUrl)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.arrayBuffer();
                })
                .then(buffer => {
                    console.log('STL file size:', buffer.byteLength, 'bytes');
                    
                    const geometry = this.parseSTL(buffer);
                    
                    // Create material with better lighting response
                    const material = new THREE.MeshPhongMaterial({
                        color: 0xf1c40f,
                        shininess: 30,
                        specular: 0x444444,
                        transparent: false,
                        opacity: 1.0,
                        flatShading: false
                    });
                    
                    // Create mesh
                    mesh = new THREE.Mesh(geometry, material);
                    mesh.castShadow = true;
                    mesh.receiveShadow = true;
                    
                    // Center the model
                    geometry.computeBoundingBox();
                    const box = geometry.boundingBox;
                    const center = box.getCenter(new THREE.Vector3());
                    geometry.translate(-center.x, -center.y, -center.z);
                    
                    // Scale to fit viewport
                    const size = box.getSize(new THREE.Vector3());
                    const maxDim = Math.max(size.x, size.y, size.z);
                    const scale = 100 / maxDim;
                    mesh.scale.setScalar(scale);
                    
                    scene.add(mesh);
                    
                    // Position camera
                    camera.position.set(50, 50, 50);
                    camera.lookAt(0, 0, 0);
                    
                    // Hide loading and show renderer
                    loadingEl.style.display = 'none';
                    container.appendChild(renderer.domElement);
                    
                    // Show autorotate button
                    const autoRotateBtn = document.getElementById('autorotate-btn');
                    if (autoRotateBtn) {
                        autoRotateBtn.style.display = 'inline-block';
                    }
                    
                    // Animation loop
                    const animate = () => {
                        requestAnimationFrame(animate);
                        updateCamera();
                        renderer.render(scene, camera);
                    };
                    animate();
                    
                    // Handle window resize
                    const handleResize = () => {
                        camera.aspect = container.clientWidth / container.clientHeight;
                        camera.updateProjectionMatrix();
                        renderer.setSize(container.clientWidth, container.clientHeight);
                    };
                    window.addEventListener('resize', handleResize);
                    
                    // Store for cleanup
                    this.threejsViewer = {
                        scene, camera, renderer, mesh,
                        cleanup: () => {
                            window.removeEventListener('resize', handleResize);
                            if (container.contains(renderer.domElement)) {
                                container.removeChild(renderer.domElement);
                            }
                            renderer.dispose();
                        }
                    };
                    
                    console.log('3D model loaded successfully');
                })
                .catch(error => {
                    console.error('Error loading STL model:', error);
                    loadingEl.innerHTML = `
                        <div class="model-error">
                            <h4>❌ 3D Model Not Available</h4>
                            <p>The 3D preview requires OpenSCAD to be installed.<br>
                            You can still download the SCAD file manually.</p>
                        </div>
                    `;
                });
            
        } catch (error) {
            console.error('Error loading 3D model:', error);
            loadingEl.innerHTML = `
                <div class="model-error">
                    <h4>❌ 3D Viewer Error</h4>
                    <p>Failed to initialize 3D viewer.<br>
                    Please try downloading the files instead.</p>
                </div>
            `;
        }
    }
    
    // STL parser for both ASCII and binary formats
    parseSTL(buffer) {
        // Convert buffer to string to check format
        const text = new TextDecoder().decode(buffer.slice(0, 1000));
        
        if (text.includes('solid')) {
            // ASCII format
            return this.parseASCIISTL(buffer);
        } else {
            // Binary format
            return this.parseBinarySTL(buffer);
        }
    }
    
    parseASCIISTL(buffer) {
        const text = new TextDecoder().decode(buffer);
        const lines = text.split('\n');
        
        const geometry = new THREE.BufferGeometry();
        const vertices = [];
        const normals = [];
        
        let currentNormal = [0, 0, 0];
        let vertexCount = 0;
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            
            if (line.startsWith('facet normal')) {
                // Parse normal: "facet normal 0 0 1"
                const parts = line.split(/\s+/);
                currentNormal = [
                    parseFloat(parts[2]),
                    parseFloat(parts[3]),
                    parseFloat(parts[4])
                ];
            } else if (line.startsWith('vertex')) {
                // Parse vertex: "vertex -55.1485 -23.8037 3.5"
                const parts = line.split(/\s+/);
                vertices.push(
                    parseFloat(parts[1]),
                    parseFloat(parts[2]),
                    parseFloat(parts[3])
                );
                normals.push(currentNormal[0], currentNormal[1], currentNormal[2]);
                vertexCount++;
            }
        }
        
        geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
        geometry.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
        
        console.log('Parsed ASCII STL:', vertexCount, 'vertices,', vertexCount / 3, 'triangles');
        return geometry;
    }
    
    parseBinarySTL(buffer) {
        const view = new DataView(buffer);
        
        // Skip header (80 bytes)
        let offset = 80;
        
        // Read number of triangles
        const triangles = view.getUint32(offset, true);
        offset += 4;
        
        const geometry = new THREE.BufferGeometry();
        const vertices = [];
        const normals = [];
        
        for (let i = 0; i < triangles; i++) {
            // Read normal (3 floats)
            const nx = view.getFloat32(offset, true); offset += 4;
            const ny = view.getFloat32(offset, true); offset += 4;
            const nz = view.getFloat32(offset, true); offset += 4;
            
            // Read vertices (3 vertices * 3 floats each)
            for (let j = 0; j < 3; j++) {
                const x = view.getFloat32(offset, true); offset += 4;
                const y = view.getFloat32(offset, true); offset += 4;
                const z = view.getFloat32(offset, true); offset += 4;
                
                vertices.push(x, y, z);
                normals.push(nx, ny, nz);
            }
            
            // Skip attribute byte count
            offset += 2;
        }
        
        geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
        geometry.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
        
        console.log('Parsed Binary STL:', triangles, 'triangles');
        return geometry;
    }
    
    showMessage(message, type = 'error') {
        // Remove existing messages
        document.querySelectorAll('.error, .success').forEach(el => el.remove());
        
        const messageEl = document.createElement('div');
        messageEl.className = type;
        messageEl.textContent = message;
        
        const container = document.querySelector('.container');
        container.insertBefore(messageEl, container.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (messageEl.parentNode) {
                messageEl.remove();
            }
        }, 5000);
    }
}

// Global variables for 3D viewer autorotate
let globalAutoRotate = true;
let globalAutoRotateSpeed = 0.005;

// Global function to toggle autorotate
function toggleAutoRotate() {
    globalAutoRotate = !globalAutoRotate;
    const btn = document.getElementById('autorotate-btn');
    if (btn) {
        if (globalAutoRotate) {
            btn.textContent = '⏸️ Pause Auto-Rotate';
        } else {
            btn.textContent = '▶️ Start Auto-Rotate';
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new BadgeGenerator();
});