# TON Observatory — универсальная библиотека иконок

Отдельный набор **брендовых логотипов** (`brands/`) и **иконок интерфейса** (`ui/`). 
Готов для автономного `index.html` и последующего копирования в другие обсерватории. Никаких CDN и внешних шрифтов.

**Важно:** фирменные векторы взяты из известных репозиториев Simple Icons и GitHub Primer, а не выданы за официальный экспорт фирменных брендбуков. Логотипы сервисов нельзя заменять вымышленными.

## Что доступно
- Бренды: Telegram, X, GitHub, Tether/USDT, TON (блокчейн).
- UI: поиск, настройки, фильтр, снежинка, замок, обмен, график, награда, внешняя ссылка.
- Из Ludoman уже есть изображения для Ludoman, ARNI, VNUK, Joystick, Phoenix, staking и NFT-метки (оригиналы независимо не проверялись).

## Telegram iOS UI Kit
Источник: https://www.figma.com/design/fIjhy6ddPFSXmia3DCvQa2/Telegram-IOS-UI-Kit--Community-

Проверены страницы **App Icons (11 стилей), Buttons, Tab Bars, System**. 
Компонент иконки Telegram по умолчанию: `6140:5660`. 
На текущем этапе Figma Starter ограничила дополнительные запросы; точные SVG/PNG не импортированы. 
Текущий Telegram SVG взят из Simple Icons; UI-иконки — из Lucide. Поэтому **они не называются экспортированными из набора Figma**.

## Откуда взять ожидающие логотипы
- https://telegram.org/tour/screenshots — официальная страница Telegram
- https://ton.org/media/ — официальные GRAM/TON медиаархивы (не путать токен GRAM и сеть TON)
- https://ston.fi/press-room — официальный брендбук STON.fi
- https://app.dedust.io/ — официальный интерфейс DeDust
- https://tonco.io/ — официальный сайт TONCO

Полный реестр с источниками и перечнем ожидающих оригиналов: `manifest.json`.

## Использование
`python3 scripts/icon_pack.py --gallery` создаёт автономную страницу `build/icon-gallery.html`.
`python3 build.py` встраивает подтверждённые SVG через data URI в автономный `index.html`.
Каждое изображение проверяется: запрещены внешние URI, скрипты, обработчики событий.
Чтобы добавить иконку, положить файл в `brands/` или `ui/`, затем указать его в `manifest.json` вместе с источником.

## Лицензии
- Simple Icons: CC0, https://github.com/simple-icons/simple-icons/blob/develop/LICENSE.md
- GitHub Octicons: MIT, https://github.com/primer/octicons/blob/main/LICENSE
- Lucide: ISC, https://github.com/lucide-icons/lucide/blob/main/LICENSE

Товарные знаки принадлежат соответствующим владельцам; лицензия SVG-библиотеки сама по себе не предоставляет права выдавать сайт за официальный сервис. 
