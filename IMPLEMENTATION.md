# Техническая документация по реализации
## Цифровой двойник участка метро СПб

---

## 📊 1. Данные мониторинга в реальном времени

### 1.1 Типы датчиков и измеряемые параметры

#### **Датчики деформаций конструкций**

**Струнные датчики деформации**
- Модель: SVWG-D01 или аналоги
- Интерфейс: RS-485
- Протокол: Modbus RTU
- Точность: ±0.001 мм
- Измеряют: напряженно-деформированное состояние обделки тоннеля

**Тензометры**
- Размещение: в бетонной обделке тоннелей
- Измеряют: напряжения сжатия/растяжения
- Частота опроса: 1 раз в час (норма), 5 мин (критично)

#### **Датчики наклона зданий**

**MEMS-инклинометры**
- Размещение: на фасадах зданий над тоннелями
- Измеряют: угол наклона относительно горизонта (градусы)
- Точность: 0.001°
- Беспроводная передача: LoRaWAN или NB-IoT
- Частота опроса: 6 часов (норма), 15 мин (критично)

#### **Осадочные и деформационные марки**

**Геодезические марки**
- Тип: оптические отражатели
- Размещение: на стенах зданий, на грунте
- Измерение: тахеометром или GPS/GNSS
- Точность: ±1 мм по вертикали, ±2 мм по горизонтали
- Частота: 1 раз в неделю (вручную) или непрерывно (автоматические станции)

#### **Скважинные датчики**

**Скважинная инклинометрия**
- Измеряют: горизонтальные смещения грунта по глубине
- Глубина скважин: 20-50 м
- Шаг измерений: каждые 0.5-1 м по глубине

**Скважинная экстензометрия**
- Измеряют: вертикальные деформации грунта послойно
- Показывают: какой слой грунта дает наибольшую осадку

#### **Дополнительные датчики**

**Пьезометры**
- Измеряют: уровень грунтовых вод
- Критично для СПб: сильная обводненность грунтов
- Частота: 1 час

**Датчики раскрытия трещин (Crack meters)**
- Размещение: на трещинах в стенах зданий
- Точность: 0.01 мм
- Измеряют: ширину раскрытия трещины

**Акселерометры**
- Размещение: в тоннеле, на зданиях
- Измеряют: вибрации от движения поездов
- Частота опроса: 100-1000 Гц

### 1.2 Архитектура системы сбора данных

```
┌─────────────────────────────────────────────────────────────────┐
│                     ДАТЧИКИ (Уровень 1)                         │
├─────────────────────────────────────────────────────────────────┤
│  Тензометры    Инклинометры    Пьезометры    Crack meters      │
│  (Modbus)      (LoRaWAN)        (RS-485)      (Modbus)          │
└───────┬─────────────┬─────────────┬─────────────┬───────────────┘
        │             │             │             │
        ▼             ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────┐
│              DATA LOGGER (Регистратор данных)                   │
├─────────────────────────────────────────────────────────────────┤
│  • Сбор данных по Modbus RTU / RS-485                           │
│  • Оцифровка и временные метки                                  │
│  • Первичная фильтрация                                         │
│  • Локальное хранение (буфер на 24 часа)                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │ Ethernet / LTE
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│               EDGE GATEWAY (Пограничный шлюз)                   │
├─────────────────────────────────────────────────────────────────┤
│  • Агрегация данных от нескольких логгеров                      │
│  • Преобразование в MQTT/JSON                                   │
│  • Буферизация при потере связи                                 │
│  • Предварительная обработка (аномалии, пропуски)               │
└───────────────────────────┬─────────────────────────────────────┘
                            │ MQTT over TLS
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                 MQTT BROKER (Брокер сообщений)                  │
├─────────────────────────────────────────────────────────────────┤
│  • Mosquitto / HiveMQ / AWS IoT Core                            │
│  • Топики: sensors/{location}/{sensor_type}/{sensor_id}         │
│  • QoS 1 (гарантированная доставка)                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              BACKEND SERVER (Сервер приложений)                 │
├─────────────────────────────────────────────────────────────────┤
│  • FastAPI (Python) - REST API                                  │
│  • MQTT Subscriber - прием данных с датчиков                    │
│  • Data Validation - валидация и фильтрация                     │
│  • Business Logic - расчет метрик, оценка рисков                │
│  • ML Inference - прогнозирование деформаций                    │
└───┬───────────────┬───────────────┬─────────────────────────────┘
    │               │               │
    ▼               ▼               ▼
┌─────────┐  ┌──────────────┐  ┌─────────────┐
│TimescaleDB  │Redis Cache   │  │ML Models    │
│(Временные   │(Кэш данных)  │  │(TensorFlow) │
│ ряды)       │              │  │             │
└─────────┘  └──────────────┘  └─────────────┘
```

