from .models import EditorialBrief, PostVariant


class EngagementEngine:
    def why_topic_now(self, brief: EditorialBrief) -> str:
        parts = [f"жанр={brief.genre}", f"слот={brief.slot}", f"score={brief.score}"]
        if brief.price:
            parts.append(f"есть цена {brief.price}")
        if brief.date_text:
            parts.append(f"есть дата {brief.date_text}")
        if brief.route_to or brief.city:
            parts.append(f"есть понятная география {brief.route_to or brief.city}")
        return ", ".join(parts)

    def suggested_cta(self, brief: EditorialBrief) -> str:
        mapping = {
            "flight_deal": "проверить конкретный билет и, если идея зацепила, посмотреть проживание",
            "tour_offer": "посмотреть туры или мягко увести в TourJin",
            "destination_post": "сохранить идею, затем билеты/отели/активности",
            "weekend_trip": "сохранить маршрут выходного дня и посмотреть проживание",
            "event_trip": "сначала событие, затем билеты и отели, если поездка логична",
            "visa_or_residence": "написать в личку или перейти к профильному сервису по теме",
            "payment_abroad": "перейти к сервису карт для поездки",
            "practical_travel": "дать полезную ссылку только если она продолжает тему",
        }
        return mapping.get(brief.genre, "CTA должен вытекать из темы, а не быть пришитым сверху")

    def media_hint(self, brief: EditorialBrief) -> str:
        place = brief.route_to or brief.city or brief.country
        if place:
            return f"Нужна реальная travel-фотография по теме: {place}"
        return "Нужна реальная релевантная travel-фотография; если релевантной нет, лучше без медиа"

    def improve_variant(self, brief: EditorialBrief, variant: PostVariant) -> None:
        if brief.genre in {"flight_deal", "tour_offer", "event_trip"} and not variant.cta_text:
            variant.cta_text = "Проверьте детали по ссылкам ниже, пока условия актуальны."
