// メインアプリケーション
class EnvironmentDashboard {
    constructor() {
        this.environments = [];
        this.healthStatus = new Map();
        this.isUpdating = false;
        this.updateInterval = null;
        this.expandedCards = new Set();
        
        // DOM要素の参照
        this.elements = {
            dashboard: null,
            lastUpdated: null,
            healthyCount: null,
            warningCount: null,
            errorCount: null
        };
    }

    // 初期化
    async initialize() {
        try {
            Logger.info('Initializing Environment Dashboard');
            
            // DOM要素の取得
            this.elements.dashboard = document.getElementById('dashboard');
            this.elements.lastUpdated = document.getElementById('lastUpdated');
            this.elements.healthyCount = document.getElementById('healthyCount');
            this.elements.warningCount = document.getElementById('warningCount');
            this.elements.errorCount = document.getElementById('errorCount');

            // イベントリスナーの設定
            this.setupEventListeners();

            // 初回データ読み込み
            await this.loadEnvironments();
            
            // ダッシュボード描画
            await this.renderDashboard();
            
            // 自動更新の開始
            this.startAutoUpdate();
            
            Logger.info('Dashboard initialization completed');
        } catch (error) {
            Logger.error('Failed to initialize dashboard:', error);
            this.showError('ダッシュボードの初期化に失敗しました');
        }
    }

    // イベントリスナーの設定
    setupEventListeners() {
        // キーボードショートカット
        document.addEventListener('keydown', (e) => {
            if (e.key === 'F5' || (e.ctrlKey && e.key === 'r')) {
                e.preventDefault();
                this.manualUpdate();
            }
        });

        // ウィンドウフォーカス時の更新
        window.addEventListener('focus', () => {
            this.manualUpdate();
        });
    }

    // 環境データの読み込み
    async loadEnvironments() {
        try {
            Logger.info('Loading environments data');
            
            // Wikiキャッシュからデータを取得
            const wikiCache = await api.getWikiCache();
            
            if (wikiCache.environments && wikiCache.environments.length > 0) {
                this.environments = wikiCache.environments.map(env => 
                    wikiParser.normalizeEnvironment(env)
                );
                Logger.info(`Loaded ${this.environments.length} environments from wiki cache`);
            } else {
                // フォールバック: 設定ファイルから読み込み
                const config = await api.getEnvironments();
                this.environments = config.environments || [];
                Logger.warn(`Fallback to config file. Loaded ${this.environments.length} environments`);
            }

            // ヘルスチェック実行
            await this.performHealthChecks();
            
        } catch (error) {
            Logger.error('Failed to load environments:', error);
            this.environments = [];
        }
    }

    // ヘルスチェック実行
    async performHealthChecks() {
        if (this.environments.length === 0) return;

        try {
            Logger.info('Performing health checks');
            
            // ヘルスチェックURL一覧を作成
            const healthCheckUrls = this.environments
                .filter(env => env.healthCheck)
                .map(env => env.healthCheck);

            // 並列でヘルスチェック実行
            const healthResults = await api.batchHealthCheck(healthCheckUrls);

            // 結果をマップに保存
            this.healthStatus.clear();
            healthResults.forEach(result => {
                const env = this.environments.find(e => e.healthCheck === result.url);
                if (env) {
                    this.healthStatus.set(env.id, result);
                }
            });

            // サービス別ヘルスチェック
            await this.performServiceHealthChecks();

            Logger.info('Health checks completed');
        } catch (error) {
            Logger.error('Health check failed:', error);
        }
    }

    // サービス別ヘルスチェック
    async performServiceHealthChecks() {
        for (const env of this.environments) {
            if (!env.services || env.services.length === 0) continue;

            try {
                const serviceUrls = env.services
                    .filter(service => service.url)
                    .map(service => service.url);

                if (serviceUrls.length > 0) {
                    const serviceResults = await api.batchHealthCheck(serviceUrls);
                    
                    // サービス結果を環境に反映
                    env.services.forEach(service => {
                        const result = serviceResults.find(r => r.url === service.url);
                        if (result) {
                            service.status = result.status;
                            service.responseTime = result.responseTime;
                        }
                    });
                }
            } catch (error) {
                Logger.warn(`Service health check failed for ${env.id}:`, error);
            }
        }
    }

