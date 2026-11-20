# Well Model Builder

Стартовый репозиторий хакатона **«Система построения моделей скважин»**.

Модель скважины — это результат узлового анализа: пересечение кривых IPR и VLP.
Участники реализуют три HTTP-сервиса:

- **IPR** — кривая притока;
- **VLP** — кривая подъёма;
- **Nodal** — точка пересечения IPR и VLP.

## Что внутри

```text
.
├── docker-compose.yml          # шаблон для трёх сервисов
├── .env.example
├── docs/
│   └── contracts.md            # контракты IPR / VLP / Nodal
├── examples/
│   ├── input_data.json         # общий пример входных данных кейса
│   ├── ipr_request.json
│   ├── vlp_request.json
│   └── nodal_request.json
├── services/
│   ├── ipr/README.md           # сюда кладётся реализация IPR
│   ├── vlp/README.md           # сюда кладётся реализация VLP
│   └── nodal/README.md         # сюда кладётся реализация Nodal
├── backend/README.md           # обязательный backend
├── frontend/README.md          # обязательный frontend
├── ai_assistant/README.md      # обязательный AI-помощник
└── selfcheck/
    ├── conftest.py
    ├── helpers.py
    ├── pytest.ini
    ├── requirements.txt
    ├── cases/public/           # публичные входы и ожидаемые значения
    └── tests/                  # публичные тесты
```

Готовых реализаций сервисов здесь нет. `services/*` содержат только контракты и место для кода.

`backend/`, `frontend/` и `ai_assistant/` — обязательные части системы.
Автоматическая проверка покрывает только IPR, VLP и Nodal; слой приложения
оценивается на демо и live-защите.

## Порты

| Сервис | Порт | Расчёт | Health |
|---|---:|---|---|
| VLP | 8002 | `POST /vlp/calc` | `GET /vlp/health` |
| IPR | 8003 | `POST /ipr/calc` | `GET /ipr/health` |
| Nodal | 8004 | `POST /nodal/calc` | `GET /nodal/health` |
| Backend | 8080 | `/api/*` | `GET /health` |
| Frontend | 3000 | дашборд | — |

Порты 8002/8003/8004 на хосте должны быть именно такими: по ним работает `selfcheck`.
Backend и frontend запускаются только под профилем `app`.

Health у расчётных сервисов одинаковый: `GET /<service>/health` →
`{"status": "ok", "service": "<service>"}`. OpenAPI: `/docs` и `/openapi.json`.

## Быстрый старт

1. Реализуйте сервисы в `services/ipr`, `services/vlp`, `services/nodal`.
2. Добавьте в каждую папку `Dockerfile`.
3. Поднимите стек:

   ```bash
   docker compose up -d --build
   ```

4. Установите зависимости self-check:

   ```bash
   python -m pip install -r selfcheck/requirements.txt
   ```

5. Запустите публичную проверку:

   ```bash
   python -m pytest selfcheck/tests -v --no-stack
   ```

`selfcheck` можно запустить и так, чтобы он сам поднял compose:

```bash
python -m pytest selfcheck/tests -v --compose-file docker-compose.yml
```

Публичная проверка запускает только core-сервисы:

```bash
docker compose up -d --build ipr vlp nodal
```

Полное приложение с backend и frontend:

```bash
docker compose --profile app up -d --build
```

## Слой приложения

`backend/`, `frontend/` и `ai_assistant/` — обязательные части системы.
Автоматическая проверка хакатона их не запускает и не оценивает:
она покрывает только IPR, VLP и Nodal.
Защита и оценка слоя приложения — на демо и live-защите.

## Публичная проверка

`selfcheck` — это **публичная минимальная проверка JSON-контракта и состава
репозитория**. Она проверяет форму ответов IPR, VLP и Nodal, а также то,
что в репозиторий не попали `.idea`, `venv`, кэши, `.env` и другие артефакты.
Точность расчёта она не проверяет. Её можно читать, запускать и менять.

Все расчётные проверки, golden-кривые, валидация граничных случаев и E2E
находятся в приватном grader. Итоговую проверку организаторы запускают
отдельно, на скрытых данных.

На каждый push GitHub Actions запускает `.github/workflows/selfcheck.yml`.
Проверка состава репозитория выполняется всегда. JSON-тесты запускаются только
после того, как во всех трёх `services/*` появится `Dockerfile`; до этого
workflow остаётся зелёным и напоминает, что реализации ещё нет.

## Важно про входные данные

**IPR** — `POST /ipr/calc`:

```json
{
  "p_res": 200,
  "wct": 50,
  "pi": 1,
  "pb": 150
}
```

- `p_res`, `pb` — атм;
- `wct` — %;
- `pi` — м³/сут/атм.

**VLP** — `POST /vlp/calc`:

```json
{
  "inclinometry": {"MD": [0, 1000, 1500], "TVD": [0, 1000, 1100]},
  "casing": {"d": 0.1},
  "tubing": {"d": 0.062, "h_mes": 1000},
  "pvt": {
    "wct": 50,
    "rp": 100,
    "gamma_oil": 0.8,
    "gamma_gas": 0.7,
    "gamma_wat": 1.0,
    "t_res": 90
  },
  "p_wh": 10,
  "geo_grad": 3,
  "h_res": 1500,
  "roughness": 0.0001,
  "q_max": 400,
  "points": 21
}
```

- длины — м;
- давления — атм;
- температура — °C;
- `wct` — %;
- `rp` — м³/т;
- `roughness`, `q_max`, `points` — опциональные.

**Nodal** — `POST /nodal/calc`:

```json
{
  "ipr": {"q_liq": [139.98, "...", 0.0], "p_wf": [1.0, "...", 200.0]},
  "vlp": {"q_liq": [0.0, "...", 400.0], "p_wf": [47.48, "...", 62.16]}
}
```

- Nodal принимает две готовые кривые;
- `q_liq` — м³/сут;
- `p_wf` — атм;
- ответ — массив ровно из одной точки.

`examples/input_data.json` — общий пример кейса. Для прямых вызовов используйте
`examples/ipr_request.json`, `examples/vlp_request.json` и `examples/nodal_request.json`.

Подробные контракты — в [`docs/contracts.md`](docs/contracts.md).

## Ограничения

- В зачёт входит только один режим — одна рабочая точка.
- Multi-intersection не тестируется.
- Nodal возвращает массив ровно из одной точки.
- Все давления — атм, дебиты — м³/сут, длины — м.
