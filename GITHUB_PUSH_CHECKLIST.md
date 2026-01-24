# GitHub Push Preparation Checklist

Используйте этот checklist перед пушем проекта в GitHub.

## ✅ Основные файлы

- [x] `.gitignore` - исключает venv, .env, __pycache__, etc.
- [x] `README.md` - полное описание проекта и инструкции
- [x] `LICENSE` - MIT лицензия
- [x] `.gitattributes` - нормализация линий и кодировки
- [x] `pyproject.toml` - метаданные и зависимости

## ✅ Документация

- [x] `CONTRIBUTING.md` - рекомендации для разработчиков
- [x] `DEVELOPMENT.md` - гайд по локальной разработке
- [x] `CHANGELOG.md` - история изменений
- [x] `docs/ARCHITECTURE.md` - архитектурный анализ

## ✅ GitHub Actions

- [x] `.github/workflows/tests.yml` - CI/CD pipeline
  - Lint с Ruff
  - Type check с Pyright
  - Tests с pytest
  - Coverage report в Codecov

## ✅ GitHub Templates

- [x] `.github/ISSUE_TEMPLATE/bug_report.md` - шаблон для bug report'ов
- [x] `.github/ISSUE_TEMPLATE/feature_request.md` - шаблон для feature request'ов
- [x] `.github/pull_request_template.md` - шаблон для PR'ов

## ✅ Scripts

- [x] `scripts/prepush.sh` - pre-push чеклист

## 🔐 Безопасность

- [x] ✅ `.env` НЕ коммичен (добавлен в `.gitignore`)
- [x] ✅ Нет hardcoded токенов в коде
- [x] ✅ Только `env.example` в репо
- [x] ✅ Все чувствительные данные из environment variables
- [x] ✅ `.gitignore` исключает `.env*` файлы

## 📝 Код

- [x] Запущен `ruff format app/` - код отформатирован
- [x] Запущен `ruff check app/` - нет lint ошибок
- [x] Запущен `pyright app/` - type checking пройден
- [x] Все комментарии на английском (или отсутствуют)
- [x] Нет TODO/FIXME comments (или они обоснованы)
- [x] Нет debug print'ов или breakpoint()'ов

## 🗄️ База данных

- [x] Миграции находятся в `alembic/versions/`
- [x] `alembic.ini` настроен правильно
- [x] `env.example` содержит правильный `DATABASE_URL`
- [x] Миграции тестированы

## 🐳 Docker

- [x] `Dockerfile` валиден
- [x] `docker-compose.yml` работает
- [x] `.dockerignore` исключает ненужные файлы
- [x] Сервисы запускаются корректно
- [x] Health checks настроены

## 📦 Dependencies

- [x] `pyproject.toml` актуален
- [x] Все зависимости указаны
- [x] Dev зависимости в `optional-dependencies`
- [x] Python 3.12+ requirement

## 🧪 Tests (если добавлены)

- [x] Тесты написаны и проходят
- [x] Coverage > 70% (если требуется)
- [x] Tests CI/CD pipeline настроен

## 📋 Коммиты

- [x] Коммиты используют conventional commits:
  - `feat:` - новая функция
  - `fix:` - исправление
  - `docs:` - документация
  - `refactor:` - рефакторинг
  - `test:` - тесты
  - `chore:` - технические

- [x] Каждый коммит в develop/feature branches
- [x] Нет merge commits в истории

## 🔗 GitHub Setup

Перед первым пушем:

```bash
# 1. Создать репо на GitHub (не инициализировать файлы)
# https://github.com/new

# 2. Добавить remote
git remote add origin https://github.com/yourusername/bot_klima.git

# 3. Создать main ветку (если нету)
git branch -M main

# 4. Первый push
git push -u origin main
git push -u origin develop

# 5. На GitHub:
#    Settings → Branches → main is default branch
#    Settings → Branches → Branch protection rules → main (требовать review'ов)
```

## ✨ Перед финальным пушем

```bash
# 1. Запустить all checks
bash scripts/prepush.sh

# 2. Проверить статус
git status

# 3. Ничего не должно быть в staging (или все должно быть готово)

# 4. Push
git push origin develop

# 5. Открыть PR на GitHub
#    Title: [FEATURE] Describe what you're doing
#    Description: Fill the PR template
#    Assign reviewers

# 6. После approval и merge в main:
#    Create release tag: git tag v0.1.0
#    git push origin v0.1.0
#    На GitHub: Create Release from tag
```

## 📌 Дополнительно

### Рекомендуемые GitHub Settings

1. **Настройки репо**
   - [ ] Description: "Telegram bot for event synchronization"
   - [ ] Website: добавить если есть
   - [ ] Topics: telegram, bot, aiogram, python

2. **Branch protection (main)**
   - [ ] Require pull request reviews before merging
   - [ ] Require status checks to pass
   - [ ] Include administrators

3. **Secrets (для CI/CD)**
   - [ ] CODECOV_TOKEN (если используется codecov)

### Рекомендуемые GitHub Actions Secrets

```
CODECOV_TOKEN=your_codecov_token
```

### First Release

```bash
# After first merge to main
git tag v0.1.0
git push origin v0.1.0

# На GitHub:
# Releases → Draft new release
# Tag: v0.1.0
# Title: "Initial Release"
# Description: Скопировать из CHANGELOG.md
```

---

## Финальная проверка

```bash
# Убедитесь что всё готово:
✅ git status (clean)
✅ python -m app.bot (работает)
✅ docker-compose up (работает)
✅ pytest tests/ (все тесты pass)
✅ ruff check app/ (no errors)
✅ pyright app/ (no errors)

# Then:
git push origin develop
# Open PR on GitHub
```

---

**🚀 Готово к пушу в GitHub!**