    // ダッシュボード描画
    async renderDashboard() {
        if (!this.elements.dashboard) return;

        try {
            this.elements.dashboard.innerHTML = '';

            for (const env of this.environments) {
                const card = this.createEnvironmentCard(env);
                this.elements.dashboard.appendChild(card);
            }

            // 統計情報の更新
            this.updateStatusSummary();
            this.updateLastUpdatedTime();

        } catch (error) {
            Logger.error('Dashboard rendering failed:', error);
        }
    }

    // 環境カードの作成
    createEnvironmentCard(env) {
        const health = this.healthStatus.get(env.id);
        const status = health?.status || 'maintenance';
        const responseTime = health?.responseTime || '-';
        
        const card = document.createElement('div');
        card.className = `environment-card ${status}`;
        card.setAttribute('data-env-id', env.id);
        
        // 展開状態の復元
        if (this.expandedCards.has(env.id)) {
            card.classList.add('expanded');
        }

        // サービス統計
        const healthyServices = env.services?.filter(s => s.status === 'healthy').length || 0;
        const totalServices = env.services?.length || 0;

        card.innerHTML = `
            <div class="card-header">
                <h3 class="env-name">${this.escapeHtml(env.name)}</h3>
                <div class="status-indicator ${status}"></div>
            </div>
            <div class="card-summary">
                <div class="service-count">
                    ${healthyServices}/${totalServices} サービス
                </div>
                <div class="response-time">${this.formatResponseTime(responseTime)}</div>
            </div>
            <div class="card-footer">
                <div class="last-check">${this.formatTime(health?.timestamp)}</div>
                <div class="expand-icon">▼</div>
            </div>
            <div class="card-details">
                ${this.createCardDetails(env)}
            </div>
        `;

        // クリックイベント
        card.addEventListener('click', () => this.toggleEnvironmentDetails(env.id));

        return card;
    }

    // カード詳細の作成
    createCardDetails(env) {
        return `
            <div class="env-url">${this.escapeHtml(env.url)}</div>
            
            ${env.credentials?.username ? `
            <div class="detail-section">
                <div class="detail-label">ユーザー名</div>
                <div class="detail-value">
                    ${this.escapeHtml(env.credentials.username)}
                    <button class="copy-btn" onclick="event.stopPropagation(); dashboard.copyToClipboard('${this.escapeHtml(env.credentials.username)}')">コピー</button>
                </div>
            </div>` : ''}

            ${env.credentials?.password ? `
            <div class="detail-section">
                <div class="detail-label">パスワード</div>
                <div class="detail-value">
                    <span id="password-${env.id}">••••••••••</span>
                    <div>
                        <button class="copy-btn" onclick="event.stopPropagation(); dashboard.togglePassword('${env.id}', '${this.escapeHtml(env.credentials.password)}')">表示</button>
                        <button class="copy-btn" onclick="event.stopPropagation(); dashboard.copyToClipboard('${this.escapeHtml(env.credentials.password)}')">コピー</button>
                    </div>
                </div>
            </div>` : ''}

            ${env.description ? `
            <div class="detail-section">
                <div class="detail-label">説明</div>
                <div class="detail-value">${this.escapeHtml(env.description)}</div>
            </div>` : ''}

            ${env.access_notes ? `
            <div class="detail-section">
                <div class="detail-label">注意事項</div>
                <div class="detail-value">${this.escapeHtml(env.access_notes)}</div>
            </div>` : ''}

            ${env.services && env.services.length > 0 ? `
            <div class="detail-section">
                <div class="detail-label">サービス状況</div>
                <div class="services-list">
                    ${env.services.map(service => `
                        <div class="service-item ${service.status || 'unknown'}">
                            <div>${this.escapeHtml(service.name)}</div>
                            <div>${this.formatResponseTime(service.responseTime)}</div>
                        </div>
                    `).join('')}
                </div>
            </div>` : ''}
        `;
    }

