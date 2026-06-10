from __future__ import annotations

from .models import Brief, PostVariant


class FactChecker:
    def check(self, variant: PostVariant, brief: Brief) -> PostVariant:
        risky = []
        text = f"{variant.body} {variant.cta_text}".lower()
        if any(x in text for x in ["гарантирован", "точно", "безусловно", "всегда дешевле"]):
            risky.append("слишком категоричная формулировка")
        if brief.genre in {"flight_deal", "tour_offer"} and not (brief.price or brief.dates):
            risky.append("оффер без цены/дат — использовать осторожные формулировки")
        if brief.genre in {"visa_or_residence", "payment_abroad"}:
            risky.append("визовые/платёжные правила нужно проверять перед поездкой")
        variant.warnings.extend(x for x in risky if x not in variant.warnings)
        return variant
