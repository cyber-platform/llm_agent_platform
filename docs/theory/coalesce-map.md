# Coalesce map (last-write-wins buffer): теория и применение

## TL;DR

**Coalesce map** — это приём, когда мы принимаем много обновлений состояния и **схлопываем** их по ключу, сохраняя только *последнее* значение (last-write-wins), а затем периодически делаем **батчевую запись** (flush) наружу: на диск, в БД, в сеть.

В нашем прокси coalesce map используется как часть write-behind persistence для state-файлов: request-path работает быстро по in-memory, а запись на диск идёт асинхронно.

Связанный дизайн: [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:1).

Для пошагового углубления:

- нормативная архитектура и runtime contract: [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:1)
- подробный FAQ с примерами mixed updates, swap, merge-back и crash semantics: [`docs/theory/coalesce-map-faq.md`](docs/theory/coalesce-map-faq.md:1)

---

## 1) Что это: структура данных vs приём vs паттерн

1) **Структура данных**
- `hash map / dict` (ключ → значение).

2) **Алгоритмический приём**
- *update coalescing* / *collapsing updates*:
  - много апдейтов одного ключа схлопываются в один (последний).
- в связке с периодическим flush это похоже на *debounce + batching*.

3) **Инженерный/архитектурный паттерн**
- **write-behind** (write-back) persistence: “обновили in-memory сейчас, сохранили на диск позже”.

---

## 2) Зачем это нужно

### 2.1 Снижение нагрузки на I/O
Если одна и та же сущность обновляется часто (например, state аккаунта на каждый запрос), то запись “каждый раз” создаёт много мелких операций записи.

Coalesce map делает так, что за период `flush_interval` на диск уйдёт **одна** запись per key.

### 2.2 Снижение latency на request-path
Если запись на диск вынести из основного потока запроса, уменьшается tail latency.

---

## 3) Как работает (общая схема)

Пусть ключ — это `path` файла.

### 3.1 enqueue

- `enqueue_write(path, payload)`
  - `pending[path] = payload` (перезапись)

### 3.2 flush

Периодически writer делает flush.

Рекомендованный вариант для конкурентного доступа: **swap** + запись вне lock.

```text
lock
  to_flush = pending
  pending = {}
unlock

write all to_flush to disk
```

Это гарантирует:

- во время записи на диск новые апдейты не блокируются и попадают в новый `pending`.
- после записи `to_flush` можно просто выбросить.

---

## 4) Ограничения и trade-offs

### 4.1 Потеря промежуточных состояний
Это **не журнал событий**. Промежуточные значения между flush-ами не сохраняются.

### 4.2 Потеря хвоста при краше
Если процесс упадёт между flush-ами, может потеряться хвост данных, которые ещё не успели быть записаны.

Для PoC это обычно приемлемо, если система умеет самовосстанавливаться через повторные попытки и re-detect ошибок.

---

## 5) Где этот подход применяют

- write-behind кэширование (persist state по ключу)
- UI state: “последнее значение” отправить раз в N мс
- telemetry gauges: периодический snapshot
- файловые индексаторы и file watchers (coalesce по пути)
- reconciliation loops (desired state snapshot)

---

## 6) Когда НЕ использовать

- нужен audit trail / точная последовательность событий
- нельзя терять промежуточные изменения
- нужна транзакционная консистентность между множеством ключей

В таких системах обычно нужен event log, очередь, WAL/journal.

---

## 7) Как читать этот материал в документации проекта

Этот файл специально оставлен коротким и отвечает на вопрос **что это за паттерн и зачем он нужен в проекте**.

Если нужен следующий уровень детализации:

1. Сначала смотри нормативный runtime дизайн в [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:222)
2. Затем переходи к подробным вопросам и примерам в [`docs/theory/coalesce-map-faq.md`](docs/theory/coalesce-map-faq.md:1)

Такое разделение даёт progressive disclosure:

- архитектурный документ фиксирует **что принято и как система обязана работать**
- этот theory-файл объясняет **почему выбран именно такой паттерн**
- FAQ раскрывает **как именно ведёт себя механизм на примерах и в edge-cases**
