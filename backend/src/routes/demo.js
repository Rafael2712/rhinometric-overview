const express = require('express');
const logger = require('../utils/logger');
const { dbQueryDuration } = require('../utils/metrics');

const router = express.Router();

// Simulador de métricas de base de datos
router.get('/simulate-db', async (req, res) => {
    try {
        // Simular diferentes tipos de consultas con diferentes duraciones
        const queryTypes = [
            { type: 'SELECT users', duration: Math.random() * 0.05 + 0.01 }, // 10-60ms
            { type: 'SELECT orgs', duration: Math.random() * 0.03 + 0.005 }, // 5-35ms  
            { type: 'UPDATE user', duration: Math.random() * 0.1 + 0.02 }, // 20-120ms
            { type: 'INSERT log', duration: Math.random() * 0.02 + 0.005 }, // 5-25ms
        ];

        const selectedQuery = queryTypes[Math.floor(Math.random() * queryTypes.length)];
        
        // Simular la duración de la consulta
        await new Promise(resolve => setTimeout(resolve, selectedQuery.duration * 1000));
        
        // Registrar la métrica
        dbQueryDuration.observe(selectedQuery.duration);

        logger.info('Simulated DB query', { 
            type: selectedQuery.type, 
            duration: `${selectedQuery.duration.toFixed(3)}s` 
        });

        res.json({
            message: 'Database query simulated',
            query_type: selectedQuery.type,
            duration: selectedQuery.duration,
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        logger.error('Simulation error:', error.message);
        res.status(500).json({
            error: 'Simulation Error',
            message: error.message
        });
    }
});

// Endpoint para generar errores 5xx (para SLA compliance)
router.get('/error-test', (req, res) => {
    const shouldError = Math.random() < 0.3; // 30% chance de error
    
    if (shouldError) {
        logger.error('Simulated 500 error for SLA testing');
        res.status(500).json({
            error: 'Simulated Error',
            message: 'This is a test error for SLA compliance metrics'
        });
    } else {
        res.json({
            message: 'Success response for SLA testing',
            timestamp: new Date().toISOString()
        });
    }
});

// Endpoint de demo para generar tráfico variado
router.get('/demo-traffic', async (req, res) => {
    // Simular procesamiento con duración variable
    const processingTime = Math.random() * 0.2 + 0.01; // 10-210ms
    await new Promise(resolve => setTimeout(resolve, processingTime * 1000));
    
    res.json({
        message: 'Demo traffic endpoint',
        processing_time: processingTime,
        server_time: new Date().toISOString(),
        random_data: Math.floor(Math.random() * 1000)
    });
});

module.exports = router;