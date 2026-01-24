# 🐛 Bug Fix: TelegramBadRequest "message is not modified"

**Дата:** 24 января 2026  
**Статус:** ✅ FIXED

---

## 📋 Описание проблемы

### Ошибка
```
TelegramBadRequest: Telegram server says - Bad Request: message is not modified: 
specified new message content and reply markup are exactly the same as a current 
content and reply markup of the message
```

### Причина
Когда пользователь нажимал на кнопку в меню, бот пытался обновить сообщение (используя `edit_text()`) с **точно таким же текстом и кнопками**, которые уже были в сообщении.

Telegram API не позволяет обновлять сообщение, если содержимое не изменилось.

### Где возникала
- `app/handlers/callbacks/menu.py` - функция `menu_action()` (основное место)
- `app/handlers/callbacks/rooms.py` - функция `delete_room_prompt()` (вторичное)

---

## ✅ Решение

### Подход
Обработать исключение `TelegramBadRequest` с проверкой на сообщение "message is not modified":

```python
try:
    await cb.message.edit_text(text, reply_markup=keyboard)
except TelegramBadRequest as e:
    if "message is not modified" not in str(e):
        raise  # Re-raise если это другая ошибка
    # Иначе - просто игнорируем (сообщение уже такое же)
```

### Измененные файлы

#### 1. `app/handlers/callbacks/menu.py`
- ✅ Добавлен импорт: `from aiogram.exceptions import TelegramBadRequest`
- ✅ Обновлены все `edit_text()` вызовы с обработкой исключения:
  - `action == "home"` - Главное меню
  - `action == "rooms"` - Список комнат
  - `action == "create_room"` - Создание комнаты
  - `action == "join_room"` - Присоединение к комнате

#### 2. `app/handlers/callbacks/rooms.py`
- ✅ Добавлен импорт: `from aiogram.exceptions import TelegramBadRequest`
- ✅ Обновлена функция `delete_room_prompt()` с обработкой исключения

---

## 🎯 Почему это лучший подход

### ❌ Что было бы плохо

1. **Сравнивать текст и кнопки перед обновлением**
   - Усложняет код
   - Нужно хранить предыдущее состояние
   - Сложно с динамическими кнопками

2. **Использовать разные методы (edit_text vs answer)**
   - Непредсказуемо
   - Сложнее поддерживать

3. **Всегда отправлять новое сообщение вместо edit**
   - Много сообщений в чате
   - Плохой UX

### ✅ Наш подход

- **Простой** - просто обрабатываем исключение
- **Надежный** - не зависит от состояния
- **Чистый** - минимум изменений кода
- **Стандартный** - это паттерн используется в Telegram ботах

---

## 🧪 Тестирование

Чтобы проверить что баг исправлен:

```bash
# 1. Запустить бот
docker-compose up -d

# 2. Открыть бот в Telegram

# 3. Нажать на одну и ту же кнопку несколько раз подряд
# (например, /start → кнопка "Главное меню" → нажать еще раз)

# 4. Не должно быть ошибок в логах:
docker-compose logs -f bot | grep -i "TelegramBadRequest"

# Результат: ничего не должно выпечататься
```

---

## 📚 Best Practices для будущего

### Правило 1: Всегда обрабатывайте TelegramBadRequest

```python
from aiogram.exceptions import TelegramBadRequest

try:
    await message.edit_text(text)
except TelegramBadRequest as e:
    if "message is not modified" in str(e):
        pass  # OK, сообщение уже такое же
    elif "message to edit not found" in str(e):
        # Сообщение было удалено, отправляем новое
        await message.answer(text)
    else:
        raise  # Другая ошибка, пробрасываем
```

### Правило 2: Используйте edit_text для меню

```python
# ✅ Правильно - обновляем существующее сообщение
await message.edit_text(
    text="Новый текст",
    reply_markup=new_keyboard
)

# ❌ Неправильно - отправляем новое сообщение каждый раз
await message.answer(text="Новый текст", reply_markup=new_keyboard)
```

### Правило 3: Обрабатывайте все исключения в callbacks

```python
@router.callback_query(...)
async def my_callback(cb: CallbackQuery, ...):
    try:
        # Ваш код
        await cb.message.edit_text(...)
    except TelegramBadRequest as e:
        # Обработать Telegram ошибки
        if "message is not modified" not in str(e):
            raise
    except Exception as e:
        # Обработать другие ошибки
        await cb.answer(f"❌ Ошибка: {e}", show_alert=True)
        raise
    finally:
        # Всегда отвечайте на callback
        await cb.answer()
```

---

## 🔍 Дополнительно

### Другие возможные Telegram ошибки

```python
# message.text too long (> 4096 chars)
if "too long" in str(e):
    # Сокращить текст или отправить файл

# message to edit not found
if "message to edit not found" in str(e):
    # Сообщение было удалено, отправить новое

# message is not modified  
if "message is not modified" in str(e):
    # Игнорировать - сообщение уже такое же

# user is member
if "user is member" in str(e):
    # Пользователь уже в чате/группе
```

---

## 📝 Commit

```
fix: handle TelegramBadRequest "message is not modified" error

- Add try-except blocks to edit_text() calls in menu_action()
- Add try-except blocks to edit_text() calls in delete_room_prompt()
- Import TelegramBadRequest from aiogram.exceptions
- Gracefully ignore "message is not modified" errors
- Re-raise other TelegramBadRequest errors for debugging

Fixes error in menu navigation when same state is selected
```

---

## 🎯 Резюме

**Проблема:** Telegram API ошибка при попытке обновить сообщение с тем же содержимым  
**Решение:** Обработать `TelegramBadRequest` с проверкой на "message is not modified"  
**Файлы:** 2 (`menu.py`, `rooms.py`)  
**Строки кода:** ~50  
**Время исправления:** 5 минут  
**Статус:** ✅ READY FOR TESTING
