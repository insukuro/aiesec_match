#!/usr/bin/env python3
"""Polish generated draw.io DFD files: readable layout, Russian labels, consistent styles."""

import html
import math
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DFD = ROOT / "docs" / "dfd"

STYLE_EXTERNAL = "shape=rectangle;rounded=1;whiteSpace=wrap;html=1;fillColor=#DAE8FC;strokeColor=#6C8EBF;fontSize=13;fontStyle=1;fontColor=#1F2937;"
STYLE_PROCESS = "ellipse;whiteSpace=wrap;html=1;fillColor=#FFF2CC;strokeColor=#D6B656;fontSize=12;fontStyle=1;fontColor=#1F2937;"
STYLE_STORE = "shape=partialRectangle;rounded=0;whiteSpace=wrap;html=1;top=0;bottom=0;left=1;right=0;fillColor=#F3F4F6;strokeColor=#6B7280;fontSize=12;fontStyle=1;fontColor=#1F2937;"
STYLE_BOUNDARY = "rounded=0;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#9CA3AF;strokeWidth=2;dashed=1;verticalAlign=top;spacingTop=10;fontSize=11;fontColor=#6B7280;"
STYLE_EDGE = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;strokeColor=#64748B;strokeWidth=1.5;fontSize=10;fontColor=#334155;labelBackgroundColor=#FFFFFF;"

