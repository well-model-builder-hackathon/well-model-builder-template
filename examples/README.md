# Примеры запросов

- `input_data.json` — общий пример кейса. Это не готовый запрос к отдельному сервису.
- `ipr_request.json` — чистый запрос для `POST /ipr/calc`.
- `vlp_request.json` — чистый запрос для `POST /vlp/calculator`.
- `nodal_request.json` — пример запроса для `POST /nodal/calc` с двумя простыми кривыми.

## Как разложить общий пример

Для IPR:

```json
{
  "p_res": 200,
  "wct": 50,
  "pi": 1,
  "pb": 150
}
```

Здесь `wct` и `pb` берутся из `pvt.wct` и `pvt.pb`, а `p_res` и `pi` — с верхнего уровня.

Для VLP:

- берётся `inclinometry`, `casing`, `tubing`, `p_wh`, `geo_grad`, `h_res`;
- `pvt` передаётся без `pb`;
- `p_res` и `pi` VLP не нужны.

Для Nodal:

- сначала вызовите IPR и VLP;
- передайте их ответы как `ipr` и `vlp`.
