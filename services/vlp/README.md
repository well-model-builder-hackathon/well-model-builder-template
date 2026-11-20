# VLP service

Реализация сервиса VLP. Положите сюда код и `Dockerfile`.

- Порт: **8002**
- Расчёт: `POST /vlp/calc`
- Health: `GET /vlp/health`
- OpenAPI: `/docs`, `/openapi.json`

Запрос и ответ — см. [`../../docs/contracts.md`](../../docs/contracts.md) и
[`../../examples/vlp_request.json`](../../examples/vlp_request.json).

Дополнительные поля: `roughness`, `q_max`, `points`.