### 1.3 Форматы и протоколы передачи данных

#### **Протоколы связи с датчиками**

**Modbus RTU (через RS-485)**
```
Датчик → Data Logger
Скорость: 9600-115200 бод
Адресация: каждый датчик имеет уникальный ID (1-247)
Функции: 0x03 (Read Holding Registers), 0x04 (Read Input Registers)
```

**LoRaWAN (для беспроводных датчиков)**
```
Датчик → LoRaWAN Gateway → Network Server → Application Server
Дальность: до 10 км в городе
Частота: 868 МГц (Европа)
Энергопотребление: батарея 3-5 лет
```

**MQTT (для передачи на сервер)**
```json
Topic: sensors/tunnel_1/strain_gauge/sg_001
Payload:
{
  "sensor_id": "sg_001",
  "sensor_type": "strain_gauge",
  "location": {
    "tunnel": "tunnel_1",
    "chainage": "pk_12+345",
    "depth": 45.2
  },
  "timestamp": "2026-02-22T14:35:20Z",
  "value": 0.024,
  "unit": "mm",
  "status": "ok"
}
```

### 1.4 Частота сбора и хранения данных

| Тип датчика | Норма | Внимание | Критично | Хранение |
|-------------|-------|----------|----------|----------|
| Тензометры обделки | 1 час | 15 мин | 5 мин | 3 года |
| Инклинометры зданий | 6 часов | 1 час | 15 мин | 5 лет |
| Осадочные марки | 1 неделя | 2 раза/неделю | ежедневно | 10 лет |
| Пьезометры (ГВ) | 1 час | 30 мин | 10 мин | 2 года |
| Датчики трещин | 1 час | 15 мин | 5 мин | 5 лет |
| Акселерометры | 10 мин | 1 мин | реал-тайм | 1 год |

---

## 🤖 2. Машинное обучение для прогнозирования

### 2.1 Почему ML необходим?

✅ **Сложная нелинейная динамика:**
- Осадки зависят от множества факторов: грунт, вода, вибрации, температура
- Сезонные колебания (весеннее половодье → повышение уровня грунтовых вод)
- Долговременные тренды + краткосрочные аномалии

✅ **Уникальность каждого участка:**
- Геология СПб: обводненные грунты, кембрийские глины, валуны
- Глубина залегания: 40-60 м
- Каждая станция имеет свои особенности

✅ **ML дает точность 85-95% vs 60-70% классических методов**

### 2.2 Ансамбль ML-моделей (рекомендуемый подход)

#### **Модель 1: LSTM — основа прогнозирования**

**Архитектура:**
```python
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dropout, Dense

model = Sequential([
    # Первый слой LSTM
    LSTM(128, return_sequences=True, input_shape=(60, n_features)),
    Dropout(0.2),

    # Второй слой LSTM
    LSTM(64, return_sequences=True),
    Dropout(0.2),

    # Третий слой LSTM
    LSTM(32, return_sequences=False),

    # Fully connected слои
    Dense(16, activation='relu'),
    Dense(1)  # Прогноз осадки (мм)
])

model.compile(optimizer='adam', loss='mse', metrics=['mae'])
```

**Входные данные (окно 60 дней):**
```python
Features:
- settlement (осадка, мм)
- settlement_rate (скорость осадки, мм/день)
- groundwater_level (уровень ГВ, м)
- temperature (температура грунта, °C)
- vibration_rms (вибрации от поездов, м/с²)
- tunnel_deformation (деформация обделки, мм)
- rainfall (осадки, мм/сутки)

Shape: (batch_size, 60, 7)
```

