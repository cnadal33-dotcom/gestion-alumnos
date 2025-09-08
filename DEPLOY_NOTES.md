# SEGURBOX · Notas de despliegue

## Nginx (vhost PRO+)
- HTTP→HTTPS (80→443), excepción **ACME** en `/.well-known/acme-challenge/` (root: `/var/www/letsencrypt`).
- Prefijo de app: **/app**.
- Rutas **públicas** (sin auth):
  - `/app/alumnos/**`
  - `/app/examenes/hacer_examen/**`
- Todo lo demás bajo `/app/` **protegido** (Basic Auth).
- Estáticos cacheables:
  - `/static/` y `/app/static/` → alias a `/home/carlos/gestion-alumnos/mi_plataforma_formacion_app/static/`.
- Redirecciones raíz→/app: si alguien entra en `/(alumnos|formaciones|...)/` redirige a `/app/...`.
- `proxy_redirect / /app/;` para conservar el prefijo en cualquier redirección del backend.
- Logs:  
  - access: `/var/log/nginx/gestion-alumnos.access.log`  
  - error:  `/var/log/nginx/gestion-alumnos.error.log`

## Scripts operativos
- Deploy de CSS: `/usr/local/bin/deploy_static_css.sh`
  - Log: `/var/log/segurbox/deploy_static_css.log`
- Smoke: `/usr/local/bin/segurbox_smoke.sh`
- Timer semanal (Lunes 03:00 UTC): `segurbox-deploy-static-css.timer`

## Comprobaciones rápidas
```bash
# Nginx
sudo nginx -t && sudo systemctl reload nginx

# Prefijos y auth
curl -I http://app.segurbox.com               # 301 → https
curl -I https://app.segurbox.com/             # 200 portada
curl -I https://app.segurbox.com/app/         # 401 (protegido)
curl -I https://app.segurbox.com/app/alumnos/acceso_formacion    # 200 (público)
curl -I https://app.segurbox.com/app/formaciones/                # 401 (esperado)

# Estáticos cacheables
curl -I https://app.segurbox.com/app/static/css/app.css

# ACME (si existe el fichero, debe 200)
curl -I https://app.segurbox.com/.well-known/acme-challenge/test-ngx

Problemas conocidos/noise en logs

Escaneos a /owa/, /.env, /favicon.ico, etc. — ya se bloquean o devuelven 204/404 sin afectar a la app.
```
