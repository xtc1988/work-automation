// Notion Wiki情報取得スクリプト
const https = require('https');
const fs = require('fs').promises;
const path = require('path');

class NotionFetcher {
    constructor() {
        this.token = process.env.NOTION_TOKEN;
        this.version = '2022-06-28'; // Notion APIバージョン
        
        if (!this.token) {
            throw new Error('NOTION_TOKEN environment variable is required');
        }
    }

    // HTTP POST リクエスト
    async httpPost(url, data, headers = {}) {
        return new Promise((resolve, reject) => {
            const postData = JSON.stringify(data);
            
            const options = {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                    'Content-Type': 'application/json',
                    'Notion-Version': this.version,
                    'Content-Length': Buffer.byteLength(postData),
                    ...headers
                }
            };

            const req = https.request(url, options, (res) => {
                let responseData = '';
                
                res.on('data', (chunk) => {
                    responseData += chunk;
                });
                
                res.on('end', () => {
                    if (res.statusCode >= 200 && res.statusCode < 300) {
                        try {
                            resolve(JSON.parse(responseData));
                        } catch (error) {
                            reject(new Error(`Failed to parse JSON: ${error.message}`));
                        }
                    } else {
                        reject(new Error(`HTTP ${res.statusCode}: ${responseData}`));
                    }
                });
            });

            req.on('error', (error) => {
                reject(error);
            });

            req.setTimeout(15000, () => {
                req.destroy();
                reject(new Error('Request timeout'));
            });

            req.write(postData);
            req.end();
        });
    }

    // データベースクエリ
    async queryDatabase(databaseId, filter = {}) {
        const url = `https://api.notion.com/v1/databases/${databaseId}/query`;
        
        console.log(`Querying Notion database: ${databaseId}`);
        
        try {
            const data = await this.httpPost(url, {
                filter: filter,
                page_size: 100 // 最大100件取得
            });
            
            return data;
        } catch (error) {
            console.error(`Failed to query database ${databaseId}:`, error.message);
            throw error;
        }
    }

    // Notionからデータを取得
    async fetchFromNotion(sourceConfig) {
        try {
            const databaseId = sourceConfig.database_id;
            if (!databaseId) {
                throw new Error('database_id is required for Notion source');
            }

            const queryResult = await this.queryDatabase(databaseId);
            
            // Notion解析
            const environments = this.parseNotionData(queryResult, sourceConfig);
            
            console.log(`Successfully fetched ${environments.length} environments from ${sourceConfig.name}`);
            return environments;
            
        } catch (error) {
            console.error(`Failed to fetch from Notion:`, error.message);
            return [];
        }
    }

    // Notionデータベースレスポンスの解析
    parseNotionData(queryResult, sourceConfig) {
        const environments = [];
        
        try {
            if (!queryResult.results || !Array.isArray(queryResult.results)) {
                console.warn('No results found in Notion query response');
                return environments;
            }

            for (const page of queryResult.results) {
                try {
                    const properties = page.properties;
                    
                    const env = {
                        id: page.id,
                        name: this.extractNotionProperty(properties.Name || properties.環境名 || properties.name),
                        url: this.extractNotionProperty(properties.URL || properties.url),
                        healthCheck: '',
                        credentials: {
                            username: this.extractNotionProperty(properties.Username || properties.ユーザー名 || properties.username),
                            password: this.extractNotionProperty(properties.Password || properties.パスワード || properties.password),
                            auth_type: 'basic'
                        },
                        description: this.extractNotionProperty(properties.Description || properties.説明 || properties.description),
                        access_notes: this.extractNotionProperty(properties.Notes || properties.注意事項 || properties.notes),
                        source: {
                            wiki: 'notion',
                            page: sourceConfig.name,
                            updated: new Date().toISOString()
                        },
                        services: []
                    };

                    // ヘルスチェックURLの推定
                    if (env.url) {
                        env.healthCheck = `${env.url}/health`;
                    }

                    // 必須フィールドのチェック
                    if (env.name && env.url) {
                        environments.push(env);
                    } else {
                        console.warn(`Skipping page ${page.id}: missing name or URL`);
                    }
                    
                } catch (error) {
                    console.warn(`Failed to parse Notion page ${page.id}:`, error.message);
                }
            }
        } catch (error) {
            console.error('Failed to parse Notion data:', error.message);
        }

        return environments;
    }

    // Notionプロパティの値を抽出
    extractNotionProperty(property) {
        if (!property) return '';
        
        try {
            switch (property.type) {
                case 'title':
                    return property.title?.[0]?.plain_text || '';
                case 'rich_text':
                    return property.rich_text?.[0]?.plain_text || '';
                case 'url':
                    return property.url || '';
                case 'email':
                    return property.email || '';
                case 'phone_number':
                    return property.phone_number || '';
                case 'select':
                    return property.select?.name || '';
                case 'multi_select':
                    return property.multi_select?.map(s => s.name).join(', ') || '';
                case 'date':
                    return property.date?.start || '';
                case 'checkbox':
                    return property.checkbox ? 'true' : 'false';
                case 'number':
                    return property.number?.toString() || '';
                case 'formula':
                    return this.extractNotionProperty(property.formula) || '';
                case 'rollup':
                    return this.extractNotionProperty(property.rollup) || '';
                default:
                    // プレーンテキストの場合
                    if (typeof property === 'string') {
                        return property;
                    }
                    return property.plain_text || '';
            }
        } catch (error) {
            console.warn(`Failed to extract property:`, error.message);
            return '';
        }
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
        console.log('Starting Notion data fetch...');
        
        // 設定ファイルの読み込み
        const configPath = path.join(__dirname, '..', 'config', 'wiki-sources.json');
        const configData = await fs.readFile(configPath, 'utf8');
        const config = JSON.parse(configData);
        
        // Notionソースを抽出
        const notionSources = config.sources.filter(source => source.type === 'notion');
        
        if (notionSources.length === 0) {
            console.log('No Notion sources found in configuration');
            return;
        }

        const fetcher = new NotionFetcher();
        const allEnvironments = [];

        // 各Notionソースからデータを取得
        for (const source of notionSources) {
            console.log(`Processing Notion source: ${source.name}`);
            const environments = await fetcher.fetchFromNotion(source);
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

        // Notionからのデータで既存データを更新
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
        
        console.log(`Successfully updated cache with ${allEnvironments.length} environments from Notion`);
        console.log(`Total environments in cache: ${updatedEnvironments.length}`);
        
    } catch (error) {
        console.error('Failed to fetch Notion data:', error.message);
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

module.exports = { NotionFetcher };