    // 環境詳細の開閉
    toggleEnvironmentDetails(envId) {
        // 他のカードを閉じる
        this.expandedCards.forEach(id => {
            if (id !== envId) {
                const otherCard = document.querySelector(`[data-env-id="${id}"]`);
                if (otherCard) {
                    otherCard.classList.remove('expanded');
                }
            }
        });
        this.expandedCards.clear();

        // 該当カードを開閉
        const targetCard = document.querySelector(`[data-env-id="${envId}"]`);
        if (targetCard) {
            const isExpanded = targetCard.classList.contains('expanded');
            targetCard.classList.toggle('expanded');
            
            if (!isExpanded) {
                this.expandedCards.add(envId);
            }
        }
    }

    // クリップボードコピー
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showToast('クリップボードにコピーしました');
        } catch (error) {
            Logger.error('Clipboard copy failed:', error);
            this.showToast('コピーに失敗しました', 'error');
        }
    }

    // パスワード表示切り替え
    togglePassword(envId, password) {
        const passwordElement = document.getElementById(`password-${envId}`);
        const isHidden = passwordElement.textContent === '••••••••••';
        
        if (isHidden) {
            passwordElement.textContent = password;
            event.target.textContent = '隠す';
        } else {
            passwordElement.textContent = '••••••••••';
            event.target.textContent = '表示';
        }
    }

    // 統計情報の更新
    updateStatusSummary() {
        const counts = { healthy: 0, warning: 0, error: 0 };
        
        this.healthStatus.forEach(health => {
            counts[health.status] = (counts[health.status] || 0) + 1;
        });

        if (this.elements.healthyCount) this.elements.healthyCount.textContent = counts.healthy;
        if (this.elements.warningCount) this.elements.warningCount.textContent = counts.warning;
        if (this.elements.errorCount) this.elements.errorCount.textContent = counts.error;
    }

    // 最終更新時刻の更新
    updateLastUpdatedTime() {
        if (this.elements.lastUpdated) {
            const now = new Date();
            this.elements.lastUpdated.textContent = now.toLocaleString('ja-JP', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        }
    }

    // 自動更新の開始
    startAutoUpdate() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }

        this.updateInterval = setInterval(() => {
            this.updateData();
        }, Config.UPDATE_INTERVAL);

        Logger.info(`Auto-update started with interval: ${Config.UPDATE_INTERVAL}ms`);
    }

    // データ更新
    async updateData() {
        if (this.isUpdating) return;

        try {
            this.isUpdating = true;
            Logger.info('Updating dashboard data');

            await this.loadEnvironments();
            await this.renderDashboard();

        } catch (error) {
            Logger.error('Data update failed:', error);
        } finally {
            this.isUpdating = false;
        }
    }

    // 手動更新
    async manualUpdate() {
        api.clearCache();
        await this.updateData();
        this.showToast('手動更新しました');
    }

    // トースト通知
    showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'error' ? '#ff4757' : '#00ff88'};
            color: ${type === 'error' ? 'white' : 'black'};
            padding: 12px 20px;
            border-radius: 8px;
            font-weight: 600;
            z-index: 2000;
            animation: slideIn 0.3s ease;
        `;
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    // エラー表示
    showError(message) {
        this.showToast(message, 'error');
    }

    // ユーティリティメソッド
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatResponseTime(responseTime) {
        if (!responseTime || responseTime === '-') return '-';
        if (responseTime === 'timeout') return 'タイムアウト';
        if (responseTime === 'error') return 'エラー';
        if (typeof responseTime === 'number') return `${responseTime}ms`;
        return responseTime;
    }

    formatTime(timestamp) {
        if (!timestamp) return '-';
        const date = new Date(timestamp);
        return date.toLocaleTimeString('ja-JP');
    }
}

// グローバルインスタンス
const dashboard = new EnvironmentDashboard();

// 初期化
document.addEventListener('DOMContentLoaded', () => {
    dashboard.initialize();
});