LABELS = {
    "AIESEC Match\nSystem": "AIESEC Match\nСистема",
    "User": "Пользователь",
    "Telegram Bot / WebApp": "Telegram Bot / WebApp",
    "Telegram Consumer": "Потребитель Telegram",
    "AIESEC External API": "Внешний API AIESEC",
    "AIESEC GraphQL API": "AIESEC GraphQL API",
    "Parser Administrator": "Администратор парсера",
    "Matching / Run Creation": "Сервис подбора / создание запуска",
    "User / In-App UI": "Пользователь / интерфейс",
    "User / Telegram WebApp": "Пользователь / Telegram WebApp",
    "1.0 Frontend /\nUser Interaction": "1.0 Frontend /\nВзаимодействие с пользователем",
    "2.0 Authentication &\nAccount Management": "2.0 Аутентификация и\nуправление аккаунтом",
    "3.0 Profile & Consent\nManagement": "3.0 Профиль и\nуправление согласиями",
    "4.0 Opportunity Catalog\nManagement": "4.0 Управление каталогом\nвозможностей",
    "5.0 Matching &\nRecommendations": "5.0 Подбор и\nрекомендации",
    "6.0 Feedback &\nHistory": "6.0 Feedback и\nистория",
    "7.0 Notifications &\nSubscriptions": "7.0 Уведомления и\nподписки",
    "8.0 Data\nSynchronization": "8.0 Синхронизация\nданных",
    "9.0 Analytics": "9.0 Аналитика",
    "2.1 Register Account": "2.1 Регистрация аккаунта",
    "2.2 Password Login": "2.2 Вход по паролю",
    "2.3 Verify Telegram\ninitData": "2.3 Проверка Telegram\ninitData",
    "2.4 Issue / Validate\nJWT": "2.4 Выдача и проверка\nJWT",
    "2.5 Account Changes": "2.5 Изменение аккаунта",
    "2.6 Telegram Identity\nLinking": "2.6 Привязка identity\nTelegram",
    "3.1 Load Form &\nConsent Schema": "3.1 Загрузка схемы формы\nи согласий",
    "3.2 Validate Profile\n& Age": "3.2 Валидация анкеты\nи возраста",
    "3.3 Normalize Profile\nFields": "3.3 Нормализация\nполей анкеты",
    "3.4 Calculate\nCompleteness": "3.4 Расчёт\nполноты профиля",
    "3.5 Manage Consents": "3.5 Управление\nсогласиями",
    "3.6 Persist Profile\nVersions": "3.6 Сохранение версий\nпрофиля",
    "4.1 OAuth / Token\nRefresh": "4.1 OAuth и обновление\nтокена",
    "4.2 Build GraphQL\nQueries": "4.2 Формирование GraphQL\nзапросов",
    "4.3 Full Strategy": "4.3 Полная синхронизация",
    "4.4 Incremental Strategy": "4.4 Инкрементальная\nсинхронизация",
    "4.5 Reconcile Strategy": "4.5 Сверочная\nсинхронизация",
    "4.6 Gap Filling": "4.6 Заполнение пропусков",
    "4.7 Normalize /\nActuality / Target": "4.7 Нормализация, актуальность\nи целевые фильтры",
    "4.8 Upsert / Close\nMissing": "4.8 Upsert и закрытие\nне найденных записей",
    "5.1 Validate Consent &\nCreate Run": "5.1 Проверка согласия\nи создание запуска",
    "5.2 Prepare Profile\nSnapshot": "5.2 Подготовка снимка\nпрофиля",
    "5.3 Build Matcher\nPayload": "5.3 Формирование запроса\nк matcher",
    "5.4 Matcher: Route /\nFilter / Score": "5.4 Matcher: маршрутизация,\nфильтры и scoring",
    "5.5 Attach Catalog\nCards": "5.5 Добавление карточек\nкаталога",
    "5.6 Persist Run &\nItems": "5.6 Сохранение запуска\nи результатов",
    "6.1 Receive / Remove\nFeedback": "6.1 Получение и удаление\nfeedback",
    "6.2 Build Activity\nHistory": "6.2 Формирование истории\nактивности",
    "6.3 Aggregate\nAnalytics": "6.3 Агрегация\nаналитики",
    "6.4 Resolve\nOpportunity Cards": "6.4 Получение карточек\nвозможностей",
    "7.1 Check Subscription": "7.1 Проверка подписки",
    "7.2 Create Outbox\nEvent": "7.2 Создание события\nOutbox",
    "7.3 Dedupe by\nUser + Run": "7.3 Дедупликация по\nпользователю и запуску",
    "7.4 Lease Notifications": "7.4 Аренда уведомлений",
    "7.5 Update Sent /\nFailed State": "7.5 Обновление Sent /\nFailed",
    "7.6 In-App Read\nState": "7.6 Состояние прочтения\nв интерфейсе",
    "2.0 Auth &\nAccounts": "2.0 Аутентификация и\nаккаунты",
    "3.0 Profiles &\nConsents": "3.0 Профили и\nсогласия",
    "5.0 Matching": "5.0 Подбор",
    "6.0 Feedback / History": "6.0 Feedback и история",
    "core.users / identities /\npassword_credentials": "core.users / identities /\npassword_credentials",
    "core.password_reset_tokens /\nemail_verifications": "core.password_reset_tokens /\nemail_verifications",
    "core.profiles /\nprofile_versions": "core.profiles /\nprofile_versions",
    "core.consents": "core.consents",
    "catalog.opportunity_v1 /\nopportunity_requirement_v1": "catalog.opportunity_v1 /\nopportunity_requirement_v1",
    "core.recommendation_runs /\nrecommendation_items": "core.recommendation_runs /\nrecommendation_items",
    "core.feedback": "core.feedback",
    "core.subscriptions /\nnotification_outbox / link_codes": "core.subscriptions /\nnotification_outbox / link_codes",
    "parser.opportunities / sync_runs /\nsync_state": "parser.opportunities / sync_runs /\nsync_state",
    "7.0 Notifications": "7.0 Уведомления",
    "4.0 Parser Sync": "4.0 Синхронизация парсера",
}

