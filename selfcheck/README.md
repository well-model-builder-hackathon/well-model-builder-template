# Публичная проверка

Минимальная публичная проверка JSON-контрактов IPR, VLP и Nodal.

Она **не является итоговой оценкой**. Здесь проверяется только то, что сервис
принимает запрос, возвращает JSON нужной формы и не отдаёт `NaN/Inf`.
Все расчётные проверки, golden-кривые, валидация граничных случаев и E2E
находятся в приватном grader.

## Установка

```bash
python -m pip install -r selfcheck/requirements.txt
```

## Запуск

Если сервисы уже подняты:

```bash
python -m pytest selfcheck/tests -v --no-stack
```

Если хотите, чтобы тесты сами подняли compose:

```bash
python -m pytest selfcheck/tests -v --compose-file docker-compose.yml
```

В GitHub Actions проверка состава репозитория запускается всегда, а JSON-тесты —
только когда во всех трёх `services/*` уже есть `Dockerfile`. Пока сервисов нет,
workflow остаётся зелёным и пишет, что реализации ещё не добавлены.

Selfcheck запускает только core-сервисы `ipr`, `vlp` и `nodal`.
Backend, frontend и AI-помощник в проверке не участвуют. Если нужно добавить
другие сервисы в запуск, используйте:

```bash
python -m pytest selfcheck/tests -v \
  --compose-file docker-compose.yml \
  --services "ipr vlp nodal"
```

Полезные опции:

- `--keep-stack` — не гасить compose после тестов;
- `--stack-timeout 300` — увеличить ожидание readiness;
- `--ipr-url`, `--vlp-url`, `--nodal-url` — переопределить адреса.

## Что проверяется

- `POST /ipr/calc` возвращает JSON с `q_liq` и `p_wf`;
- `POST /vlp/calculator` возвращает JSON с `q_liq` и `p_wf`;
- `POST /nodal/calc` возвращает массив ровно из одной точки;
- состав репозитория: `.idea`, `venv`, кэши, логи, `.env`, большие файлы
  и другие нежелательные артефакты.

Проверка состава запускается и локально:

```bash
python selfcheck/repo_hygiene.py .
```

Если в репозитории есть `.idea` или `venv`, selfcheck покажет это до пуша.
Этого достаточно, чтобы проверить, что сервисы собрались и репозиторий чистый.
Полную проверку расчётов участник увидит только в результатах приватной проверки.
