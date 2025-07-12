// Wiki解析処理
class WikiParser {
    constructor() {
        this.parsers = {
            'confluence': this.parseConfluence.bind(this),
            'github_wiki': this.parseGitHubWiki.bind(this),
            'notion': this.parseNotion.bind(this),
            'mediawiki': this.parseMediaWiki.bind(this),
            'html': this.parseHTML.bind(this)
        };
    }

    // メイン解析メソッド
    async parseWikiSource(sourceConfig, rawData) {
        try {
            Logger.info(`Parsing wiki source: ${sourceConfig.type} - ${sourceConfig.name}`);
            
            const parser = this.parsers[sourceConfig.type];
            if (!parser) {
                throw new Error(`Unsupported wiki type: ${sourceConfig.type}`);
            }

            const environments = await parser(sourceConfig, rawData);
            
            Logger.info(`Successfully parsed ${environments.length} environments from ${sourceConfig.name}`);
            return environments;
        } catch (error) {
            Logger.error(`Failed to parse wiki source ${sourceConfig.name}:`, error);
            return [];
        }
    }

    // Confluence解析
    async parseConfluence(sourceConfig, data) {
        const environments = [];
        
        try {
            // Confluence REST API レスポンスの解析
            if (data.body && data.body.storage) {
                const htmlContent = data.body.storage.value;
                const parser = new DOMParser();
                const doc = parser.parseFromString(htmlContent, 'text/html');
                
                const tableSelector = sourceConfig.parser.table_selector || 'table';
                const table = doc.querySelector(tableSelector);
                
                if (table) {
                    const rows = table.querySelectorAll('tbody tr');
                    const columns = sourceConfig.parser.columns;
                    
                    rows.forEach((row, index) => {
                        try {
                            const cells = row.querySelectorAll('td');
                            if (cells.length < Object.keys(columns).length) return;
                            
                            const env = {
                                id: this.generateId(cells[columns.name]?.textContent?.trim()),
                                name: cells[columns.name]?.textContent?.trim(),
                                url: cells[columns.url]?.textContent?.trim(),
                                credentials: {
                                    username: cells[columns.login_user]?.textContent?.trim(),
                                    password: cells[columns.login_pass]?.textContent?.trim(),
                                    auth_type: 'basic'
                                },
                                description: cells[columns.description]?.textContent?.trim(),
                                source: {
                                    wiki: 'confluence',
                                    page: sourceConfig.name,
                                    updated: new Date().toISOString()
                                },
                                services: []
                            };
                            
                            // ヘルスチェックURLの推定
                            if (env.url) {
                                env.healthCheck = `${env.url}/health`;
                            }
                            
                            environments.push(env);
                        } catch (error) {
                            Logger.warn(`Failed to parse Confluence row ${index}:`, error);
                        }
                    });
                }
            }
        } catch (error) {
            Logger.error('Confluence parsing error:', error);
        }
        
        return environments;
    }

    // GitHub Wiki解析
    async parseGitHubWiki(sourceConfig, data) {
        const environments = [];
        
        try {
            // マークダウンテーブルの解析
            const content = data.content || data;
            const lines = content.split('\n');
            
            let inTable = false;
            let headers = [];
            
            for (const line of lines) {
                const trimmedLine = line.trim();
                
                // テーブルの開始を検出
                if (trimmedLine.includes('|') && !inTable) {
                    headers = trimmedLine.split('|').map(h => h.trim()).filter(h => h);
                    inTable = true;
                    continue;
                }
                
                // テーブルの区切り行をスキップ
                if (inTable && trimmedLine.match(/^\|[\s\-\|]+\|$/)) {
                    continue;
                }
                
                // テーブル行の処理
                if (inTable && trimmedLine.includes('|')) {
                    const cells = trimmedLine.split('|').map(c => c.trim()).filter(c => c);
                    
                    if (cells.length >= 3) {
                        const env = {
                            id: this.generateId(cells[0]),
                            name: cells[0],
                            url: cells[1],
                            healthCheck: `${cells[1]}/health`,
                            credentials: {
                                username: cells[2] || '',
                                password: cells[3] || '',
                                auth_type: 'basic'
                            },
                            description: cells[4] || '',
                            access_notes: cells[5] || '',
                            source: {
                                wiki: 'github_wiki',
                                page: sourceConfig.name,
                                updated: new Date().toISOString()
                            },
                            services: []
                        };
                        
                        environments.push(env);
                    }
                } else if (inTable && !trimmedLine.includes('|')) {
                    // テーブル終了
                    break;
                }
            }
        } catch (error) {
            Logger.error('GitHub Wiki parsing error:', error);
        }
        
        return environments;
    }

