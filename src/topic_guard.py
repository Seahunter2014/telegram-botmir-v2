import re
from .models import Signal

TRAVEL_ALLOW = [
    "поезд", "билет", "рейс", "отель", "тур", "море", "пляж", "город", "маршрут", "виза", "внж",
    "страхов", "багаж", "аэропорт", "перелет", "перелёт", "экскурс", "музей", "концерт", "фестиваль",
    "путеше", "курорт", "отдых", "граница", "карта", "оплата за границей", "релокац", "документ"
]

HARD_REJECT = [
    "airdrop", "крипт", "web3", "nft", "ваканси", "резюме", "найм", "зарплат", "xai", "openai", "facebook", "cisco",
    "программист", "разработчик", "айтишник", "it-карьер", "карьер", "стартап", "инвестиц", "трейдинг"
]

SOFT_REJECT = ["вебинар", "эфир", "прямая трансляция", "зарегистрируйтесь", "регистрация на", "онлайн-встреч"]

class TopicGuard:
    def check(self, signal: Signal) -> tuple[bool, str]:
        text = f"{signal.title}\n{signal.text}".lower()
        if any(bad in text for bad in HARD_REJECT):
            return False, "Тема похожа на IT/крипту/вакансии/постороннюю повестку, не travel-редакцию."
        if any(bad in text for bad in SOFT_REJECT) and not any(ok in text for ok in TRAVEL_ALLOW):
            return False, "Тема похожа на чужой эфир/вебинар без travel-ценности."
        if len(text.strip()) < 40:
            return False, "Слишком мало содержательной фактуры."
        if not any(ok in text for ok in TRAVEL_ALLOW):
            # Не убиваем красивую географическую тему: источник может быть travel-журналом.
            role = signal.raw.get("source", {}).get("role", "")
            if "beauty" not in role and "travel" not in role and "inspiration" not in role:
                return False, "Не видно travel-ценности для канала."
        return True, ""
