# 🤖 Regulator Simulator

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![Pygame-ce](https://img.shields.io/badge/rendering-pygame--ce-green)](https://github.com/pygame-community/pygame-ce)
[![License](https://img.shields.io/badge/license-MIT-purple)](LICENSE)

![pid](https://github.com/user-attachments/assets/79f40d74-2c8f-43d4-a916-836e29e1d29b)

[English](#english) | [Русский](#russian)

<a name="english"></a>

## 🇬🇧 English

A visual and interactive simulator designed to demonstrate and test the principles of PID or other controllers.

This project accompanies the article explaining how PID works in simple terms. It allows you to experiment with different regulator configurations on a physical model of a robot trying to hold a position or move to a target.

### ✨ Features

* **Real-time Visualization:** See the robot, target position, and force vectors instantly.
* **Physics Engine:** Simulates mass, damping (friction), and external forces (gravity/slope).
* **Interactive Controls:** Change simulation speed, zoom, and pause in real-time.
* **Complete Example:** `main.py` ships a ready-to-run PID regulator with both interactive playback and video export.
* **Video Recording:** Built-in capability to render simulation footage to MP4 (requires ffmpeg).

### 🛠 Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/RYAZHENKA-11/regulator-simulator.git
    cd regulator-simulator
    ```

2. **Create a virtual environment (optional but recommended):**

    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # macOS/Linux
    source .venv/bin/activate
    ```

3. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

### 🚀 Usage

`main.py` is a complete, ready-to-run example of a PID regulator.

Run the interactive simulator (opens a window):

```bash
python main.py
```

Render a video instead of opening a window:

```bash
python main.py --export --seconds 10 --speed 1.0 --fps 60 --name my_video.mp4
```

Window size, position, zoom and speed are saved to `.settings.json` when
you quit the interactive session and restored on the next launch.

### 🎮 Controls

| Key         | Action                               |
| ----------- | ------------------------------------ |
| Space       | Pause / Resume simulation            |
| R           | Restart simulation (reset state)     |
| Ctrl + +/-  | Zoom In / Out                        |
| Shift + +/- | Increase / Decrease simulation speed |
| Shift + R   | Reset speed to 1.0x                  |
| Q or Ctrl+W | Quit                                 |

### 📂 Project Structure

```text
.
├── main.py  # Complete example
├── simulator/  # Core engine
│   ├── __init__.py  # Package exports
│   ├── simulator.py  # Physics and regulator callback interface
│   ├── window_manager.py  # SDL2 window lifecycle
│   ├── graphics_renderer.py  # Low-level rendering with anti-aliasing
│   ├── simulation_renderer.py  # Simulation visualization
│   ├── player_controller.py  # Interactive control loop
│   ├── video_exporter.py  # MP4 recording via FFmpeg
│   ├── settings.py  # Saved window/scale/speed settings
│   ├── fonts/  # Bundled font (Inter-Medium.ttf)
│   └── images/  # Robot and arrow sprites
└── requirements.txt  # Dependencies
```

<a name="russian"></a>

## 🇷🇺 Русский

Визуальный интерактивный симулятор, созданный для демонстрации принципов работы PID и иных регуляторов.

Здесь вы можете на практике проверить, как каждая составляющая (P, I, D) влияет на поведение робота, пытающегося остановиться в заданной точке, преодолевая инерцию, трение и внешние силы.

### ✨ Возможности

* **Наглядная визуализация:** Отображение робота, цели, векторов силы и текущих параметров.
* **Физическая модель:** Учитывает массу, затухание (вязкое трение), внешние силы (наклон поверхности).
* **Интерактивное управление:** Изменяйте скорость времени, масштаб и ставьте паузу прямо во время симуляции.
* **Готовый пример:** В `main.py` — полностью готовый PID-регулятор с интерактивным запуском и записью видео.
* **Запись видео:** Возможность рендеринга симуляции в MP4 (требуется ffmpeg).

### 🛠 Установка

1. **Клонируйте репозиторий:**

    ```bash
    git clone https://github.com/RYAZHENKA-11/regulator-simulator.git
    cd regulator-simulator
    ```

2. **Создайте виртуальное окружение (рекомендуется):**

    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3. **Установите зависимости:**

    ```bash
    pip install -r requirements.txt
    ```

### 🚀 Запуск

`main.py` — полностью готовый пример PID-регулятора.

Интерактивный запуск (откроется окно):

```bash
python main.py
```

Запись видео вместо окна:

```bash
python main.py --export --seconds 10 --speed 1.0 --fps 60 --name my_video.mp4
```

Размер окна, его позиция, масштаб и скорость сохраняются в `.settings.json`
при выходе из интерактивного режима и восстанавливаются при следующем запуске.

### 🎮 Управление

| Клавиша        | Действие                           |
| -------------- | ---------------------------------- |
| Space (Пробел) | Пауза / Продолжить                 |
| R              | Рестарт (сброс состояния в начало) |
| Ctrl + +/-     | Приблизить / Отдалить (Масштаб)    |
| Shift + +/-    | Ускорить / Замедлить время         |
| Shift + R      | Сбросить скорость времени на 1.0x  |
| Q или Ctrl+W   | Выход                              |

### 📂 Структура проекта

```text
.
├── main.py  # Готовый пример
├── simulator/  # Основной движок
│   ├── __init__.py  # Экспорт пакета
│   ├── simulator.py  # Физика и интерфейс регулятора
│   ├── window_manager.py  # Жизненный цикл SDL2-окна
│   ├── graphics_renderer.py  # Низкоуровневый рендеринг с антиалиасингом
│   ├── simulation_renderer.py  # Визуализация симуляции
│   ├── player_controller.py  # Интерактивный цикл управления
│   ├── video_exporter.py  # Запись MP4 через FFmpeg
│   ├── settings.py  # Сохранённые настройки окна/масштаба/скорости
│   ├── fonts/  # Встроенный шрифт (Inter-Medium.ttf)
│   └── images/  # Спрайты робота и стрелки
└── requirements.txt  # Зависимости
```
