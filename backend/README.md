# Backend

Обязательная часть системы. Автоматическая проверка покрывает только IPR, VLP
и Nodal; backend оценивается на демо и live-защите.

## Что положить сюда

Код backend и `Dockerfile`. Порт — **8080**.

Рекомендуемый минимум:

- `GET /health`;
- `POST /api/sessions`;
- `POST /api/sessions/{id}/messages`;
- `POST /api/scenarios`;
- `GET /api/scenarios/{id}`;
- `POST /api/scenarios/{id}/calculate`;
- `POST /api/scenarios/{id}/what-if`;
- `GET /api/scenarios/{id}/report`.

Backend:

- нормализует единицы;
- вызывает IPR `8003`, VLP `8002`, Nodal `8004`;
- убирает отрицательный численный шум перед Nodal;
- хранит сценарии;
- отдаёт API для frontend и AI-помощника;
- не вызывает расчётные сервисы напрямую из frontend.

## Запуск

Только core-сервисы:

```bash
docker compose up -d --build ipr vlp nodal
```

Полное приложение:

```bash
docker compose --profile app up -d --build
```
