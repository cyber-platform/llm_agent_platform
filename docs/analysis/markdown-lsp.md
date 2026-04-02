# Markdown LSP: что он даёт и где его границы

## Кратко

Markdown LSP полезен для навигации, валидации ссылок и базового структурного анализа Markdown-документов. Он хорошо работает с outgoing links, но обычно не является полноценным механизмом для reverse links и общего knowledge graph по документации проекта.

## Что Markdown LSP обычно умеет хорошо

Типичный Markdown language server умеет:

- разбирать структуру Markdown:
  - headings
  - lists
  - code blocks
  - links
  - images
- находить и валидировать ссылки:
  - relative file links
  - anchors внутри документа
  - иногда URL
- поддерживать IDE-like возможности:
  - hover
  - document symbols
  - workspace symbols
  - go to definition для ссылок
  - rename/update links в некоторых реализациях
- улучшать навигацию по документации:
  - переход к целевому `.md` файлу
  - переход к heading внутри файла
  - диагностика broken links

## Ключевые сильные стороны

### 1. Outgoing links из текущего файла

Примеры:

- `[ADR-001](../adr/001-decision.md)`
- `[API Contract](../contracts/public-api.openapi.yaml)`
- `[Section](./guide.md#installation)`

Markdown LSP обычно может:

- распознать ссылку
- resolve target file
- resolve target anchor
- дать редактору перейти к target

### 2. Базовая диагностика документации

Например:

- broken file links
- broken heading anchors
- некорректные relative paths
- иногда структурные проблемы вокруг Markdown references

### 3. Навигация по структуре документа

Через `documentSymbol` клиент может получить:

- headings документа
- sections
- иногда вложенный outline

Это полезно для TOC, outline view и агентной навигации.

## Чего Markdown LSP обычно не даёт

### 1. Полноценные incoming links

Вопрос:

> Какие документы ссылаются на этот `.md` файл?

Это обычно не сильная нативная возможность LSP. LSP лучше отвечает на вопросы из текущего файла наружу, чем поддерживает полный reverse index по всему workspace.

### 2. Documentation knowledge graph

Markdown LSP не является graph engine. Обычно он не хранит явно:

- backlinks
- traceability
- transitive relationships между docs, code, ADR, contracts и tests
- shortest paths между артефактами

### 3. Architecture queries по всему workspace

Примеры:

- какие ADR ссылаются на этот contract?
- какие docs зависят от этого guide?
- какие test map упоминают этот module?

Такие задачи лучше решать через отдельный indexer или graph model.

## Практическая оценка

### Когда Markdown LSP полезен

Его стоит использовать, когда нужны:

- локальная навигация по документу
- link validation
- anchor validation
- section outline
- editor-aware diagnostics

### Когда его недостаточно

Нужно больше, чем LSP, когда нужны:

- backlinks
- impact analysis по документации
- documentation knowledge graph
- сквозные связи вида `docs -> contracts -> code -> tests`

## Простое разграничение

### Markdown LSP хорошо отвечает на

- куда ведёт эта ссылка?
- существует ли этот target?
- какие headings есть в документе?
- есть ли здесь broken Markdown links?

### Markdown LSP обычно слаб в вопросах

- кто ссылается на этот документ?
- какие документы транзитивно зависят от этого ADR?
- какие Markdown-файлы связаны с этим API contract через несколько hops?

## Вывод

Markdown LSP — это сильный локальный слой для навигации и валидации Markdown. Он полезен как источник точных фактов о структуре документа и outgoing links.

Для incoming links, глобального анализа документации и project knowledge graph нужен дополнительный index или graph database.
