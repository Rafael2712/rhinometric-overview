# --- STAGE 1: builder ---
FROM alpine:3.18 as builder
RUN apk add --no-cache python3 py3-pip
WORKDIR /build

# La ruta corregida: 'dist' debe estar en el contexto actual.
COPY dist/license_validator /validator 
RUN chmod +x /validator

# --- STAGE 2: stage-4 ---
FROM alpine:3.18 as stage-4
RUN apk add --no-cache supervisor nginx

# Copia los binarios de monitoreo desde las imágenes base
COPY --from=grafana /usr/share/grafana /usr/share/grafana
COPY --from=prometheus /bin/prometheus /usr/local/bin/prometheus
COPY --from=loki /usr/bin/loki /usr/local/bin/loki

# Copia el validador compilado
COPY --from=builder /validator /usr/local/bin/validator

# La ruta corregida: 'supervisord.conf' debe estar en el contexto actual.
COPY supervisord.conf /etc/supervisord.conf

# Copia el script de entrada corregido
COPY entrypoint-secure.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
