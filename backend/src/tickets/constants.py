"""Общие константы модуля заявок."""

# Заявка считается просроченной, если она в работе дольше этого срока.
OVERDUE_DAYS = 15

# Границы города Витебска (широта/долгота).
# Взяты по bounding box города из OpenStreetMap/Nominatim и округлены наружу,
# чтобы охватить все районы, включая северные и западные окраины.
VITEBSK_LAT_MIN = 55.13
VITEBSK_LAT_MAX = 55.32
VITEBSK_LNG_MIN = 30.07
VITEBSK_LNG_MAX = 30.33


def is_in_vitebsk(latitude: float, longitude: float) -> bool:
    """Проверить, что координаты находятся в границах Витебска."""
    return (
        VITEBSK_LAT_MIN <= latitude <= VITEBSK_LAT_MAX
        and VITEBSK_LNG_MIN <= longitude <= VITEBSK_LNG_MAX
    )