    // Notion解析
    async parseNotion(sourceConfig, data) {
        const environments = [];
        
        try {
            // Notion Database API レスポンスの解析
            if (data.results) {
                data.results.forEach((page, index) => {
                    try {
                        const properties = page.properties;
                        
                        const env = {
                            id: page.id,
                            name: this.extractNotionProperty(properties.Name || properties.環境名),
                            url: this.extractNotionProperty(properties.URL),
                            credentials: {
                                username: this.extractNotionProperty(properties.Username || properties.ユーザー名),
                                password: this.extractNotionProperty(properties.Password || properties.パスワード),
                                auth_type: 'basic'
                            },
                            description: this.extractNotionProperty(properties.Description || properties.説明),
                            access_notes: this.extractNotionProperty(properties.Notes || properties.注意事項),
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
                        
                        environments.push(env);
                    } catch (error) {
                        Logger.warn(`Failed to parse Notion page ${index}:`, error);
                    }
                });
            }
        } catch (error) {
            Logger.error('Notion parsing error:', error);
        }
        
        return environments;
    }

    // MediaWiki解析
    async parseMediaWiki(sourceConfig, data) {
        // MediaWiki API レスポンスの解析実装
        // 実装は必要に応じて追加
        return [];
    }

    // 汎用HTML解析
    async parseHTML(sourceConfig, htmlContent) {
        const environments = [];
        
        try {
            const parser = new DOMParser();
            const doc = parser.parseFromString(htmlContent, 'text/html');
            
            // 設定に基づいてテーブルを解析
            const tableSelector = sourceConfig.parser.table_selector || 'table';
            const table = doc.querySelector(tableSelector);
            
            if (table) {
                const rows = table.querySelectorAll('tbody tr, tr');
                
                rows.forEach((row, index) => {
                    try {
                        const cells = row.querySelectorAll('td, th');
                        if (cells.length < 3) return;
                        
                        const env = {
                            id: this.generateId(cells[0]?.textContent?.trim()),
                            name: cells[0]?.textContent?.trim(),
                            url: cells[1]?.textContent?.trim(),
                            description: cells[2]?.textContent?.trim(),
                            source: {
                                wiki: 'html',
                                page: sourceConfig.name,
                                updated: new Date().toISOString()
                            },
                            services: []
                        };
                        
                        environments.push(env);
                    } catch (error) {
                        Logger.warn(`Failed to parse HTML row ${index}:`, error);
                    }
                });
            }
        } catch (error) {
            Logger.error('HTML parsing error:', error);
        }
        
        return environments;
    }

    // Notionプロパティの値を抽出
    extractNotionProperty(property) {
        if (!property) return '';
        
        switch (property.type) {
            case 'title':
                return property.title?.[0]?.plain_text || '';
            case 'rich_text':
                return property.rich_text?.[0]?.plain_text || '';
            case 'url':
                return property.url || '';
            case 'select':
                return property.select?.name || '';
            case 'multi_select':
                return property.multi_select?.map(s => s.name).join(', ') || '';
            default:
                return property.plain_text || '';
        }
    }

    // IDの生成（環境名から）
    generateId(name) {
        if (!name) return 'unknown';
        return name.toLowerCase()
                  .replace(/[^a-z0-9]/g, '-')
                  .replace(/-+/g, '-')
                  .replace(/^-|-$/g, '');
    }

    // 環境データの正規化
    normalizeEnvironment(env) {
        return {
            id: env.id || this.generateId(env.name),
            name: env.name || 'Unknown Environment',
            url: env.url || '',
            healthCheck: env.healthCheck || `${env.url}/health`,
            credentials: {
                username: env.credentials?.username || '',
                password: env.credentials?.password || '',
                auth_type: env.credentials?.auth_type || 'basic'
            },
            description: env.description || '',
            access_notes: env.access_notes || '',
            source: env.source || {
                wiki: 'unknown',
                page: 'unknown',
                updated: new Date().toISOString()
            },
            services: env.services || []
        };
    }
}

// WikiParserのシングルトンインスタンス
const wikiParser = new WikiParser();