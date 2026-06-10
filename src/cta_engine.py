from __future__ import annotations

from urllib.parse import quote_plus

from .config_loader import CONFIG_DIR, load_json
from .models import Brief, Button, PostVariant
from .url_builder import UrlBuilder


class CTAEngine:
    def __init__(self, channel_url: str = ""):
        self.services = load_json(CONFIG_DIR / "services.json", default=[])
        self.rules = load_json(CONFIG_DIR / "link_rules.json", default={})
        self.channel_url = channel_url
        self.url_builder = UrlBuilder()

    def apply(self, variant: PostVariant, brief: Brief) -> PostVariant:
        buttons = self._service_buttons(brief)
        if not buttons:
            buttons = self._universal_buttons(brief)
        variant.buttons = buttons
        if not variant.cta_text:
            variant.cta_text = self._cta_text(brief)
        return variant

    def _service_buttons(self, brief: Brief) -> list[Button]:
        rule = self.rules.get(brief.genre, self.rules.get("default", {}))
        cats = rule.get("categories", [])
        max_buttons = int(rule.get("max_buttons", 2) or 2)
        if not cats:
            return []
        out=[]
        for cat in cats:
            for svc in sorted(self.services, key=lambda x: int(x.get("priority", 0)), reverse=True):
                if svc.get("status") != "active" or svc.get("category") != cat:
                    continue
                genres = svc.get("genres") or []
                if "*" not in genres and brief.genre not in genres and cat not in brief.allowed_services:
                    continue
                url = svc.get("url", "")
                if not url:
                    continue
                if cat == "flights":
                    url = self.url_builder.build_flight_url(url, brief)
                else:
                    url = self.url_builder.build_generic_url(url, brief)
                text = (svc.get("button_texts") or [svc.get("name")])[0]
                out.append(Button(text=text, url=url, service_key=svc.get("key", "")))
                break
            if len(out) >= max_buttons:
                break
        return out

    def _universal_buttons(self, brief: Brief) -> list[Button]:
        buttons=[]
        channel = self.channel_url
        if channel:
            buttons.append(Button(text="🔔 Подписаться на канал", url=channel, service_key="channel_subscribe"))
            share = "https://t.me/share/url?url=" + quote_plus(channel) + "&text=" + quote_plus("Смотри, полезная travel-идея из канала «Мир на ладони»")
            buttons.append(Button(text="↗️ Отправить другу", url=share, service_key="share_friend"))
        tourjin = next((s for s in self.services if s.get("key") == "tourjin_bot"), None)
        if tourjin:
            buttons.append(Button(text="🧭 Подобрать в TourJin", url=tourjin.get("url", ""), service_key="tourjin_bot"))
        return buttons[:3]

    def _cta_text(self, brief: Brief) -> str:
        if brief.genre in {"flight_deal", "tour_offer", "hotel_post"}:
            return "Проверьте актуальные условия и сравните варианты под свои даты."
        if brief.genre in {"top_list", "route", "practical_travel"}:
            return "Сохраните пост, чтобы вернуться к нему перед поездкой."
        return "Отправьте тому, кто тоже любит собирать идеи для путешествий."
