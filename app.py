# Прогноз северного сияния в Мурманске
# Программа берёт данные из двух открытых сервисов (по API)
# и считает шанс увидеть северное сияние с помощью условий if / elif / else.

import datetime

import requests
import streamlit as st

# Координаты города Мурманска
LAT = 68.97
LON = 33.07

# Адреса открытых сервисов
WEATHER_URL = (
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={LAT}&longitude={LON}"
    "&current=temperature_2m,cloud_cover,is_day"
    "&timezone=Europe%2FMoscow"
)
KP_URL = "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json"


# Запоминаем ответ на 10 минут, чтобы страница открывалась быстрее
@st.cache_data(ttl=600)
def get_weather():
    """Спрашиваем у сервиса Open-Meteo погоду в Мурманске."""
    answer = requests.get(WEATHER_URL, timeout=15)
    data = answer.json()
    return data["current"]


@st.cache_data(ttl=600)
def get_kp():
    """Спрашиваем у сервиса NOAA текущий индекс Kp (силу магнитной бури)."""
    answer = requests.get(KP_URL, timeout=15)
    data = answer.json()
    last = data[-1]  # самая свежая запись в списке
    return last["estimated_kp"]


def count_chance(kp, clouds, is_day, month):
    """Считаем шанс увидеть сияние в процентах и объясняем почему."""
    reasons = []

    # Шаг 1. Сила магнитной бури (индекс Kp от 0 до 9)
    if kp < 1:
        chance = 5
        reasons.append("Солнце спокойное, магнитной бури нет")
    elif kp < 2:
        chance = 20
        reasons.append("Слабая солнечная активность")
    elif kp < 3:
        chance = 40
        reasons.append("Небольшая активность — сияние может быть у горизонта")
    elif kp < 4:
        chance = 60
        reasons.append("Хорошая активность — сияние вероятно")
    elif kp < 5:
        chance = 80
        reasons.append("Сильная активность — сияние почти наверняка")
    else:
        chance = 95
        reasons.append("Магнитная буря! Сияние может быть по всему небу")

    # Шаг 2. Облака: если небо закрыто, сияние не видно
    if clouds > 80:
        chance = chance * 0.1
        reasons.append("Небо почти полностью затянуто облаками")
    elif clouds > 50:
        chance = chance * 0.5
        reasons.append("Облаков много, видно только часть неба")
    elif clouds > 20:
        chance = chance * 0.8
        reasons.append("Есть немного облаков")
    else:
        reasons.append("Небо ясное")

    # Шаг 3. Светло или темно
    if month in (5, 6, 7):
        chance = 0
        reasons.append("Летом полярный день и белые ночи — слишком светло")
    elif is_day == 1:
        chance = 0
        reasons.append("Сейчас день — сияние не видно при солнечном свете")
    else:
        reasons.append("Сейчас темно — хорошее время для наблюдения")

    return round(chance), reasons


# ---------- Внешний вид страницы ----------

st.set_page_config(page_title="Северное сияние в Мурманске", page_icon="🌌")
st.title("🌌 Прогноз северного сияния в Мурманске")
st.write("Программа узнаёт погоду и солнечную активность через интернет "
         "и считает, какой шанс увидеть северное сияние прямо сейчас.")

try:
    weather = get_weather()
    kp = get_kp()
except Exception:
    st.error("Не удалось получить данные. Проверьте подключение к интернету.")
    st.stop()

clouds = weather["cloud_cover"]
is_day = weather["is_day"]
temperature = weather["temperature_2m"]
month = datetime.datetime.now().month

st.subheader("Данные, полученные по API")
col1, col2, col3 = st.columns(3)
col1.metric("Индекс Kp", round(kp, 1))
col2.metric("Облачность", f"{clouds} %")
col3.metric("Температура", f"{temperature} °C")

chance, reasons = count_chance(kp, clouds, is_day, month)

st.subheader("Прогноз")
st.metric("Шанс увидеть северное сияние", f"{chance} %")
st.progress(chance / 100)

if chance >= 50:
    st.success("Отличный шанс! Одевайтесь теплее и смотрите на север.")
elif chance >= 20:
    st.warning("Шанс есть, но небольшой. Можно попробовать.")
else:
    st.info("Сегодня сияние увидеть вряд ли получится.")

st.subheader("Почему такой прогноз")
for reason in reasons:
    st.write("•", reason)

# ---------- Режим эксперимента ----------

#st.divider()
#st.subheader("🔬 Проверь сам")
#st.write("Подвигайте ползунки и посмотрите, как меняется шанс.")

#test_kp = st.slider("Индекс Kp", 0.0, 9.0, 3.0, 0.5)
#test_clouds = st.slider("Облачность, %", 0, 100, 10)
#test_dark = st.checkbox("На улице темно", value=True)

#test_chance, test_reasons = count_chance(test_kp, test_clouds,
                                         0 if test_dark else 1, 12)
#st.metric("Шанс в эксперименте", f"{test_chance} %")

st.caption("Источники данных: Open-Meteo (погода) и NOAA SWPC (индекс Kp).")
