const express = require('express');
const { register, dbQueryDuration } = require('../utils/metrics');

const router = express.Router();

// Endpoint para que Prometheus scrape las métricas
router.get('/', async (req, res) => {
  try {
    // Generar métricas simuladas de DB ocasionalmente
    if (Math.random() < 0.7) { // 70% chance de generar métricas
      const queryDurations = [
        Math.random() * 0.05 + 0.005, // 5-55ms
        Math.random() * 0.03 + 0.008, // 8-38ms
        Math.random() * 0.08 + 0.012  // 12-92ms
      ];
      queryDurations.forEach(duration => {
        dbQueryDuration.observe(duration);
      });
    }

    res.set('Content-Type', register.contentType);
    const metrics = await register.metrics();
    res.end(metrics);
  } catch (error) {
    console.error('Error generating metrics:', error);
    res.status(500).end(error.toString());
  }
});

module.exports = router;