EDGE_LABELS = {
    "email / password": "email / пароль",
    "Telegram initData": "Telegram initData",
    "access JWT / expiry": "JWT-доступ / срок действия",
    "new user identity": "Новая identity пользователя",
    "password hash / user status": "Хеш пароля / статус пользователя",
    "credential lookup": "Поиск учетных данных",
    "verification state": "Состояние верификации",
    "email verification code hash": "Хеш кода подтверждения email",
    "password / email / account deletion": "Пароль / email / удаление аккаунта",
    "credential / identity / soft-delete update": "Обновление credentials / identity / soft-delete",
    "link code": "Код привязки",
    "link code / Telegram chat metadata": "Код привязки / данные Telegram-чата",
    "code owner / expiry": "Владелец кода / срок действия",
    "Telegram identity / chat update": "Identity и чат Telegram",
    "form / consent request": "Запрос формы / согласия",
    "form schema / consent schema / options": "Схема формы / согласия / справочники",
    "profile body / If-Match version": "Тело профиля / версия If-Match",
    "validated profile fields": "Проверенные поля профиля",
    "JSON profile snapshot": "JSON-снимок профиля",
    "new version / birth date / completeness": "Новая версия / дата рождения / полнота",
    "consent kind / version": "Тип согласия / версия",
    "consent acceptance / revocation": "Принятие / отзыв согласия",
    "accepted consent records": "Записи принятых согласий",
    "raw opportunity records": "Необработанные записи возможностей",
    "OAuth credentials / access token": "OAuth credentials / access-токен",
    "OAuth / GraphQL authorization response": "Ответ OAuth / GraphQL авторизации",
    "paginated GraphQL opportunity query": "Постраничный GraphQL-запрос возможностей",
    "full opportunity ids": "Полные идентификаторы возможностей",
    "gap-fill opportunity records": "Записи для заполнения пропусков",
    "gap-filled records": "Заполненные записи возможностей",
    "normalized / actuality-checked rows": "Нормализованные и проверенные строки",
    "upsert / close / reopen operations": "Операции upsert / close / reopen",
    "known ids / open opportunity state": "Известные ID / состояние открытых записей",
    "sync status / stats / error": "Статус / статистика / ошибка синхронизации",
    "last_full_at / last_incremental_at": "Время полной и инкрементальной синхронизации",
    "incremental watermark": "Водяной знак инкрементальной синхронизации",
    "previous incremental watermark": "Предыдущий водяной знак",
    "last_reconcile_at": "Время последней сверки",
    "consent / profile lookup": "Поиск согласия и профиля",
    "profile snapshot / filters / limit / explain": "Снимок профиля / фильтры / лимит / объяснение",
    "open catalog / opportunity requirements": "Открытый каталог / требования возможностей",
    "groups / scores / labels / reasons": "Группы / оценки / метки / причины",
    "filtered recommendation groups": "Отфильтрованные группы рекомендаций",
    "run state / items / watermark": "Состояние запуска / позиции / водяной знак",
    "recommendation run / ranked cards": "Запуск рекомендаций / ранжированные карточки",
    "opened / liked / disliked / hidden / applied": "Открыто / нравится / не нравится / скрыто / отклик",
    "feedback records / run_id / opportunity_id": "Записи feedback / run id / opportunity id",
    "feedback lists": "Списки feedback",
    "liked / hidden opportunity lists": "Списки понравившихся / скрытых возможностей",
    "history type / date range / pagination": "Тип истории / диапазон дат / пагинация",
    "completed recommendation events": "События завершённых рекомендаций",
    "feedback events": "События feedback",
    "chronological history page": "Хронологическая история",
    "profile completeness / interests": "Полнота профиля / интересы",
    "recommendation distributions / counts": "Распределение и количество рекомендаций",
    "activity events / feedback signals": "События активности / feedback-сигналы",
    "profile / programme / activity metrics": "Профиль / программы / метрики активности",
    "UI input / profile / feedback": "Ввод интерфейса / профиль / feedback",
    "responses / cards / history / metrics": "Ответы / карточки / история / метрики",
    "profile data / completeness": "Данные профиля / полнота",
    "profile body / consent actions": "Тело профиля / действия с согласиями",
    "profile / schema / completeness": "Профиль / схема / полнота",
    "profile / version / updated_at": "Профиль / версия / updated_at",
    "recommendation filters / idempotency key": "Фильтры рекомендаций / ключ идемпотентности",
    "ranked groups / run state": "Ранжированные группы / состояние запуска",
    "feedback / history filters": "Feedback / фильтры истории",
    "feedback lists / history events": "Списки feedback / события истории",
    "analytics period": "Период аналитики",
    "aggregated metrics": "Агрегированные метрики",
    "runs / feedback / profile data": "Запуски / feedback / данные профиля",
}


def unescape_label(value: str) -> str:
    return html.unescape(value)


def translated(value: str) -> str:
    value = unescape_label(value)
    if value in LABELS:
        return LABELS[value]
    if value in EDGE_LABELS:
        return EDGE_LABELS[value]
    return value


def geometry(child):
    geo = child.find("mxGeometry")
    if geo is not None:
        child.remove(geo)
    return geo


