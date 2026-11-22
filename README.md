# Ludoman Observatory

Обозреватель LUDOMAN на русском и английском. [Открыть или скачать готовый HTML из репозитория](https://raw.githubusercontent.com/Freebielife/Ludoman/main/index.html). Для публикации в TON Sites загрузите этот файл как корневой `index.html` в Resistance Tools.

В HTML встроены стили, скрипты, эмблема и последний снимок. При открытии страница проверяет обновления в GitHub каждые пять минут и по кнопке «Обновить». GitHub Actions собирает снимок через обновление исходников или ручной запуск. Внешний планировщик Cloudflare может запускать обновления по настроенному интервалу; точный график следует проверять по журналу Actions.

## Данные

- Лента, статистика за 24 часа и рейтинг продавцов учитывают успешные прямые свопы LUDOMAN/GRAM в отслеживаемых пулах STON.fi и DeDust. Подтверждённые сжигания берутся из транзакций мастер-контракта.
- График рассчитывает оценку по формуле «цена сделки в основном пуле STON.fi × текущее общее предложение». Режим USD умножает эту оценку на доступный на соответствующий момент курс GRAM/USD по CoinGecko. Данные CoinGecko за год имеют дневную детализацию. Общее предложение включает заблокированные токены.
- Золотая метка четырёхзначного `.ton` подтверждается по владельцу NFT в корневой коллекции TON DNS.
- Метка `+888` подтверждается по владельцу NFT из коллекции Anonymous Telegram Numbers. Кошельки ленты и рейтингов проверяются очередью, поиск кошелька также проверяет NFT через TonAPI.
- Метка `DEV` назначена владельцем сайта кошельку `UQD5p2Uq4b4KjKxMkivHMqP8verJ0Gl_Uegim0WKyRduBHBa` только в Ludoman. Его операции, позиции в рейтингах и результат поиска выделяются красной анимированной рамкой и полупрозрачным фоном DEV. Метка доступна в фильтре операций; генератор исключает эту настройку из других проектов.
- Пулы GeckoTerminal, заморозка TonRaffles и стейкинг JVault проверяются раз в сутки. При сбое сохраняется последнее подтверждённое значение, а проверка повторяется при следующем запуске. Известные карточки пулов сохраняются, в том числе для контрактов вне индекса GeckoTerminal.
- Эмблема и рисунок для баннера основаны на [изображении из метаданных токена](https://github.com/Freebielife/Logo-Ludo/blob/5a675433afa00797d62aac90227fe151ae3d282e/Logo.jpg).

## Проверка перед публикацией обсерватории нового токена

- Сверьте мастер-контракт, адреса торговых пулов и обе стороны каждой пары.
- Проверьте наличие стейкинга и заморозки. Сверьте принадлежность контрактов токену и суммы по данным контрактов. Подключите подтверждённые источники, укажите их в карточках по образцу Ludoman и проверьте, что первый снимок показывает фактические суммы. Если источник отсутствует или не удалось его подтвердить, показывайте «—» до подтверждения.
- Проверьте дневное обновление каждой подключённой секции и сохранение последнего успешного снимка при ошибке источника.

## Сборка

```sh
python3 collect.py
python3 build.py
python3 verify.py
node --test tests/*.test.cjs
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Шаблон для новых токенов

Теперь предусмотрен **генератор независимых обсерваторий**: он автоматически создаёт новый проект с той же визуальной системой, но без логотипа, NFT-меток, социальных ссылок, кошельков сервисов, пулов и статистики Ludoman. Параметры нового токена находятся в одном JSON-файле; исходники Ludoman вручную менять не нужно.

Пример команды:

```sh
python3 scripts/scaffold_observatory.py --config /path/to/new-token.json --output /path/to/new-observatory
```

Схема конфигурации, проверки и ограничения: [docs/NEW_PROJECT_FACTORY.md](docs/NEW_PROJECT_FACTORY.md). До проверки контрактов новый проект не получает вымышленные показатели стейкинга или APR.

## Reusable foundation 1.1.0

New sites use the contract-driven generator described in [FOUNDATION_V1.md](docs/FOUNDATION_V1.md). It generates isolated sources, collects data and verifies one standalone HTML. Holders start at 10 and expand to top 20. Existing Ludoman and KITO outputs are not migrated by these factory changes.

Branding is required for new sites: the hero logo must come from token metadata or the project website, section flags must be explicitly selected independently, and the project's Telegram channel must be present. See [BRANDING_STANDARD.md](docs/BRANDING_STANDARD.md).
