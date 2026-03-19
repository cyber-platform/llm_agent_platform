# Coalesce map FAQ: подробные вопросы и ответы

Этот документ дополняет краткую теорию в [`docs/theory/coalesce-map.md`](docs/theory/coalesce-map.md:1) и нормативный runtime design в [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:222).

Здесь собраны развернутые объяснения для тех, кто хочет понять не только **что** делает writer, но и **почему** он устроен именно так.

---

## 1) Почему здесь coalesce map, а не обычная очередь событий

Потому что в этом контуре нам нужен не полный журнал всех промежуточных изменений, а **последняя консистентная точка восстановления**.

Для каждого пути файла writer хранит только последний payload:

```text
pending[path] = latest_payload
```

Если за короткое время одно и то же состояние меняется много раз, на диск уйдёт только последняя версия.

Это осознанный компромисс:

- плюс: меньше I/O
- плюс: ниже latency на request-path
- плюс: проще storage semantics для PoC
- минус: промежуточные состояния не сохраняются

Если бы нам был нужен audit trail или строгая последовательность событий, пришлось бы использовать event log, очередь или WAL.

---

## 2) Что именно хранится в `pending`

`pending` — это не FIFO-очередь и не список всех событий.

Это map по уникальным путям файлов:

```text
pending = {
  path_1: payload_latest_for_path_1,
  path_2: payload_latest_for_path_2,
  path_3: payload_latest_for_path_3
}
```

Поэтому размер `pending` означает не число событий, а **число уникальных файлов, ожидающих записи**.

Следствие:

- 100 апдейтов одного и того же [`account_state.json`](docs/contracts/state/account-state.schema.json:1) всё равно занимают 1 слот
- 3 апдейта для трёх разных файлов занимают 3 слота

Именно поэтому [`STATE_WRITER_MAX_PENDING_FILES`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:250) ограничивает количество dirty paths, а не количество исторических событий.

---

## 3) Как выглядят mixed updates на практике

Представим, что у нас есть два аккаунта и один group snapshot:

- `acc1/account_state.json`
- `acc2/account_state.json`
- `groups/g0/quota_state.json`

Пришли события в таком порядке:

1. `A1` для `acc1/account_state.json`
2. `B1` для `acc2/account_state.json`
3. `A2` для `acc1/account_state.json`
4. `G1` для `groups/g0/quota_state.json`
5. `A3` для `acc1/account_state.json`

Тогда состояние `pending` меняется так:

```text
after A1: { acc1: A1 }
after B1: { acc1: A1, acc2: B1 }
after A2: { acc1: A2, acc2: B1 }
after G1: { acc1: A2, acc2: B1, group: G1 }
after A3: { acc1: A3, acc2: B1, group: G1 }
```

Что попадёт на диск на flush:

- для `acc1` будет записан `A3`
- для `acc2` будет записан `B1`
- для group snapshot будет записан `G1`

Промежуточные версии `A1` и `A2` не сохраняются, и это нормально: они не нужны как журнал, если routing уже живёт по in-memory состоянию.

---

## 4) Почему snapshot нужно формировать после обновления in-memory

Ключевой инвариант: snapshot должен отражать уже применённое runtime состояние.

Поэтому порядок действий должен быть таким:

1. router обновляет in-memory state
2. router формирует payload для account state и snapshot
3. router делает enqueue в writer

Если сначала enqueue, а потом менять память, можно получить snapshot, который отстаёт от фактического состояния роутера уже в момент постановки в очередь.

---

## 5) Что происходит, если во время flush приходят новые апдейты

Чтобы writer не блокировал новые обновления, flush выполняется через swap:

```text
lock
  to_flush = pending
  pending = {}
unlock

write all from to_flush
```

После swap новые события идут уже в новый `pending` и не смешиваются с текущим flush.

Пример:

```text
to_flush = { acc1: A3, acc2: B1, group: G1 }
pending = {}
```