def set_geometry(root, cells):
    page_width = 1500
    page_height = 1120

    boundaries = [c for c in cells if c.get("vertex") == "1" and "dashed=1" in c.get("style", "")]
    for i, c in enumerate(boundaries):
        c.set("style", STYLE_BOUNDARY)
        geo = ET.SubElement(c, "mxGeometry", {"x": "55", "y": "55", "width": "1390", "height": "890", "as": "geometry"})

    externals = [c for c in cells if c.get("vertex") == "1" and "shape=rectangle" in c.get("style", "") and "dashed=1" not in c.get("style", "")]
    stores = [c for c in cells if c.get("vertex") == "1" and "partialRectangle" in c.get("style", "")]
    processes = [c for c in cells if c.get("vertex") == "1" and "ellipse" in c.get("style", "")]

    # External entities: two balanced columns at the canvas edges.
    left = []
    right = []
    for c in externals:
        cid = c.get("id", "")
        old = c.find("mxGeometry")
        old_x = float(old.get("x", "0")) if old is not None else 0
        if old_x < page_width * 0.45:
            left.append(c)
        else:
            right.append(c)

    def place_vertical(items, x):
        if not items:
            return
        spacing = 860 / max(1, len(items))
        for i, c in enumerate(sorted(items, key=lambda q: q.get("value", ""))):
            y = 70 + i * spacing
            c.set("style", STYLE_EXTERNAL)
            for geo in c.findall("mxGeometry"):
                c.remove(geo)
            ET.SubElement(c, "mxGeometry", {"x": str(x), "y": str(round(y)), "width": "170", "height": "78", "as": "geometry"})

    place_vertical(left, 35)
    place_vertical(right, 1295)

    # Processes: compact central grid, preserving the original reading order by x/y.
    if processes:
        original = []
        for c in processes:
            geo = c.find("mxGeometry")
            old_x = float(geo.get("x", "0")) if geo is not None else 0
            old_y = float(geo.get("y", "0")) if geo is not None else 0
            original.append((old_y, old_x, c))

        ordered = [x[2] for x in sorted(original, key=lambda item: (round(item[0] / 140), item[1]))]
        n = len(ordered)
        if n <= 1:
            cols, rows = 1, 1
        elif n <= 4:
            cols, rows = 2, math.ceil(n / 2)
        elif n <= 9:
            cols, rows = 3, math.ceil(n / 3)
        else:
            cols, rows = 4, math.ceil(n / 4)

        cell_w, cell_h = 215, 88
        grid_w = cols * cell_w + (cols - 1) * 35
        start_x = 245 + max(0, (760 - grid_w) / 2)
        start_y = 120
        row_gap = 125

        for i, c in enumerate(ordered):
            row, col = divmod(i, cols)
            x = start_x + col * (cell_w + 35)
            y = start_y + row * row_gap
            if n > 6:
                y = min(y, 650)
            c.set("style", STYLE_PROCESS)
            for geo in c.findall("mxGeometry"):
                c.remove(geo)
            ET.SubElement(c, "mxGeometry", {"x": str(round(x)), "y": str(round(y)), "width": str(cell_w), "height": str(cell_h), "as": "geometry"})

    # Stores: compact full-width bank along the bottom.
    if stores:
        n = len(stores)
        cols = 3 if n >= 4 else 2
        store_w = 270
        store_h = 86
        gap_x = 30
        gap_y = 25
        grid_w = cols * store_w + (cols - 1) * gap_x
        start_x = (page_width - grid_w) / 2
        start_y = 820
        for i, c in enumerate(stores):
            row, col = divmod(i, cols)
            c.set("style", STYLE_STORE)
            for geo in c.findall("mxGeometry"):
                c.remove(geo)
            ET.SubElement(c, "mxGeometry", {
                "x": str(round(start_x + col * (store_w + gap_x))),
                "y": str(round(start_y + row * (store_h + gap_y))),
                "width": str(store_w),
                "height": str(store_h),
                "as": "geometry",
            })


def polish_file(path: Path):
    tree = ET.parse(path)
    root = tree.getroot()

    model = root.find(".//mxGraphModel")
    if model is not None:
        model.set("pageWidth", "1500")
        model.set("pageHeight", "1120")

    cells = list(root.findall(".//mxCell"))

    for c in cells:
        value = c.get("value")
        if value:
            c.set("value", translated(html.unescape(value)))

        if c.get("edge") == "1":
            c.set("style", STYLE_EDGE)

    set_geometry(root, cells)

    ET.indent(tree, space="  ")
    tree.write(path, encoding="utf-8", xml_declaration=True)


def main():
    files = sorted(DFD.glob("*.drawio"))
    if len(files) != 9:
        raise SystemExit(f"Expected 9 drawio files, found {len(files)}")
    for path in files:
        polish_file(path)
        print(path.name)


if __name__ == "__main__":
    main()
