# DEPLOY на GitHub + Railway

1. Создайте бота через BotFather и получите токен.
2. Добавьте бота администратором в основной и тестовый каналы с правом публикации.
3. Создайте GitHub-репозиторий.
4. Загрузите все файлы проекта в корень репозитория.
5. В Railway создайте New Project → Deploy from GitHub.
6. Укажите Start Command: `python -m src.telegram_app`.
7. Добавьте переменные из `.env.example`.
8. Откройте Deploy Logs и дождитесь запуска.
9. В Telegram отправьте боту:
   - `/version`
   - `/status`
   - `/test 1`
   - `/run_once`

Если бот не отвечает: проверьте `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ADMIN_ID`, логи Railway и права бота в канале.
