# Deploying grd_backend on the LXD container

The container (`ci-bc-eos-1`) is just Ubuntu. This runs gunicorn under systemd,
bound directly to a **TCP port** — no nginx. The database is remote
(`ci-bc-eos-db-1…` in `.env`), so nothing Postgres runs in the container; it
only needs network access to that host. Static files (the Django admin's
CSS/JS) are served by WhiteNoise from inside gunicorn.

Assumptions:

| | |
| --- | --- |
| repo path | `/home/webadm/grd_backend` |
| run as user | `webadm` |
| virtualenv | `/home/webadm/grd_backend/.venv` |
| listen | `0.0.0.0:8000` (set by `GUNICORN_BIND` in `.env`) |

---

## 1. System packages

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
python3 --version        # must be >= 3.10
```

## 2. Python environment

```bash
cd ~/grd_backend
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

## 3. Environment file

`.env` is git-ignored — create it on the container:

```bash
cp .env.example .env
nano .env
```

Values that matter here:

```ini
DJANGO_DEBUG=False
DJANGO_HTTPS=False                       # plain HTTP on the port
DJANGO_SECRET_KEY=<64+ random chars — command below>
DJANGO_ALLOWED_HOSTS=ci-bc-eos-1,<lxd-host ip/name>,127.0.0.1,localhost
DJANGO_CSRF_TRUSTED_ORIGINS=http://<host>:8000
CORS_ALLOWED_ORIGINS=http://<your Next.js origin>

POSTGRES_DB=grd-dev-3.1
POSTGRES_USER=...
POSTGRES_PASSWORD=...
POSTGRES_HOST=ci-bc-eos-db-1.ent.dfo-mpo.ca
POSTGRES_PORT=5432
POSTGRES_SSLMODE=require
POSTGRES_SEARCH_PATH=public,grd,grd_ref,grd_validation

GUNICORN_BIND=0.0.0.0:8000
```

Secret key:

```bash
.venv/bin/python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

Check the DB is reachable from the container:

```bash
nc -vz "$POSTGRES_HOST" 5432
```

## 4. Migrate + collect static

```bash
.venv/bin/python manage.py migrate            # Django's own tables only
.venv/bin/python manage.py collectstatic --noinput
.venv/bin/python manage.py createsuperuser    # optional, for /admin/
```

> The `grd*` apps are `managed = False`; `migrate` never touches those tables.
> Pointed at the same DB you migrated locally, `migrate` is a no-op — expected.

## 5. Run it

**Quick test (foreground):**

```bash
.venv/bin/gunicorn -c gunicorn.conf.py config.wsgi:application
# -> http://<host>:8000/api/health/
```

**As a service:**

```bash
sudo cp deploy/grd-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now grd-backend
systemctl status grd-backend
```

Logs: `journalctl -u grd-backend -f`

## 6. Verify

```bash
curl -s http://localhost:8000/api/health/
curl -s http://localhost:8000/api/reports/options/species
curl -s -I http://localhost:8000/static/admin/css/base.css   # 200 via WhiteNoise
```

## 7. Reach it from outside the container

Run on the **LXD host** (not inside):

```bash
lxc config device add ci-bc-eos-1 grd-http proxy \
  listen=tcp:0.0.0.0:8000 connect=tcp:127.0.0.1:8000
```

API then at `http://<lxd-host>:8000/`. Point the frontend's
`NEXT_PUBLIC_API_URL` there and add that origin to `CORS_ALLOWED_ORIGINS`
and the host to `DJANGO_ALLOWED_HOSTS`.

---

## Updating after a push

```bash
cd ~/grd_backend
git pull
.venv/bin/pip install -r requirements.txt          # if it changed
.venv/bin/python manage.py migrate                 # if migrations changed
.venv/bin/python manage.py collectstatic --noinput # if static changed
sudo systemctl restart grd-backend
```

---

## Later: putting TLS in front

Add nginx (or use the LXD host's proxy) to terminate HTTPS, point it at
`127.0.0.1:8000`, then set `DJANGO_HTTPS=True` in `.env` and restart. A sample
`deploy/nginx.conf` is included for when you get there.

---

## Checklist

- [ ] `python3 --version` ≥ 3.10
- [ ] `DJANGO_DEBUG=False`, `DJANGO_HTTPS=False`, real `DJANGO_SECRET_KEY`
- [ ] `DJANGO_ALLOWED_HOSTS` has every name/IP you'll hit the API by
- [ ] `CORS_ALLOWED_ORIGINS` = the frontend URL
- [ ] `nc -vz $POSTGRES_HOST 5432` succeeds from the container
- [ ] `collectstatic` run
- [ ] `systemctl status grd-backend` active
- [ ] LXD host `proxy` device forwards the port
- [ ] auth decision on `reports/` (`AllowAny` today — see `reports/README.md`)
