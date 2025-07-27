// メインアプリケーション
class EnvironmentDashboard {
    constructor() {
        this.environments = [];
        this.filteredEnvironments = [];
        this.isUpdating = false;
        this.updateInterval = null;
        
        // DOM要素の参照
        this.elements = {
            environmentsGrid: null,
            updateTime: null,
            searchInput: null,
            clearSearchBtn: null,
            versionFilter: null,
            databaseFilter: null,
            multicompanyFilter: null,
            multipersonFilter: null,
            resetFiltersBtn: null,
            resultsCount: null
        };
    }

    // 初期化
    async initialize() {
        try {
            console.log('Initializing Environment Dashboard');
            
            // DOM要素の取得
            this.elements.environmentsGrid = document.getElementById('environments-grid');
            this.elements.updateTime = document.getElementById('update-time');
            this.elements.searchInput = document.getElementById('search-input');
            this.elements.clearSearchBtn = document.getElementById('clear-search');
            this.elements.versionFilter = document.getElementById('version-filter');
            this.elements.databaseFilter = document.getElementById('database-filter');
            this.elements.multicompanyFilter = document.getElementById('multicompany-filter');
            this.elements.multipersonFilter = document.getElementById('multiperson-filter');
            this.elements.resetFiltersBtn = document.getElementById('reset-filters');
            this.elements.resultsCount = document.getElementById('results-count');

            // 検索・フィルター機能の初期化
            this.initializeSearch();

            // 初回データ読み込み
            await this.loadEnvironments();
            
            // ダッシュボード描画
            this.renderDashboard();
            
            // 自動更新の開始
            this.startAutoUpdate();
            
            console.log('Dashboard initialization completed');
        } catch (error) {
            console.error('Failed to initialize dashboard:', error);
        }
    }

    // 環境データの読み込み
    async loadEnvironments() {
        try {
            console.log('Loading environments data');
            
            // ダミーデータ（実際にはAPIから取得）
            this.environments = [
                {
                    id: 'dev',
                    name: '開発環境 (DEV)',
                    displayName: 'DEV',
                    status: 'operational',
                    database: 'Oracle',
                    channel: '#dev-環境',
                    version: 'v8.2.1',
                    url: 'https://dev.example.com',
                    services: [
                        { name: 'マルチカンパニー', enabled: true },
                        { name: 'マルチパーソン', enabled: true }
                    ]
                },
                {
                    id: 'stg',
                    name: 'ステージング環境 (STG)',
                    displayName: 'STG',
                    status: 'warning',
                    database: 'Aurora',
                    channel: '#stg-環境',
                    version: 'v7.5.3',
                    url: 'https://stg.example.com',
                    services: [
                        { name: 'マルチカンパニー', enabled: true },
                        { name: 'マルチパーソン', enabled: false }
                    ]
                },
                {
                    id: 'uat',
                    name: 'UAT環境 (UAT)',
                    displayName: 'UAT',
                    status: 'operational',
                    database: 'Aurora',
                    channel: '#uat-環境',
                    version: 'v8.1.0',
                    url: 'https://uat.example.com',
                    services: [
                        { name: 'マルチカンパニー', enabled: false },
                        { name: 'マルチパーソン', enabled: false }
                    ]
                },
                {
                    id: 'demo',
                    name: 'デモ環境 (DEMO)',
                    displayName: 'DEMO',
                    status: 'error',
                    database: 'Oracle',
                    channel: '#demo-環境',
                    version: 'v6.9.2',
                    url: 'https://demo.example.com',
                    services: [
                        { name: 'マルチカンパニー', enabled: true },
                        { name: 'マルチパーソン', enabled: false }
                    ]
                }
            ];
            
            console.log(`Loaded ${this.environments.length} environments`);
            this.filteredEnvironments = [...this.environments];
        } catch (error) {
            console.error('Failed to load environments:', error);
            this.environments = [];
            this.filteredEnvironments = [];
        }
    }