Пока writer пишет `to_flush`, приходят:

- `A4` для `acc1`
- `G2` для group snapshot

Тогда новый `pending` становится:

```text
pending = { acc1: A4, group: G2 }
```

После успешного flush записи из нового `pending` **не удаляются**. Они будут записаны на следующем цикле.

---

## 6) Что значит merge-back при ошибке записи

Если flush упал, нельзя просто потерять локальный `to_flush`.

Поэтому writer делает fail-safe merge-back:

1. ловит ошибку записи
2. снова берёт lock
3. возвращает `to_flush` в новый `pending`
4. но не затирает более свежие payload, если они уже пришли после swap

Практическое правило:

- если `path` из `to_flush` отсутствует в новом `pending` → кладём обратно
- если `path` уже есть в новом `pending` → оставляем новое значение

Это защищает от двух проблем сразу:

- не теряем старые данные при write failure
- не откатываем более новые изменения назад

---

## 7) Что именно теряется при crash

При crash может потеряться только **последний хвост не-flushed изменений** между последним успешным flush и моментом падения процесса.

Что при этом остаётся безопасным:

- per-file запись остаётся атомарной через `tmp + replace`
- не возникает битых или partially written JSON файлов

Что остаётся допустимым для PoC, но неидеальным:

- один файл мог успеть записаться, другой нет
- [`quota_state.json`](docs/contracts/state/group-quota-state.schema.json:1) может временно отставать от [`account_state.json`](docs/contracts/state/account-state.schema.json:1)

Это допустимо, потому что:

- routing использует in-memory state как источник истины во время жизни процесса
- snapshot является monitoring-артефактом, а не operational source of truth
- после рестарта система может самовосстановиться через повторные сигналы quota/rate-limit

---

## 8) Почему для PoC это приемлемо

Если хвост state потерялся после краша, сервис обычно не ломает бизнес-логику, а лишь временно теряет часть накопленного runtime знания.

Что это значит на практике:

- exhausted аккаунт может быть повторно проверен и снова получить 429
- cooldown аккаунт может снова получить rate-limit и снова уйти в cooldown
- `last_used_at` может временно отстать, из-за чего случится лишний refresh

Это неприятно, но контролируемо.

Для текущего проекта такой компромисс выглядит разумно, потому что цена более строгих гарантий — это дополнительная сложность в виде WAL, журналов или транзакционного слоя.

---

## 9) Где такой паттерн обычно хорош

Coalesce map хорошо подходит, когда важнее быстро поддерживать актуальный snapshot, чем хранить всю историю изменений.

Типичные примеры:

1. write-behind persistence
2. UI state с частыми обновлениями
3. telemetry gauges
4. file watchers и indexers
5. reconciliation loops

Во всех этих случаях естественно хранить **последнее актуальное состояние**, а не каждый промежуточный шаг.

---

## 10) Когда такой паттерн применять нельзя

Не стоит использовать coalesce map как основной persistence-механизм, если системе нужен хотя бы один из следующих инвариантов:

- полный audit trail
- строгая последовательность событий
- невозможность терять промежуточные состояния
- транзакционная консистентность между множеством файлов или сущностей

В этих случаях нужен другой класс решений:

- event log
- message queue
- WAL или journal
- transactional storage

---

## 11) Как это соотносится с документацией проекта

Материалы разделены специально:

- [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:1) — канонический runtime design
- [`docs/theory/coalesce-map.md`](docs/theory/coalesce-map.md:1) — краткая теория и мотивация паттерна
- [`docs/theory/coalesce-map-faq.md`](docs/theory/coalesce-map-faq.md:1) — длинные примеры, reasoning и edge-cases

Так пользователь сам выбирает глубину погружения:

- прочитать только архитектурный контракт
- понять инженерную мотивацию паттерна
- разобрать поведение writer пошагово на вопросах и примерах