**Выходные данные:**
```python
# Прогноз на несколько горизонтов
predictions = {
    '1_day': model.predict(X),
    '7_days': model_7d.predict(X),
    '14_days': model_14d.predict(X),
    '30_days': model_30d.predict(X)
}
```

**Метрики качества:**
- MAE < 0.5 мм (отлично), < 1 мм (хорошо)
- MAPE < 10%
- R² > 0.85

---

#### **Модель 2: XGBoost — среднесрочный прогноз**

**Применение:**
- Прогноз на 30-90 дней
- Классификация уровня риска (зеленый/желтый/красный)
- Feature importance (какие факторы важны)

**Пример кода:**
```python
import xgboost as xgb

# Признаки (агрегированные)
X_train = df[[
    'current_settlement_mm',
    'settlement_rate_mm_per_month',
    'settlement_acceleration',
    'groundwater_level_m',
    'avg_temperature_c',
    'vibration_level_rms',
    'tunnel_convergence_mm',
    'building_age_years',
    'distance_to_tunnel_m',
    'soil_type_encoded',
    'season'  # весна/лето/осень/зима
]]

y_train = df['settlement_in_30_days_mm']

model = xgb.XGBRegressor(
    n_estimators=500,
    learning_rate=0.01,
    max_depth=6,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)

model.fit(X_train, y_train)

# Feature importance
importance = model.feature_importances_
```

**Классификация рисков:**
```python
# Многоклассовая классификация
risk_model = xgb.XGBClassifier(
    objective='multi:softmax',
    num_class=3  # 0: зеленый, 1: желтый, 2: красный
)

# Правила классификации
def classify_risk(settlement_pred, settlement_limit):
    if settlement_pred < 0.7 * settlement_limit:
        return 0  # Зеленый
    elif settlement_pred < 0.9 * settlement_limit:
        return 1  # Желтый
    else:
        return 2  # Красный
```

---

#### **Модель 3: Prophet — сезонность**

**Применение:**
- Долгосрочные прогнозы (3-6 месяцев)
- Выделение сезонной компоненты
- Учет праздников и событий (например, строительство рядом)

**Пример:**
```python
from fbprophet import Prophet

# Подготовка данных
df_prophet = df[['date', 'settlement']].rename(
    columns={'date': 'ds', 'settlement': 'y'}
)

# Модель
model = Prophet(
    yearly_seasonality=True,
    weekly_seasonality=False,
    daily_seasonality=False,
    changepoint_prior_scale=0.05
)

# Добавление внешних регрессоров
model.add_regressor('groundwater_level')
model.add_regressor('temperature')

model.fit(df_prophet)

# Прогноз на 90 дней вперед
future = model.make_future_dataframe(periods=90)
forecast = model.predict(future)
```

---

#### **Модель 4: Autoencoder — детекция аномалий**

**Применение:**
- Обнаружение нетипичных паттернов деформаций
- Раннее предупреждение об аномалиях
- Триггер для перевода в режим "Внимание"

**Архитектура:**
```python
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense

# Encoder
input_layer = Input(shape=(n_features,))
encoded = Dense(64, activation='relu')(input_layer)
encoded = Dense(32, activation='relu')(encoded)
encoded = Dense(16, activation='relu')(encoded)  # Bottleneck

# Decoder
decoded = Dense(32, activation='relu')(encoded)
decoded = Dense(64, activation='relu')(decoded)
decoded = Dense(n_features, activation='sigmoid')(decoded)

autoencoder = Model(input_layer, decoded)
autoencoder.compile(optimizer='adam', loss='mse')

# Обучение только на нормальных данных
autoencoder.fit(X_normal, X_normal, epochs=100)

# Детекция аномалий
reconstruction_error = np.mean((X_test - autoencoder.predict(X_test))**2, axis=1)
threshold = np.percentile(reconstruction_error_train, 95)
anomalies = reconstruction_error > threshold
```

---

### 2.3 Ансамблевое объединение моделей