    // ダッシュボード描画
    renderDashboard() {
        if (!this.elements.environmentsGrid) return;

        try {
            this.elements.environmentsGrid.innerHTML = '';

            for (const env of this.filteredEnvironments) {
                const card = this.createEnvironmentCard(env);
                this.elements.environmentsGrid.appendChild(card);
            }

            // 最終更新時刻の更新
            this.updateLastUpdatedTime();

            // 検索結果数の更新
            this.updateResultsCount();

        } catch (error) {
            console.error('Dashboard rendering failed:', error);
        }
    }

    // 環境カードの作成
    createEnvironmentCard(env) {
        // 全体のステータスを決定（環境自体のステータスのみ）
        
        let cardClass = 'env-card';
        if (env.status === 'error') {
            cardClass += ' has-error';
        } else if (env.status === 'warning') {
            cardClass += ' has-warning';
        } else {
            cardClass += ' all-operational';
        }

        // ステータスバッジのテキストとクラス
        let statusText, statusClass;
        if (env.status === 'operational') {
            statusText = `正常稼働 | ${env.database}`;
            statusClass = 'operational';
        } else if (env.status === 'warning') {
            statusText = `一部問題あり | ${env.database}`;
            statusClass = 'warning';
        } else {
            statusText = `障害発生中 | ${env.database}`;
            statusClass = 'error';
        }
        
        const card = document.createElement('div');
        card.className = cardClass;
        card.setAttribute('data-env-id', env.id);

        card.innerHTML = `
            <div class="env-header">
                <div class="env-status-badge ${statusClass}">
                    <span class="status-dot ${statusClass}"></span>
                    ${statusText}
                </div>
                <h3 class="env-title">${env.name}</h3>
                <div class="env-info">
                    <div class="env-info-item">
                        <span>💬</span>
                        <span>${env.channel}</span>
                    </div>
                    <div class="env-info-item">
                        <span>🔄</span>
                        <span>${env.version}</span>
                    </div>
                </div>
            </div>
            <div class="env-body">
                <div class="services-list">
                    ${env.services.map(service => `
                        <div class="service-item">
                            <span class="service-name">${service.name}</span>
                            <span class="service-status">
                                ${service.enabled ? 'ON' : 'OFF'}
                            </span>
                        </div>
                    `).join('')}
                </div>

                <div class="env-actions">
                    <button class="action-btn primary" onclick="window.open('${env.url}', '_blank')">ログイン</button>
                    <button class="action-btn secondary" onclick="dashboard.deployUnit('${env.id}')">ユニットデプロイ</button>
                </div>
            </div>
        `;

        return card;
    }

    // ユニットデプロイ
    deployUnit(envId) {
        const env = this.environments.find(e => e.id === envId);
        if (env) {
            alert(`${env.name}にユニットデプロイを実行します`);
            // 実際のデプロイロジックをここに実装
        }
    }

    // 最終更新時刻の更新
    updateLastUpdatedTime() {
        if (this.elements.updateTime) {
            const now = new Date();
            const options = { 
                year: 'numeric', 
                month: 'numeric', 
                day: 'numeric',
                hour: '2-digit', 
                minute: '2-digit'
            };
            this.elements.updateTime.textContent = now.toLocaleString('ja-JP', options);
        }
    }

