@echo off
echo ========================================
echo VERIFICANDO PLATAFORMA RHINOMETRIC
echo ========================================
echo.

echo [1/4] Verificando contenedores...
docker ps --format "table {{.Names}}\t{{.Status}}" | findstr /C:"rhinometric-grafana" /C:"rhinometric-tempo" /C:"rhinometric-loki" /C:"rhinometric-prometheus"
echo.

echo [2/4] Verificando Grafana en puerto 3000...
curl -s -o NUL -w "HTTP Status: %%{http_code}\n" http://localhost:3000/api/health
echo.

echo [3/4] Reiniciando stack completo...
docker compose -f docker-compose-trial.yml restart
echo.

echo [4/4] Esperando 15 segundos...
timeout /t 15 /nobreak >nul
echo.

echo ========================================
echo VERIFICACION COMPLETADA
echo ========================================
echo.
echo Abre en tu navegador: http://localhost:3000
echo Usuario: admin
echo Password: admin_trial_2024
echo.
pause