**Взвешенное усреднение:**
```python
def ensemble_prediction(X):
    # Прогнозы от разных моделей
    lstm_pred = lstm_model.predict(X)
    xgb_pred = xgb_model.predict(X)
    prophet_pred = prophet_forecast['yhat'].values

    # Веса (подбираются на валидации)
    w_lstm = 0.5
    w_xgb = 0.3
    w_prophet = 0.2

    # Итоговый прогноз
    final_pred = (w_lstm * lstm_pred +
                  w_xgb * xgb_pred +
                  w_prophet * prophet_pred)

    return final_pred
```

**Доверительные интервалы:**
```python
def confidence_interval(predictions, confidence=0.95):
    mean = np.mean(predictions, axis=0)
    std = np.std(predictions, axis=0)

    # Z-score для 95% доверительного интервала
    z = 1.96

    lower_bound = mean - z * std
    upper_bound = mean + z * std

    return lower_bound, mean, upper_bound
```

### 2.4 Обучение и валидация

**Разделение данных (временное!):**
```python
# Исторические данные (2 года)
train_size = int(len(df) * 0.7)  # 70% = ~504 дня
val_size = int(len(df) * 0.15)   # 15% = ~108 дней
test_size = len(df) - train_size - val_size  # 15% = ~108 дней

train_data = df[:train_size]
val_data = df[train_size:train_size+val_size]
test_data = df[train_size+val_size:]
```

**Переобучение (Continuous Learning):**
```python
# Еженедельное дообучение на новых данных
def retrain_weekly():
    # Получить новые данные за последнюю неделю
    new_data = get_last_week_data()

    # Дообучить модель
    lstm_model.fit(new_data, epochs=5, batch_size=32)

    # Сохранить новую версию
    lstm_model.save(f'models/lstm_v{version}.h5')

    # A/B тестирование
    compare_models(old_model, new_model, test_data)
```

---

## 🎨 3. 3D-визуализация

### 3.1 Технологии

**Three.js** (рекомендуется)
- JavaScript библиотека для WebGL
- Большое комьюнити, много примеров
- Хорошая производительность

**Babylon.js** (альтернатива)
- Более мощный движок
- Встроенная поддержка физики

### 3.2 Слои визуализации

```javascript
// Структура сцены
scene
├── MetroLayer (тоннели и станции)
│   ├── Tunnel_1
│   │   ├── TunnelMesh (3D-модель тоннеля)
│   │   ├── LiningSegments (сегменты обделки)
│   │   └── Sensors (датчики на стенах)
│   └── Station_1
│       ├── Platform
│       └── Halls
│
├── SoilLayer (грунт)
│   ├── Clay_Layers
│   ├── Sand_Layers
│   └── Groundwater_Level
│
└── BuildingsLayer (здания)
    ├── Building_15 (цветовая индикация статуса)
    ├── Building_16
    └── Building_17
```

**Цветовая индикация:**
```javascript
const statusColors = {
    green: 0x00ff00,   // Норма
    yellow: 0xffff00,  // Внимание
    red: 0xff0000      // Критично
};

function updateBuildingColor(building, riskLevel) {
    building.material.color.setHex(statusColors[riskLevel]);
}
```

### 3.3 Интерактивность

```javascript
// Клик по зданию
raycaster.setFromCamera(mouse, camera);
const intersects = raycaster.intersectObjects(buildings);

if (intersects.length > 0) {
    const building = intersects[0].object;
    showBuildingDetails(building.userData.id);
}

// Показать панель с данными
function showBuildingDetails(buildingId) {
    const data = fetchBuildingData(buildingId);
    displayPanel({
        name: data.address,
        settlement: data.current_settlement,
        forecast: data.forecast_30d,
        risk: data.risk_level,
        chart: createSettlementChart(data.history)
    });
}
```

---

## 🏗️ 4. Архитектура системы

### 4.1 Microservices Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                         FRONTEND                               │
│  React + Three.js + Recharts                                   │
│  - 3D-визуализация                                             │
│  - Дашборды и графики                                          │
│  - Уведомления                                                 │
└──────────────────────┬─────────────────────────────────────────┘
                       │ REST API / WebSocket
                       ▼
