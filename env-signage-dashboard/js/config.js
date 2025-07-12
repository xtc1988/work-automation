// 設定管理
const Config = {
    // 更新間隔（ミリ秒）
    UPDATE_INTERVAL: 60000, // 60秒

    // API エンドポイント
    API_ENDPOINTS: {
        wikiCache: 'data/wiki-cache.json',
        environments: 'config/environments.json',
        wikiSources: 'config/wiki-sources.json'
    },

    // ヘルスチェックタイムアウト
    HEALTH_CHECK_TIMEOUT: 5000, // 5秒

    // 状態の色設定
    STATUS_COLORS: {
        healthy: '#00ff88',
        warning: '#ffa500',
        error: '#ff4757',
        maintenance: '#747d8c'
    },

    // レスポンスタイムしきい値
    RESPONSE_TIME_THRESHOLDS: {
        good: 100,    // 100ms以下
        warning: 300, // 300ms以下
        error: 1000   // 1000ms以上
    },

    // デバッグモード
    DEBUG: false,

    // ログレベル
    LOG_LEVEL: 'info' // 'debug', 'info', 'warn', 'error'
};

// ログ出力関数
const Logger = {
    debug: (message, ...args) => {
        if (Config.DEBUG || Config.LOG_LEVEL === 'debug') {
            console.debug(`[DEBUG] ${new Date().toISOString()}: ${message}`, ...args);
        }
    },
    info: (message, ...args) => {
        if (['debug', 'info'].includes(Config.LOG_LEVEL)) {
            console.info(`[INFO] ${new Date().toISOString()}: ${message}`, ...args);
        }
    },
    warn: (message, ...args) => {
        if (['debug', 'info', 'warn'].includes(Config.LOG_LEVEL)) {
            console.warn(`[WARN] ${new Date().toISOString()}: ${message}`, ...args);
        }
    },
    error: (message, ...args) => {
        console.error(`[ERROR] ${new Date().toISOString()}: ${message}`, ...args);
    }
};