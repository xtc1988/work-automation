// API通信処理
class APIClient {
    constructor() {
        this.cache = new Map();
        this.cacheTTL = 60000; // 1分間キャッシュ
    }

    // キャッシュキーの生成
    generateCacheKey(url, options = {}) {
        return `${url}_${JSON.stringify(options)}`;
    }

    // キャッシュからの取得
    getFromCache(key) {
        const cached = this.cache.get(key);
        if (cached && Date.now() - cached.timestamp < this.cacheTTL) {
            Logger.debug(`Cache hit for: ${key}`);
            return cached.data;
        }
        return null;
    }

    // キャッシュへの保存
    setCache(key, data) {
        this.cache.set(key, {
            data: data,
            timestamp: Date.now()
        });
    }

    // HTTP GET リクエスト
    async get(url, options = {}) {
        const cacheKey = this.generateCacheKey(url, options);
        const cached = this.getFromCache(cacheKey);
        
        if (cached) {
            return cached;
        }

        try {
            Logger.debug(`Fetching: ${url}`);
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                signal: options.signal
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            this.setCache(cacheKey, data);
            
            Logger.debug(`Successfully fetched: ${url}`);
            return data;
        } catch (error) {
            Logger.error(`Failed to fetch ${url}:`, error);
            throw error;
        }
    }

    // ヘルスチェック
    async healthCheck(url, timeout = Config.HEALTH_CHECK_TIMEOUT) {
        const startTime = Date.now();
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        try {
            Logger.debug(`Health check: ${url}`);
            const response = await fetch(url, {
                method: 'GET',
                signal: controller.signal,
                mode: 'cors'
            });

            clearTimeout(timeoutId);
            const responseTime = Date.now() - startTime;

            const result = {
                url: url,
                status: response.ok ? 'healthy' : 'error',
                responseTime: responseTime,
                httpStatus: response.status,
                timestamp: new Date().toISOString()
            };

            // レスポンスタイムによる状態判定
            if (result.status === 'healthy' && responseTime > Config.RESPONSE_TIME_THRESHOLDS.warning) {
                result.status = responseTime > Config.RESPONSE_TIME_THRESHOLDS.error ? 'error' : 'warning';
            }

            Logger.debug(`Health check result for ${url}:`, result);
            return result;
        } catch (error) {
            clearTimeout(timeoutId);
            
            const result = {
                url: url,
                status: 'error',
                responseTime: error.name === 'AbortError' ? 'timeout' : 'error',
                error: error.message,
                timestamp: new Date().toISOString()
            };

            Logger.warn(`Health check failed for ${url}:`, error);
            return result;
        }
    }

    // 複数のヘルスチェックを並列実行
    async batchHealthCheck(urls) {
        Logger.info(`Batch health check for ${urls.length} URLs`);
        
        const promises = urls.map(url => 
            this.healthCheck(url).catch(error => ({
                url: url,
                status: 'error',
                error: error.message,
                timestamp: new Date().toISOString()
            }))
        );

        const results = await Promise.all(promises);
        
        Logger.info(`Batch health check completed. Results:`, results);
        return results;
    }

    // Wiki キャッシュデータの取得
    async getWikiCache() {
        try {
            return await this.get(Config.API_ENDPOINTS.wikiCache);
        } catch (error) {
            Logger.error('Failed to load wiki cache:', error);
            return { environments: [], last_updated: null };
        }
    }

    // 環境設定の取得
    async getEnvironments() {
        try {
            return await this.get(Config.API_ENDPOINTS.environments);
        } catch (error) {
            Logger.error('Failed to load environments config:', error);
            return { environments: [] };
        }
    }

    // Wiki ソース設定の取得
    async getWikiSources() {
        try {
            return await this.get(Config.API_ENDPOINTS.wikiSources);
        } catch (error) {
            Logger.error('Failed to load wiki sources config:', error);
            return { sources: [] };
        }
    }

    // キャッシュクリア
    clearCache() {
        this.cache.clear();
        Logger.info('API cache cleared');
    }
}

// APIクライアントのシングルトンインスタンス
const api = new APIClient();