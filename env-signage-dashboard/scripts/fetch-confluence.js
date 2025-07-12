// Confluence Wiki情報取得スクリプト
const https = require('https');
const fs = require('fs').promises;
const path = require('path');

class ConfluenceFetcher {
    constructor() {
        this.baseUrl = process.env.CONFLUENCE_BASE_URL;
        this.token = process.env.CONFLUENCE_TOKEN;
        this.username = process.env.CONFLUENCE_USERNAME;
        
        if (!this.baseUrl || !this.token) {
            throw new Error('CONFLUENCE_BASE_URL and CONFLUENCE_TOKEN environment variables are required');
        }
    }

    // HTTP GET リクエスト
    async httpGet(url, headers = {}) {
        return new Promise((resolve, reject) => {
            const options = {
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    ...headers
                }
            };

            const req = https.get(url, options, (res) => {
                let data = '';
                
                res.on('data', (chunk) => {
                    data += chunk;
                });
                
                res.on('end', () => {
                    if (res.statusCode >= 200 && res.statusCode < 300) {
                        try {
                            resolve(JSON.parse(data));
                        } catch (error) {
                            reject(new Error(`Failed to parse JSON: ${error.message}`));
                        }
                    } else {
                        reject(new Error(`HTTP ${res.statusCode}: ${data}`));
                    }
                });
            });

            req.on('error', (error) => {
                reject(error);
            });

            req.setTimeout(10000, () => {
                req.destroy();
                reject(new Error('Request timeout'));
            });
        });
    }

    // ページコンテンツの取得
    async getPageContent(pageId) {
        const url = `${this.baseUrl}/rest/api/content/${pageId}?expand=body.storage,version`;
        
        console.log(`Fetching Confluence page: ${pageId}`);
        
        try {
            const data = await this.httpGet(url);
            return data;
        } catch (error) {
            console.error(`Failed to fetch page ${pageId}:`, error.message);
            throw error;
        }
    }

    // ページIDからURLを生成
    extractPageId(url) {
        const match = url.match(/pages\/(\d+)/);
        return match ? match[1] : null;
    }

    // Confluenceからデータを取得
    async fetchFromConfluence(sourceConfig) {
        try {
            const pageId = this.extractPageId(sourceConfig.url);
            if (!pageId) {
                throw new Error(`Cannot extract page ID from URL: ${sourceConfig.url}`);
            }

            const pageData = await this.getPageContent(pageId);
            
            // Wiki解析（simplified version）
            const environments = this.parseConfluenceContent(pageData, sourceConfig);
            
            console.log(`Successfully fetched ${environments.length} environments from ${sourceConfig.name}`);
            return environments;
            
        } catch (error) {
            console.error(`Failed to fetch from Confluence:`, error.message);
            return [];
        }
    }

    // Confluenceコンテンツの解析
    parseConfluenceContent(pageData, sourceConfig) {
        const environments = [];
        
        try {
            if (!pageData.body || !pageData.body.storage) {
                console.warn('No storage content found in page data');
                return environments;
            }

            const htmlContent = pageData.body.storage.value;
            
            // 簡易的なHTMLテーブル解析
            const tableRegex = /<table[^>]*>(.*?)<\/table>/gis;
            const rowRegex = /<tr[^>]*>(.*?)<\/tr>/gis;
            const cellRegex = /<t[hd][^>]*>(.*?)<\/t[hd]>/gis;
            
            const tableMatch = tableRegex.exec(htmlContent);
            if (!tableMatch) {
                console.warn('No table found in Confluence content');
                return environments;
            }

            const tableContent = tableMatch[1];
            let rowMatch;
            let isHeaderRow = true;
            
            while ((rowMatch = rowRegex.exec(tableContent)) !== null) {
                if (isHeaderRow) {
                    isHeaderRow = false;
                    continue; // ヘッダー行をスキップ
                }

                const rowContent = rowMatch[1];
                const cells = [];
                let cellMatch;
                
                while ((cellMatch = cellRegex.exec(rowContent)) !== null) {
                    // HTMLタグを除去してテキストのみを抽出
                    const cellText = cellMatch[1].replace(/<[^>]*>/g, '').trim();
                    cells.push(cellText);
                }

                if (cells.length >= 3) {
                    const env = {
                        id: this.generateId(cells[0]),
                        name: cells[0] || 'Unknown Environment',
                        url: cells[1] || '',
                        healthCheck: cells[1] ? `${cells[1]}/health` : '',
                        credentials: {
                            username: cells[2] || '',
                            password: cells[3] || '',
                            auth_type: 'basic'
                        },
                        description: cells[4] || '',
                        access_notes: cells[5] || '',
                        source: {
                            wiki: 'confluence',
                            page: sourceConfig.name,
                            updated: new Date().toISOString()
                        },
                        services: []
                    };

                    environments.push(env);
                }
            }
        } catch (error) {
            console.error('Failed to parse Confluence content:', error.message);
        }

        return environments;
    }

    // IDの生成
    generateId(name) {
        if (!name) return 'unknown';
        return name.toLowerCase()
                  .replace(/[^a-z0-9]/g, '-')
                  .replace(/-+/g, '-')
                  .replace(/^-|-$/g, '');
    }
}

