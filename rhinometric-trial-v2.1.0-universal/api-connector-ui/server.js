#!/usr/bin/env node

/**
 * ═══════════════════════════════════════════════════════════════════════════
 *  RHINOMETRIC API CONNECTOR UI - STANDALONE SERVER
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * Simple static file server for the API Connector UI
 * Runs on port 8091 by default
 * 
 * Usage:
 *   node server.js
 * ═══════════════════════════════════════════════════════════════════════════
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 8091;

const mimeTypes = {
    '.html': 'text/html',
    '.js': 'text/javascript',
    '.css': 'text/css',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon'
};

const server = http.createServer((req, res) => {
    // Enable CORS
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }

    let filePath = '.' + req.url;
    if (filePath === './') {
        filePath = './index.html';
    }

    const extname = String(path.extname(filePath)).toLowerCase();
    const contentType = mimeTypes[extname] || 'application/octet-stream';

    fs.readFile(filePath, (error, content) => {
        if (error) {
            if (error.code === 'ENOENT') {
                res.writeHead(404, { 'Content-Type': 'text/html' });
                res.end('<h1>404 - File Not Found</h1>', 'utf-8');
            } else {
                res.writeHead(500);
                res.end('Server Error: ' + error.code);
            }
        } else {
            res.writeHead(200, { 'Content-Type': contentType });
            res.end(content, 'utf-8');
        }
    });
});

server.listen(PORT, () => {
    console.log('╔════════════════════════════════════════════════════════════╗');
    console.log('║   RHINOMETRIC API CONNECTOR UI v2.1.0                     ║');
    console.log('╚════════════════════════════════════════════════════════════╝');
    console.log('');
    console.log(`✓ Server running at http://localhost:${PORT}`);
    console.log('✓ CORS enabled');
    console.log('');
    console.log('Press Ctrl+C to stop');
});
