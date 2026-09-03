# Deploying grd_backend on an LXD container

The container is just Ubuntu — a normal gunicorn + systemd + nginx Django
deploy. The database is remote (`ci-bc-eos-db-1…` in `.env`), so nothing
Postgres runs in the container; it only needs network access to that host.

Paths below assume the repo at **`/opt/grd_backend`**. Adjust to taste.

---

## 1. One-time system setup (inside the container)

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx git

# move the clone into place (or clone straight there)
sudo mkdir -p /opt/grd_backend
sudo chown "$USER":"$USER" /opt/grd_backend
git clone https://github.com/dfo-pacific-science/grd_backend.git /opt/grd_backend
cd /opt/grd_backend
```

## 2. Python environment

```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

## 3. Environment file

`.env` is git-ignored — create it on the server. Start from the example:

```bash
cp .env.example .env
nano .env
```

Production values that matter:

```ini
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<64+ random chars — see below>
DJANGO_ALLOWED_HOSTS=<container hostname>,<domain>,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=https://<domain>
CORS_ALLOWED_ORIGINS=https://<your Next.js origin>

# database — same block you used locally
POSTGRES_DB=grd-dev-3.1
POSTGRES_USER=...
POSTGRES_PASSWORD=...
POSTGRES_HOST=ci-bc-eos-db-1.ent.dfo-mpo.ca
POSTGRES_PORT=5432
POSTGRES_SSLMODE=require
POSTGRES_SEARCH_PATH=public,grd,grd_ref,grd_validation

# behind nginx on the same host
GUNICORN_BIND=unix:/run/grd-backend/gunicorn.sock
```

Generate a secret key:

```bash
.venv/bin/python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

## 4. Migrate + collect static

```bash
.venv/bin/python manage.py migrate           # creates auth/session/admin tables
.venv/bin/python manage.py collectstatic --noinput
.venv/bin/python manage.py createsuperuser    # optional, for /admin/
```

> The `grd*` apps are `managed = False`, so `migrate` only touches Django's own
> tables. If this container points at the **same** database you already
> migrated locally, `migrate` is a no-op — that's fine.

## 5. Gunicorn service

```bash
sudo cp deploy/grd-backend.service /etc/systemd/system/
# the unit runs as www-data — let it read the repo + write the socket dir
sudo chown -R www-data:www-data /opt/grd_backend
sudo systemctl daemon-reload
sudo systemctl enable --now grd-backend
sudo systemctl status grd-backend
```

Logs: `journalctl -u grd-backend -f`

## 6. nginx

```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/grd-backend
sudo ln -sf /etc/nginx/sites-available/grd-backend /etc/nginx/sites-enabled/grd-backend
sudo rm -f /etc/nginx/sites-enabled/default
# edit server_name in the file first
sudo nginx -t && sudo systemctl reload nginx
```

## 7. Verify

```bash
curl -s http://localhost/api/health/            # {"status": "ok"}
curl -s http://localhost/api/reports/options/species
```

From outside, hit the container's IP / the LXD proxy device you forward to it.

---

## Updating after a push

```bash
cd /opt/grd_backend
sudo -u www-data git pull
.venv/bin/pip install -r requirements.txt          # if it changed
.venv/bin/python manage.py migrate                 # if migrations changed
.venv/bin/python manage.py collectstatic --noinput # if static changed
sudo systemctl restart grd-backend
```

## Exposing the container (on the LXD host)

Forward a host port to the container, e.g.:

```bash
lxc config device add grd-backend http proxy \
  listen=tcp:0.0.0.0:8080 connect=tcp:127.0.0.1:80
```

Then the API is at `http://<lxd-host>:8080/`. Point `NEXT_PUBLIC_API_URL` there
(and add that origin to `CORS_ALLOWED_ORIGINS` / `DJANGO_ALLOWED_HOSTS`).

---

## Checklist

- [ ] `DJANGO_DEBUG=False` and a real `DJANGO_SECRET_KEY`
- [ ] `DJANGO_ALLOWED_HOSTS` includes the hostname/domain you'll hit
- [ ] `DJANGO_CSRF_TRUSTED_ORIGINS` + `CORS_ALLOWED_ORIGINS` set to the frontend URL
- [ ] DB reachable from the container (`.venv/bin/python manage.py dbshell` or `nc -vz $POSTGRES_HOST 5432`)
- [ ] `collectstatic` run so `/admin/` has its CSS
- [ ] `systemctl status grd-backend` active, `nginx -t` passes
- [ ] decide auth on `reports/` (`AllowAny` today — see `reports/README.md`)
