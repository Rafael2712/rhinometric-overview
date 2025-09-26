# Demo "mi-proyecto" (acceso controlado por VPN Tailscale)

## Servicios (sólo localhost en la VM)
- App:        http://127.0.0.1/
- Grafana:    http://127.0.0.1:3002  (admin / pass de demo)
- Prometheus: http://127.0.0.1:9090
- Loki:       http://127.0.0.1:3100

## Ciclo de vida
- Start:  ./demo/start-demo.sh
- Status: ./demo/status-demo.sh
- Stop:   ./demo/stop-demo.sh

## Seguridad
- Nada expuesto a Internet; sólo 127.0.0.1.
- El acceso de testers se hace vía VPN Tailscale (IP privada 100.x.y.z).
- Puedes revocar acceso en cualquier momento desde el panel de Tailscale.