    // 自動更新の開始
    startAutoUpdate() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }

        this.updateInterval = setInterval(() => {
            this.updateData();
        }, 60000); // 1分ごとに更新

        console.log('Auto-update started');
    }

    // 検索・フィルター機能の初期化
    initializeSearch() {
        // 検索入力のイベントリスナー
        if (this.elements.searchInput) {
            this.elements.searchInput.addEventListener('input', () => {
                this.applyFilters();
            });
        }

        // クリアボタンのイベントリスナー
        if (this.elements.clearSearchBtn) {
            this.elements.clearSearchBtn.addEventListener('click', () => {
                this.elements.searchInput.value = '';
                this.applyFilters();
            });
        }

        // フィルターのイベントリスナー
        const filters = [
            this.elements.versionFilter,
            this.elements.databaseFilter,
            this.elements.multicompanyFilter,
            this.elements.multipersonFilter
        ];

        filters.forEach(filter => {
            if (filter) {
                filter.addEventListener('change', () => {
                    this.applyFilters();
                });
            }
        });

        // リセットボタンのイベントリスナー
        if (this.elements.resetFiltersBtn) {
            this.elements.resetFiltersBtn.addEventListener('click', () => {
                this.resetFilters();
            });
        }
    }

    // フィルターの適用
    applyFilters() {
        const searchTerm = this.elements.searchInput?.value.toLowerCase() || '';
        const versionFilter = this.elements.versionFilter?.value || '';
        const databaseFilter = this.elements.databaseFilter?.value || '';
        const multicompanyFilter = this.elements.multicompanyFilter?.value || '';
        const multipersonFilter = this.elements.multipersonFilter?.value || '';

        this.filteredEnvironments = this.environments.filter(env => {
            // テキスト検索（環境名、バージョン、チャンネル）
            const searchMatch = !searchTerm || 
                env.name.toLowerCase().includes(searchTerm) ||
                env.version.toLowerCase().includes(searchTerm) ||
                env.channel.toLowerCase().includes(searchTerm);

            // バージョンフィルター（メジャーバージョンでフィルタリング）
            const versionMatch = !versionFilter || env.version.toLowerCase().startsWith(versionFilter.toLowerCase());

            // データベースフィルター
            const databaseMatch = !databaseFilter || env.database === databaseFilter;

            // マルチカンパニーフィルター
            const multicompanyService = env.services.find(s => s.name === 'マルチカンパニー');
            const multicompanyMatch = !multicompanyFilter || 
                (multicompanyService && multicompanyService.enabled.toString() === multicompanyFilter);

            // マルチパーソンフィルター
            const multipersonService = env.services.find(s => s.name === 'マルチパーソン');
            const multipersonMatch = !multipersonFilter || 
                (multipersonService && multipersonService.enabled.toString() === multipersonFilter);

            return searchMatch && versionMatch && databaseMatch && multicompanyMatch && multipersonMatch;
        });

        this.renderDashboard();
    }

    // フィルターのリセット
    resetFilters() {
        if (this.elements.searchInput) this.elements.searchInput.value = '';
        if (this.elements.versionFilter) this.elements.versionFilter.value = '';
        if (this.elements.databaseFilter) this.elements.databaseFilter.value = '';
        if (this.elements.multicompanyFilter) this.elements.multicompanyFilter.value = '';
        if (this.elements.multipersonFilter) this.elements.multipersonFilter.value = '';
        
        this.applyFilters();
    }

    // 検索結果数の更新
    updateResultsCount() {
        if (this.elements.resultsCount) {
            const count = this.filteredEnvironments.length;
            this.elements.resultsCount.textContent = `${count}件の環境が見つかりました`;
        }
    }

    // データ更新時にフィルターを再適用
    async updateData() {
        if (this.isUpdating) return;

        try {
            this.isUpdating = true;
            console.log('Updating dashboard data');

            await this.loadEnvironments();
            this.applyFilters(); // フィルターを再適用

        } catch (error) {
            console.error('Data update failed:', error);
        } finally {
            this.isUpdating = false;
        }
    }
}

// グローバルインスタンス
const dashboard = new EnvironmentDashboard();

// 初期化
document.addEventListener('DOMContentLoaded', () => {
    dashboard.initialize();
});

// 現在時刻の更新
function updateTime() {
    const now = new Date();
    const options = { 
        year: 'numeric', 
        month: 'numeric', 
        day: 'numeric',
        hour: '2-digit', 
        minute: '2-digit'
    };
    const updateTimeElement = document.getElementById('update-time');
    if (updateTimeElement) {
        updateTimeElement.textContent = now.toLocaleString('ja-JP', options);
    }
}

// 初期表示と定期更新
updateTime();
setInterval(updateTime, 60000); // 1分ごとに更新