# VLP service

Реализация сервиса VLP. Положите сюда код и `Dockerfile`.

- Порт: **8002**
- Endpoint: `POST /vlp/calculator`
- Health: `GET /vlp/health`
- OpenAPI: `/docs` или `/openapi.json`

Запрос и ответ — см. [`../../docs/contracts.md`](../../docs/contracts.md) и
[`../../examples/vlp_request.json`](../../examples/vlp_request.json).

Дополнительные поля: `roughness`, `q_max`, `points`.
