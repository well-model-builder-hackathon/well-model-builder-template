# Nodal service

Реализация сервиса узлового анализа. Положите сюда код и `Dockerfile`.

- Порт: **8004**
- Расчёт: `POST /nodal/calc`
- Health: `GET /nodal/health`
- OpenAPI: `/docs`, `/openapi.json`

Nodal принимает **две готовые кривые** IPR и VLP, а не исходные данные скважины.
Ответ — массив ровно из одной точки.

Полный контракт: [`../../docs/contracts.md`](../../docs/contracts.md).
