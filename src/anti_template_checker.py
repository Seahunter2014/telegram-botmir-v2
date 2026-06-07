from .config_loader import read_json

class AntiTemplateChecker:
    def __init__(self):
        self.forbidden = [x.lower() for x in read_json("forbidden_phrases.json", [])]
        self.internal_markers = ["сигнал для", "genre:", "slot:", "editorial_angle", "вариант поста", "как ai"]

    def check(self, title: str, body: str, cta: str = "") -> tuple[bool, list[str]]:
        text = f"{title}\n{body}\n{cta}".lower()
        errors = []
        for phrase in self.forbidden:
            if phrase and phrase in text:
                errors.append(f"Запрещённая фраза: {phrase}")
        for marker in self.internal_markers:
            if marker in text:
                errors.append(f"Внутренний технический маркер: {marker}")
        if len(title.strip()) < 18:
            errors.append("Слишком слабый/короткий заголовок")
        if len(body.strip()) < 180:
            errors.append("Тело поста слишком короткое для редакционного поста")
        if "билет" in text and any(w in text for w in ["вебинар", "эфир", "вакансия"]):
            errors.append("Билеты вставлены в не travel-контекст")
        return (len(errors) == 0), errors