┌────────────────────────────────────────────────────────────────┐
│                      API GATEWAY                               │
│  Nginx / Kong                                                  │
│  - Маршрутизация запросов                                      │
│  - Аутентификация JWT                                          │
│  - Rate limiting                                               │
└───┬────────────┬────────────┬────────────┬─────────────────────┘
    │            │            │            │
    ▼            ▼            ▼            ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐
│ Sensors │ │   ML    │ │ Reports │ │ Notifications│
│ Service │ │ Service │ │ Service │ │   Service    │
└─────────┘ └─────────┘ └─────────┘ └──────────────┘
    │            │            │            │
    └────────────┴────────────┴────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────────────┐
│                      DATABASES                                 │
│  TimescaleDB  │  PostgreSQL  │  Redis  │  MinIO (файлы)        │
└────────────────────────────────────────────────────────────────┘
```

### 4.2 Sensors Service (FastAPI)

```python
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()

class SensorReading(BaseModel):
    sensor_id: str
    timestamp: datetime
    value: float
    unit: str

@app.post("/api/v1/sensors/readings")
async def ingest_sensor_data(reading: SensorReading):
    # Валидация
    validate_reading(reading)

    # Сохранение в TimescaleDB
    await save_to_timescale(reading)

    # Проверка на аномалии
    if is_anomaly(reading):
        await trigger_alert(reading)

    # Отправка в WebSocket для real-time обновлений
    await websocket_manager.broadcast(reading)

    return {"status": "ok"}

@app.get("/api/v1/sensors/{sensor_id}/history")
async def get_sensor_history(sensor_id: str, days: int = 30):
    data = await fetch_history(sensor_id, days)
    return data
```

### 4.3 ML Service

```python
from fastapi import FastAPI
import joblib
import numpy as np

app = FastAPI()

# Загрузка моделей при старте
lstm_model = load_model('models/lstm_latest.h5')
xgb_model = joblib.load('models/xgb_latest.pkl')

@app.post("/api/v1/ml/predict")
async def predict_settlement(data: PredictionRequest):
    # Подготовка данных
    X = prepare_features(data)

    # Прогноз от ансамбля моделей
    lstm_pred = lstm_model.predict(X)
    xgb_pred = xgb_model.predict(X)

    # Объединение
    final_pred = 0.6 * lstm_pred + 0.4 * xgb_pred

    # Расчет риска
    risk_level = calculate_risk(final_pred, data.settlement_limit)

    return {
        "prediction_1d": float(final_pred[0]),
        "prediction_7d": float(final_pred[1]),
        "prediction_30d": float(final_pred[2]),
        "risk_level": risk_level,
        "confidence": 0.85
    }

@app.post("/api/v1/ml/retrain")
async def retrain_models():
    # Запуск фоновой задачи переобучения
    background_tasks.add_task(retrain_pipeline)
    return {"status": "training started"}
```

---

## 📈 5. Система оценки рисков

### 5.1 Метрики рисков

```python
class RiskAssessment:
    def __init__(self, settlement_limit=10.0):  # мм
        self.settlement_limit = settlement_limit

    def calculate_risk_percentage(self, prediction, limit):
        """
        Риск = вероятность превышения предельного значения
        """
        # Нормальное распределение
        mu = prediction
        sigma = prediction * 0.1  # 10% uncertainty

        # P(X > limit)
        from scipy.stats import norm
        risk = 1 - norm.cdf(limit, mu, sigma)

        return risk * 100  # в процентах

    def classify_status(self, risk_percentage):
        """
        Зеленый / Желтый / Красный
        """
        if risk_percentage < 10:
            return "green"
        elif risk_percentage < 50:
            return "yellow"
        else:
            return "red"

    def safety_index(self, current_value, limit):
        """
        Индекс безопасности (0-100)
        """
        ratio = current_value / limit

        if ratio < 0.5:
            index = 100
        elif ratio < 0.7:
            index = 90
        elif ratio < 0.9:
            index = 70
        elif ratio < 1.0:
            index = 40
        else:
            index = 0

        return index

    def time_to_critical(self, current, rate, limit):
        """
        Время до критического состояния (дни)
        """
        if rate <= 0:
            return float('inf')

        remaining = limit - current
        days = remaining / rate

        return max(0, days)
