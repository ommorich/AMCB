import json
from django import template

register = template.Library()


FIELD_LABELS = {
    "calc_title": "Название расчёта",

    "mass": "Масса, кг",
    "initial_speed": "Начальная скорость, м/с",
    "v0": "Начальная скорость, м/с",

    "time_max": "Максимальное время, с",
    "tMax": "Максимальное время, с",
    "dt": "Шаг dt, с",

    "gamma": "Проводимость γ",
    "delta": "Толщина δ, м",
    "xm": "xm, м",
    "ym": "ym, м",
    "dh1": "dh1, м",
    "dh2": "dh2, м",
    "dm": "dm, м",
    "n": "Количество магнитов n",
    "mu": "Магнитная проницаемость μ",
    "bz": "Индукция Bz, Тл",

    "v": "Скорость, м/с",
    "x": "Путь, м",

    "final_time": "Итоговое время, с",
    "final_speed": "Итоговая скорость, м/с",
    "final_distance": "Итоговый путь, м",

    "points": "Точки F(V)",
    "forceUnit": "Единицы силы",
}


def parse_json_if_needed(value):
    data = value

    for _ in range(2):
        if isinstance(data, str):
            text = data.strip()

            if not text:
                return {}

            if text.startswith("{") or text.startswith("["):
                try:
                    data = json.loads(text)
                    continue
                except Exception:
                    return text

        break

    return data


def label_for_key(key):
    return FIELD_LABELS.get(str(key), str(key))


def format_number(value):
    if isinstance(value, bool):
        return "Да" if value else "Нет"

    if isinstance(value, int):
        return str(value)

    if isinstance(value, float):
        return f"{value:g}"

    return str(value)


def format_value(value):
    value = parse_json_if_needed(value)

    if value is None:
        return "—"

    if isinstance(value, (int, float, bool)):
        return format_number(value)

    if isinstance(value, dict):
        parts = []

        for key, item in value.items():
            parts.append(f"{label_for_key(key)}: {format_value(item)}")

        return "; ".join(parts)

    if isinstance(value, list):
        if len(value) == 0:
            return "—"

        if all(isinstance(item, dict) and "v" in item and "f" in item for item in value):
            preview = value[:5]

            text = "; ".join(
                f"V={format_value(item.get('v'))}, F={format_value(item.get('f'))}"
                for item in preview
            )

            if len(value) > 5:
                text += f"; всего точек: {len(value)}"

            return text

        if len(value) > 8:
            return f"{len(value)} элементов"

        return "; ".join(format_value(item) for item in value)

    return str(value)


@register.filter
def json_table_items(value):
    data = parse_json_if_needed(value)

    if isinstance(data, dict):
        rows = []

        for key, item in data.items():
            rows.append({
                "key": label_for_key(key),
                "value": format_value(item),
            })

        return rows

    if isinstance(data, list):
        rows = []

        for index, item in enumerate(data, start=1):
            rows.append({
                "key": f"Элемент {index}",
                "value": format_value(item),
            })

        return rows

    if data:
        return [{
            "key": "Данные",
            "value": str(data),
        }]

    return []