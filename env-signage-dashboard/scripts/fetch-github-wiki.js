// GitHub Wiki情報取得スクリプト
const https = require('https');
const fs = require('fs').promises;
const path = require('path');

class GitHubWikiFetcher {
    constructor() {
        this.token = process.env.GITHUB_TOKEN;
        
        if (!this.token) {
            throw new Error('GITHUB_TOKEN environment variable is required');
        }
    }

    // HTTP GET リクエスト
    async httpGet(url, headers = {}) {
        return new Promise((resolve, reject) => {
            const options = {
                headers: {
                    'Authorization': `token ${this.token}`,
                    'Accept': 'application/vnd.github.v3+json',
                    'User-Agent': 'env-signage-dashboard',
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

    // GitHubリポジトリ情報の抽出
    parseGitHubWikiUrl(url) {
        // https://github.com/owner/repo/wiki/PageName
        const match = url.match(/github\.com\/([^\/]+)\/([^\/]+)\/wiki\/(.+)/);
        if (!match) {
            throw new Error(`Invalid GitHub Wiki URL: ${url}`);
        }

        return {
            owner: match[1],
            repo: match[2],
            pageName: match[3]
        };
    }

    // Wikiページコンテンツの取得
    async getWikiPageContent(owner, repo, pageName) {
        // GitHub API v3を使用してWikiコンテンツを取得
        const url = `https://api.github.com/repos/${owner}/${repo}/contents/wiki/${pageName}.md`;
        
        console.log(`Fetching GitHub Wiki: ${owner}/${repo}/wiki/${pageName}`);
        
        try {
            const data = await this.httpGet(url);
            
            if (data.content) {
                // Base64デコード
                const content = Buffer.from(data.content, 'base64').toString('utf8');
                return content;
            } else {
                throw new Error('No content found in response');
            }
        } catch (error) {
            // API経由でアクセスできない場合は、raw URLで試行
            console.log(`API access failed, trying raw URL...`);
            return await this.getRawWikiContent(owner, repo, pageName);
        }
    }

    // Raw URLからWikiコンテンツを取得（フォールバック）
    async getRawWikiContent(owner, repo, pageName) {
        const rawUrl = `https://raw.githubusercontent.com/wiki/${owner}/${repo}/${pageName}.md`;
        
        return new Promise((resolve, reject) => {
            const req = https.get(rawUrl, (res) => {
                let data = '';
                
                res.on('data', (chunk) => {
                    data += chunk;
                });
                
                res.on('end', () => {
                    if (res.statusCode >= 200 && res.statusCode < 300) {
                        resolve(data);
                    } else {
                        reject(new Error(`HTTP ${res.statusCode}: Failed to fetch raw content`));
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

    // GitHub Wikiからデータを取得
    async fetchFromGitHubWiki(sourceConfig) {
        try {
            const urlInfo = this.parseGitHubWikiUrl(sourceConfig.url);
            const content = await this.getWikiPageContent(urlInfo.owner, urlInfo.repo, urlInfo.pageName);
            
            // マークダウン解析
            const environments = this.parseMarkdownContent(content, sourceConfig);
            
            console.log(`Successfully fetched ${environments.length} environments from ${sourceConfig.name}`);
            return environments;
            
        } catch (error) {
            console.error(`Failed to fetch from GitHub Wiki:`, error.message);
            return [];
        }
    }

    // マークダウンコンテンツの解析
    parseMarkdownContent(content, sourceConfig) {
        const environments = [];
        
        try {
            const lines = content.split('\n');
            let inTable = false;
            let headers = [];
            
            for (const line of lines) {
                const trimmedLine = line.trim();
                
                // テーブルの開始を検出
                if (trimmedLine.includes('|') && !inTable) {
                    headers = trimmedLine.split('|')
                        .map(h => h.trim())
                        .filter(h => h);
                    inTable = true;
                    continue;
                }
                
                // テーブルの区切り行をスキップ
                if (inTable && trimmedLine.match(/^\|[\s\-\|]+\|$/)) {
                    continue;
                }
                
                // テーブル行の処理
                if (inTable && trimmedLine.includes('|')) {
                    const cells = trimmedLine.split('|')
                        .map(c => c.trim())
                        .filter(c => c);
                    
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
                                wiki: 'github_wiki',
                                page: sourceConfig.name,
                                updated: new Date().toISOString()
                            },
                            services: []
                        };
                        
                        environments.push(env);
                    }
                } else if (inTable && !trimmedLine.includes('|') && trimmedLine !== '') {
                    // テーブル終了
                    break;
                }
            }
        } catch (error) {
            console.error('Failed to parse markdown content:', error.message);
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
        console.log('Starting GitHub Wiki data fetch...');
        
        // 設定ファイルの読み込み
        const configPath = path.join(__dirname, '..', 'config', 'wiki-sources.json');
        const configData = await fs.readFile(configPath, 'utf8');
        const config = JSON.parse(configData);
        
        // GitHub Wikiソースを抽出
        const githubSources = config.sources.filter(source => source.type === 'github_wiki');
        
        if (githubSources.length === 0) {
            console.log('No GitHub Wiki sources found in configuration');
            return;
        }

        const fetcher = new GitHubWikiFetcher();
        const allEnvironments = [];

        // 各GitHub Wikiソースからデータを取得
        for (const source of githubSources) {
            console.log(`Processing GitHub Wiki source: ${source.name}`);
            const environments = await fetcher.fetchFromGitHubWiki(source);
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

        // GitHub Wikiからのデータで既存データを更新
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
        
        console.log(`Successfully updated cache with ${allEnvironments.length} environments from GitHub Wiki`);
        console.log(`Total environments in cache: ${updatedEnvironments.length}`);
        
    } catch (error) {
        console.error('Failed to fetch GitHub Wiki data:', error.message);
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

module.exports = { GitHubWikiFetcher };