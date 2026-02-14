# 🤖 Regulator Simulator

[![Python](https://img.shields.io/badge/python-3.8%2B-blue?logo=python)](https://www.python.org/)
[![Pygame-ce](https://img.shields.io/badge/rendering-pygame--ce-green)](https://github.com/pygame-community/pygame-ce)
[![License](https://img.shields.io/badge/license-MIT-purple)](LICENSE)

![pid](https://github.com/user-attachments/assets/79f40d74-2c8f-43d4-a916-836e29e1d29b)

[English](#english) | [Русский](#russian)

<a name="english"></a>

## 🇬🇧 English

A visual and interactive simulator designed to demonstrate and test the principles of PID controllers.

This project accompanies the article explaining how PID works in simple terms. It allows you to experiment with different regulator configurations (P, PD, PI, PID) on a physical model of a robot trying to hold a position or move to a target.

### ✨ Features

* **Real-time Visualization:** See the robot, target position, and force vectors instantly.
* **Physics Engine:** Simulates mass, damping (friction), and external forces (gravity/slope).
* **Interactive Controls:** Change simulation speed, zoom, and pause in real-time.
* **Modular Examples:** Ready-to-run scripts for Relay, P, PD, PI, and PID controllers.
* **Video Recording:** Built-in capability to render simulation footage to MP4 (requires ffmpeg).

### 🛠 Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/RYAZHENKA-11/regulator-simulator.git
    cd regulator-simulator
    ```

2. **Create a virtual environment (optional but recommended):**

    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

### 🚀 Usage

1. Open `main.py`.
2. Uncomment the example you want to run (e.g., `examples.pid_regulator`).

    ```Python
        # import examples.relay_regulator
        # ...
        import examples.pid_regulator  # <--- Uncommented
    ```

3. Run the simulator:

    ```bash
    python main.py
    ```

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
├── main.py                   # Entry point (select examples here)
├── examples/                 # Pre-configured regulator scenarios
├── simulator/                # Core engine
│   ├── Sim.py                # Physics logic
│   └── SimView.py            # Pygame visualization & rendering
└── requirements.txt          # Dependencies
```

<a name="russian"></a>

## 🇷🇺 Русский

Визуальный интерактивный симулятор, созданный для демонстрации принципов работы PID-регуляторов.

Здесь вы можете на практике проверить, как каждая составляющая (P, I, D) влияет на поведение робота, пытающегося остановиться в заданной точке, преодолевая инерцию, трение и внешние силы.

### ✨ Возможности

* **Наглядная визуализация:** Отображение робота, цели, векторов силы и текущих параметров.
* **Физическая модель:** Учитывает массу, затухание (трение), внешние силы (например, наклон поверхности).
* **Интерактивное управление:** Изменяйте скорость времени, масштаб и ставьте паузу прямо во время симуляции.
* **Готовые примеры:** Скрипты для запуска Релейного, P, PD, PI и PID регуляторов.
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

1. Откройте файл main.py.
2. Раскомментируйте строчку с нужным примером. Например, для запуска полноценного PID-регулятора:

    ```Python
        # import examples.relay_regulator
        # ...
        import examples.pid_regulator  # <--- Раскомментировано
    ```

3. Запустите файл:

    ```Bash
    python main.py
    ```

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
├── main.py                   # Точка входа (выберите примеры здесь)
├── examples/                 # Предварительно настроенные сценарии регулятора
├── simulator/                # Основной движок
│   ├── Sim.py                # Физическая логика
│   └── SimView.py            # Визуализация и рендеринг с помощью Pygame
└── requirements.txt          # Зависимости
```