// メイン処理
async function main() {
    try {
        console.log('Starting Confluence data fetch...');
        
        // 設定ファイルの読み込み
        const configPath = path.join(__dirname, '..', 'config', 'wiki-sources.json');
        const configData = await fs.readFile(configPath, 'utf8');
        const config = JSON.parse(configData);
        
        // Confluenceソースを抽出
        const confluenceSources = config.sources.filter(source => source.type === 'confluence');
        
        if (confluenceSources.length === 0) {
            console.log('No Confluence sources found in configuration');
            return;
        }

        const fetcher = new ConfluenceFetcher();
        const allEnvironments = [];

        // 各Confluenceソースからデータを取得
        for (const source of confluenceSources) {
            console.log(`Processing Confluence source: ${source.name}`);
            const environments = await fetcher.fetchFromConfluence(source);
            allEnvironments.push(...environments);
        }

        // 既存のキャッシュファイルを読み込み
        const cachePath = path.join(__dirname, '..', 'data', 'wiki-cache.json');
        let existingCache = { environments: [], last_updated: null };
        
        try {
            const existingData = await fs.readFile(cachePath, 'utf8');
            existingCache = JSON.parse(existingData);
        } catch (error) {
            console.log('No existing cache file found, creating new one');
        }

        // Confluenceからのデータで既存データを更新
        const updatedEnvironments = [...existingCache.environments];
        
        for (const newEnv of allEnvironments) {
            const existingIndex = updatedEnvironments.findIndex(env => env.id === newEnv.id);
            if (existingIndex >= 0) {
                // 既存データを更新
                updatedEnvironments[existingIndex] = newEnv;
            } else {
                // 新しいデータを追加
                updatedEnvironments.push(newEnv);
            }
        }

        // キャッシュファイルの更新
        const updatedCache = {
            last_updated: new Date().toISOString(),
            environments: updatedEnvironments
        };

        await fs.writeFile(cachePath, JSON.stringify(updatedCache, null, 2), 'utf8');
        
        console.log(`Successfully updated cache with ${allEnvironments.length} environments from Confluence`);
        console.log(`Total environments in cache: ${updatedEnvironments.length}`);
        
    } catch (error) {
        console.error('Failed to fetch Confluence data:', error.message);
        process.exit(1);
    }
}

// スクリプト直接実行時のエラーハンドリング
if (require.main === module) {
    main().catch(error => {
        console.error('Unhandled error:', error);
        process.exit(1);
    });
}

module.exports = { ConfluenceFetcher };