```

### 5.2 Автоматические рекомендации

```python
class RecommendationEngine:
    def generate_recommendations(self, building_data):
        recommendations = []

        # Проверка статуса
        if building_data['risk_level'] == 'yellow':
            recommendations.append({
                'priority': 'medium',
                'action': 'increase_monitoring_frequency',
                'description': 'Увеличить частоту измерений до 2 раз в неделю',
                'deadline_days': 7
            })

            recommendations.append({
                'priority': 'medium',
                'action': 'schedule_inspection',
                'description': f'Запланировать обследование здания {building_data["address"]} в течение 14 дней',
                'deadline_days': 14
            })

        elif building_data['risk_level'] == 'red':
            recommendations.append({
                'priority': 'critical',
                'action': 'emergency_inspection',
                'description': 'НЕМЕДЛЕННОЕ обследование здания',
                'deadline_days': 1
            })

            recommendations.append({
                'priority': 'critical',
                'action': 'reduce_train_speed',
                'description': 'Рассмотреть ограничение скорости движения поездов',
                'deadline_days': 3
            })

            recommendations.append({
                'priority': 'high',
                'action': 'notify_authorities',
                'description': 'Уведомить Ростехнадзор и администрацию метрополитена',
                'deadline_days': 1
            })

        return recommendations
```

---

## 🔔 6. Система уведомлений

### 6.1 Каналы уведомлений

```python
from enum import Enum

