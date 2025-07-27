const express = require('express');
const path = require('path');
const fs = require('fs').promises;
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;

// ミドルウェア設定
app.use(cors());
app.use(express.json());
app.use(express.static('.'));

// ログ機能
const logMessage = (level, message, data = null) => {
    const timestamp = new Date().toISOString();
    const logEntry = {
        timestamp,
        level,
        message,
        data
    };
    console.log(JSON.stringify(logEntry));
};

// 環境データのサンプル
const environmentsData = {
    environments: [
        {
            id: 'dev',
            name: '開発環境 (DEV)',
            displayName: 'DEV',
            status: 'operational',
            database: 'Oracle',
            channel: '#dev-環境',
            version: 'v8.2.1',
            url: 'https://dev.example.com',
            healthCheck: 'https://dev.example.com/health',
            services: [
                { 
                    name: 'マルチカンパニー', 
                    enabled: true
                },
                { 
                    name: 'マルチパーソン', 
                    enabled: true
                }
            ],
            credentials: {
                username: 'dev_user',
                password: 'dev_password123'
            },
            deployActions: [
                { name: 'ユニットデプロイ', endpoint: '/api/deploy/unit' },
                { name: 'ユニットデプロイ（dbscript）', endpoint: '/api/deploy/unit-db' }
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
            healthCheck: 'https://stg.example.com/health',
            services: [
                { 
                    name: 'マルチカンパニー', 
                    enabled: true
                },
                { 
                    name: 'マルチパーソン', 
                    enabled: false
                }
            ],
            credentials: {
                username: 'stg_user',
                password: 'stg_password456'
            },
            deployActions: [
                { name: 'ユニットデプロイ', endpoint: '/api/deploy/unit' },
                { name: 'ユニットデプロイ（dbscript）', endpoint: '/api/deploy/unit-db' }
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
            healthCheck: 'https://uat.example.com/health',
            services: [
                { 
                    name: 'マルチカンパニー', 
                    enabled: false
                },
                { 
                    name: 'マルチパーソン', 
                    enabled: false
                }
            ],
            credentials: {
                username: 'uat_user',
                password: 'uat_password789'
            },
            deployActions: [
                { name: 'ユニットデプロイ', endpoint: '/api/deploy/unit' },
                { name: 'ユニットデプロイ（dbscript）', endpoint: '/api/deploy/unit-db' }
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
            healthCheck: 'https://demo.example.com/health',
            services: [
                { 
                    name: 'マルチカンパニー', 
                    enabled: true
                },
                { 
                    name: 'マルチパーソン', 
                    enabled: false
                }
            ],
            credentials: {
                username: 'demo_user',
                password: 'demo_password000'
            },
            deployActions: [
                { name: 'ユニットデプロイ', endpoint: '/api/deploy/unit' },
                { name: 'ユニットデプロイ（dbscript）', endpoint: '/api/deploy/unit-db' }
            ]
        }
    ]
};

// API エンドポイント

// 環境一覧の取得
app.get('/api/environments', (req, res) => {
    logMessage('info', 'Environments API called');
    res.json(environmentsData);
});

// 単一環境の取得
app.get('/api/environments/:id', (req, res) => {
    const envId = req.params.id;
    const environment = environmentsData.environments.find(env => env.id === envId);
    
    if (!environment) {
        logMessage('warn', `Environment not found: ${envId}`);
        return res.status(404).json({ error: 'Environment not found' });
    }
    
    logMessage('info', `Environment details requested: ${envId}`);
    res.json(environment);
});

// ヘルスチェック
app.get('/api/health/:envId', (req, res) => {
    const envId = req.params.envId;
    const environment = environmentsData.environments.find(env => env.id === envId);
    
    if (!environment) {
        return res.status(404).json({ error: 'Environment not found' });
    }
    
    // シミュレートされたヘルスチェック結果
    const healthStatus = {
        environment: envId,
        status: environment.status,
        timestamp: new Date().toISOString(),
        responseTime: Math.floor(Math.random() * 500) + 100,
        services: environment.services.map(service => ({
            name: service.name,
            enabled: service.enabled
        }))
    };
    
    logMessage('info', `Health check requested: ${envId}`, healthStatus);
    res.json(healthStatus);
});

// バッチヘルスチェック
app.post('/api/health/batch', (req, res) => {
    const { urls } = req.body;
    
    if (!urls || !Array.isArray(urls)) {
        return res.status(400).json({ error: 'URLs array is required' });
    }
    
    // シミュレートされたヘルスチェック結果
    const results = urls.map(url => {
        const isHealthy = Math.random() > 0.2; // 80% の確率で正常
        return {
            url: url,
            status: isHealthy ? 'operational' : 'error',
            responseTime: Math.floor(Math.random() * 500) + 100,
            timestamp: new Date().toISOString()
        };
    });
    
    logMessage('info', `Batch health check requested for ${urls.length} URLs`);
    res.json(results);
});

// デプロイメント実行
app.post('/api/deploy/:envId/:action', (req, res) => {
    const { envId, action } = req.params;
    const environment = environmentsData.environments.find(env => env.id === envId);
    
    if (!environment) {
        return res.status(404).json({ error: 'Environment not found' });
    }
    
    const deployAction = environment.deployActions?.find(a => a.name.includes(action));
    
    if (!deployAction) {
        return res.status(400).json({ error: 'Deploy action not found' });
    }
    
    // シミュレートされたデプロイメント結果
    const deployResult = {
        environment: envId,
        action: action,
        status: 'started',
        deploymentId: `deploy_${Date.now()}`,
        timestamp: new Date().toISOString()
    };
    
    logMessage('info', `Deployment started: ${envId} - ${action}`, deployResult);
    res.json(deployResult);
});

// デプロイメント状況取得
app.get('/api/deploy/:deploymentId/status', (req, res) => {
    const { deploymentId } = req.params;
    
    // シミュレートされたデプロイメント状況
    const statuses = ['running', 'completed', 'failed'];
    const randomStatus = statuses[Math.floor(Math.random() * statuses.length)];
    
    const deployStatus = {
        deploymentId: deploymentId,
        status: randomStatus,
        progress: randomStatus === 'running' ? Math.floor(Math.random() * 90) + 10 : 100,
        timestamp: new Date().toISOString()
    };
    
    logMessage('info', `Deployment status requested: ${deploymentId}`, deployStatus);
    res.json(deployStatus);
});

// ステータス更新（管理用）
app.put('/api/environments/:id/status', (req, res) => {
    const envId = req.params.id;
    const { status } = req.body;
    
    const environment = environmentsData.environments.find(env => env.id === envId);
    
    if (!environment) {
        return res.status(404).json({ error: 'Environment not found' });
    }
    
    if (!['operational', 'warning', 'error', 'maintenance'].includes(status)) {
        return res.status(400).json({ error: 'Invalid status' });
    }
    
    environment.status = status;
    
    logMessage('info', `Environment status updated: ${envId} -> ${status}`);
    res.json({ message: 'Status updated successfully', environment });
});

// サービスステータス更新（管理用）
app.put('/api/environments/:id/services/:serviceName/status', (req, res) => {
    const { id: envId, serviceName } = req.params;
    const { status } = req.body;
    
    const environment = environmentsData.environments.find(env => env.id === envId);
    
    if (!environment) {
        return res.status(404).json({ error: 'Environment not found' });
    }
    
    const service = environment.services.find(s => s.name === serviceName);
    
    if (!service) {
        return res.status(404).json({ error: 'Service not found' });
    }
    
    if (!['operational', 'warning', 'error'].includes(status)) {
        return res.status(400).json({ error: 'Invalid status' });
    }
    
    service.status = status;
    
    logMessage('info', `Service status updated: ${envId}/${serviceName} -> ${status}`);
    res.json({ message: 'Service status updated successfully', service });
});

// ダッシュボード設定取得
app.get('/api/dashboard/config', (req, res) => {
    const config = {
        title: '環境ステータスダッシュボード',
        refreshInterval: 60000,
        healthCheckTimeout: 5000,
        themes: ['light', 'dark'],
        defaultTheme: 'light'
    };
    
    res.json(config);
});

// エラーハンドリング
app.use((err, req, res, next) => {
    logMessage('error', 'Unhandled error', { error: err.message, stack: err.stack });
    res.status(500).json({ error: 'Internal server error' });
});

// 404 ハンドリング
app.use((req, res) => {
    logMessage('warn', `404 Not Found: ${req.method} ${req.url}`);
    res.status(404).json({ error: 'Not found' });
});

// サーバー起動
app.listen(PORT, () => {
    logMessage('info', `Environment Status Dashboard Server started on port ${PORT}`);
    logMessage('info', `Access dashboard at: http://localhost:${PORT}`);
});