# IPR service

Реализация сервиса IPR. Положите сюда код и `Dockerfile`.

- Порт: **8003**
- Endpoint: `POST /ipr/calc`
- Health/OpenAPI: `/docs` или `/swagger-ui`

Запрос:

```json
{"p_res": 200, "wct": 50, "pi": 1, "pb": 150}
```

Ответ:

```json
{"q_liq": [139.98, 137.93, "...", 0.0], "p_wf": [1.0, 10.95, "...", 200.0]}
```

Полный контракт: [`../../docs/contracts.md`](../../docs/contracts.md).