class NotificationChannel(Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    TELEGRAM = "telegram"

class NotificationService:
    def __init__(self):
        self.channels = {
            'email': EmailChannel(),
            'sms': SMSChannel(),
            'push': PushChannel(),
            'telegram': TelegramChannel()
        }

    async def send_alert(self, alert_data):
        # Определить приоритет
        if alert_data['risk_level'] == 'red':
            channels = ['email', 'sms', 'telegram']
        elif alert_data['risk_level'] == 'yellow':
            channels = ['email', 'push']
        else:
            channels = ['push']

        # Отправить по всем каналам
        for channel_name in channels:
            channel = self.channels[channel_name]
            await channel.send(alert_data)

# Пример email-уведомления
def create_email_template(alert):
    return f"""
    <h2>🟡 Предупреждение: Риск превышения допустимых осадок</h2>

    <p><strong>Объект:</strong> {alert['building_address']}</p>
    <p><strong>Текущая осадка:</strong> {alert['current_settlement']} мм</p>
    <p><strong>Прогноз через 30 дней:</strong> {alert['forecast_30d']} мм</p>
    <p><strong>Допустимое значение:</strong> {alert['settlement_limit']} мм</p>

    <p><strong>Риск превышения:</strong> {alert['risk_percentage']}%</p>

    <h3>Рекомендации:</h3>
    <ul>
        <li>Увеличить частоту измерений до 2 раз в неделю</li>
        <li>Запланировать обследование в течение 14 дней</li>
    </ul>

    <p><a href="https://digital-twin.metro.spb.ru/buildings/{alert['building_id']}">
       Открыть в системе
    </a></p>
    """
```

---

## 📊 7. База данных

### 7.1 TimescaleDB (временные ряды)

```sql
-- Таблица для данных датчиков
CREATE TABLE sensor_readings (
    time TIMESTAMPTZ NOT NULL,
    sensor_id VARCHAR(50) NOT NULL,
    sensor_type VARCHAR(20) NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    unit VARCHAR(10),
    status VARCHAR(10),
    location_id VARCHAR(50)
);

-- Превратить в hypertable
SELECT create_hypertable('sensor_readings', 'time');

-- Индексы
CREATE INDEX idx_sensor_id ON sensor_readings (sensor_id, time DESC);
CREATE INDEX idx_location ON sensor_readings (location_id, time DESC);

-- Автоматическое удаление старых данных (retention policy)
SELECT add_retention_policy('sensor_readings', INTERVAL '3 years');

-- Continuous aggregates для производительности
CREATE MATERIALIZED VIEW sensor_readings_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS hour,
    sensor_id,
    AVG(value) as avg_value,
    MAX(value) as max_value,
    MIN(value) as min_value
FROM sensor_readings
GROUP BY hour, sensor_id;
```

### 7.2 PostgreSQL (метаданные)

```sql
-- Таблица зданий
CREATE TABLE buildings (
    id SERIAL PRIMARY KEY,
    address VARCHAR(255) NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    construction_year INT,
    floors INT,
    settlement_limit_mm DECIMAL(5, 2) DEFAULT 10.0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Таблица датчиков
CREATE TABLE sensors (
    id VARCHAR(50) PRIMARY KEY,
    type VARCHAR(20) NOT NULL,
    building_id INT REFERENCES buildings(id),
    location_description TEXT,
    installation_date DATE,
    status VARCHAR(10) DEFAULT 'active'
);

-- Таблица предупреждений
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    building_id INT REFERENCES buildings(id),
    risk_level VARCHAR(10) NOT NULL,
    risk_percentage DECIMAL(5, 2),
    message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active'
);
```

---

## 🚀 8. Развертывание (DevOps)

### 8.1 Docker Compose (для разработки)

```yaml
version: '3.8'

services:
  # Backend API
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/metro_twin
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
      - timescaledb

  # Frontend
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - api

  # TimescaleDB
  timescaledb:
    image: timescale/timescaledb:latest-pg14
    ports:
      - "5433:5432"
    environment:
      - POSTGRES_PASSWORD=password
    volumes:
      - timescale_data:/var/lib/postgresql/data

  # PostgreSQL
  postgres:
    image: postgis/postgis:14-3.2
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # Redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # MQTT Broker
  mosquitto:
    image: eclipse-mosquitto:2
    ports:
      - "1883:1883"
      - "9001:9001"
    volumes:
      - ./mosquitto/config:/mosquitto/config
      - mosquitto_data:/mosquitto/data

volumes:
  timescale_data:
  postgres_data:
  mosquitto_data:
```

### 8.2 Kubernetes (для production)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: metro-twin/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secrets
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

---

## 📦 9. Технологический стек (итоговый)

### Frontend
- **React 18** — UI framework
- **Three.js** — 3D-визуализация
- **Recharts** — графики и диаграммы
- **Material-UI** — компоненты интерфейса
- **Socket.io-client** — WebSocket для real-time

### Backend
- **FastAPI** (Python) — REST API
- **Pydantic** — валидация данных
- **asyncio** — асинхронность
- **paho-mqtt** — MQTT клиент
- **Celery** — фоновые задачи

### Databases
- **TimescaleDB** — временные ряды датчиков
- **PostgreSQL + PostGIS** — метаданные, геопространственные данные
- **Redis** — кэш, очереди
- **MinIO** — хранение файлов (отчеты, 3D-модели)

### ML/AI
- **TensorFlow/Keras** — LSTM модели
- **XGBoost** — градиентный бустинг
- **Prophet** — временные ряды
- **scikit-learn** — preprocessing, metrics
- **MLflow** — версионирование моделей

### DevOps
- **Docker** — контейнеризация
- **Kubernetes** — оркестрация
- **GitLab CI/CD** — автоматизация
- **Prometheus + Grafana** — мониторинг
- **Nginx** — reverse proxy

### IoT
- **Modbus** — протокол датчиков
- **MQTT (Mosquitto)** — message broker
- **LoRaWAN** — беспроводные датчики

---

## 🎯 10. Этапы реализации

### MVP (3-4 месяца)
- ✅ Подключение 5-10 датчиков
- ✅ Базовая 3D-визуализация
- ✅ Простая LSTM-модель
- ✅ Дашборд с графиками

### Версия 2.0 (6-8 месяцев)
- ✅ Масштабирование до 100 датчиков
- ✅ Ансамбль ML-моделей
- ✅ Автоматические рекомендации
- ✅ Система уведомлений

### Production (12-18 месяцев)
- ✅ Тысячи датчиков
- ✅ Интеграция с системами метро
- ✅ Мобильное приложение
- ✅ MLOps pipeline

---

**Документ подготовлен для дипломного проекта "Цифровой двойник участка метро СПб"**
**Горный университет им. Екатерины II, 2026**
