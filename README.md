# Garantias rurais (MVP)

SaaS multiempresa com Django 5.2 (GeoDjango) + PostGIS. Desenvolvimento via Docker.

## Pré-requisitos

- Docker e Docker Compose

## Subir o ambiente

```bash
docker compose up --build
```

- API/site: http://localhost:8000  
- Healthcheck: http://localhost:8000/health/

## Comandos úteis

```bash
# Migrações
docker compose run --rm web python manage.py migrate

# Testes
docker compose run --rm web python manage.py test

# Shell Django
docker compose run --rm web python manage.py shell
```

## Variáveis

Copie `.env.example` para `.env` e ajuste se necessário.

## Nota (Apple Silicon)

A imagem `postgis/postgis` pode avisar sobre plataforma amd64; normalmente roda via emulação. Se houver problema, defina `platform` no serviço `db` conforme a documentação da imagem para arm64.

## API (`/api/v1/`)

- JWT: `POST /api/v1/auth/token/` com corpo JSON `{"username": "<email>", "password": "..."}` (campo `username` do SimpleJWT contendo o e-mail).
- Recursos: `companies`, `users`, `properties`, `areas` (GeoJSON Feature / FeatureCollection), `guarantees`, `crop-seasons`, `commitments`, `plans`, `subscriptions`.
- `GET /api/v1/guarantees/<id>/export/` — HTML para impressão; `.../export.pdf/` — PDF (WeasyPrint).

## Mapa

- Após login em `/accounts/login/`, abra `/map/` — Leaflet + desenho de polígonos com sessão + CSRF nas chamadas à API.
