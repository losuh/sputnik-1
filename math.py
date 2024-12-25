import matplotlib
matplotlib.use('Agg')  # Используем неблокирующий бэкенд
import numpy as np
import matplotlib.pyplot as plt
import math

def rocket_trajectory():
    # Константы
    g0 = 9.81  # ускорение свободного падения на поверхности Земли, м/с^2
    rho0 = 1.225  # плотность воздуха на уровне моря, кг/м^3
    Cd = 0.742  # коэффициент сопротивления
    A_initial = 19.0  # начальная площадь поперечного сечения ракеты, м^2
    R = 6371000  # радиус Земли, м

    # Характеристики ступеней
    stage1_thrust_per_engine = 1000.3 * 1000  # тяга одного двигателя первой ступени в невесомости, Н
    stage1_engines = 4  # количество двигателей первой ступени
    stage1_thrust = stage1_engines * stage1_thrust_per_engine  # общая тяга первой ступени, Н
    stage1_mass_dry = 1740 * stage1_engines  # сухая масса первой ступени, кг
    stage1_mass_start = 44000 * stage1_engines  # стартовая масса первой ступени, кг

    stage2_thrust = 941.4 * 1000  # тяга второй ступени в невесомости, Н
    stage2_mass_dry = 2840  # сухая масса второй ступени, кг
    stage2_mass_start = 94000  # стартовая масса второй ступени, кг

    # Расчёты
    m0 = stage1_mass_start + stage2_mass_start  # начальная масса ракеты, кг
    fuel_mass1 = stage1_mass_start - stage1_mass_dry  # масса топлива первой ступени, кг
    fuel_mass2 = stage2_mass_start - stage2_mass_dry  # масса топлива второй ступени, кг

    burn_rate1 = 335 * stage1_engines  # скорость сгорания топлива первой ступени, кг/с
    burn_rate2 = 313.5  # скорость сгорания топлива второй ступени, кг/с

    maneuver_start_altitude = 12000  # начало манёвра, м
    maneuver_end_altitude = 110000  # конец манёвра, м
    dt = 0.1  # шаг времени, с
    t_max = 400  # максимальное время, с

    target_periapsis = 200000  # целевая высота апоцентра, м

    # Начальные условия
    t = 0  # начальное время
    x, y = 0, 0  # начальные координаты (м)
    vx, vy = 0, 0  # начальные скорости (м/с)
    angle = 90  # начальный угол наклона тяги (градусы)
    mass = m0  # начальная масса
    A = A_initial  # текущая площадь поперечного сечения

    # Массивы для хранения данных
    times = []
    altitudeT = []
    speedT = []
    angleT = []
    massT = []

    def altitude():
        return y

    def vertical_speed():
        return vy

    while t < t_max and y >= 0:
        # Пересчёт ускорения свободного падения и плотности воздуха
        g = g0 * (R / (R + y))**2
        rho = rho0 * np.exp(-y / 8500)  # аппроксимация снижения плотности воздуха

        # Угол наклона тяги во время манёвра
        if maneuver_start_altitude <= altitude() <= maneuver_end_altitude:
            angle = math.asin(math.sqrt((maneuver_end_altitude - altitude()) / (maneuver_end_altitude - maneuver_start_altitude))) * 57.2958
        elif altitude() > maneuver_end_altitude:
            # Управление ракетой после манёвра
            if altitude() > target_periapsis + 10000 and vertical_speed() > 50:
                print(-10, vertical_speed(), altitude(), t)
                angle = -10.0
            else:
                print(0, vertical_speed(), altitude(), t)
                angle = 0.0

        angle_rad = np.radians(angle)

        # Силы и расход топлива
        if fuel_mass1 > 0:
            thrust1 = stage1_thrust
            fuel_mass1 -= burn_rate1 * dt
        else:
            thrust1 = 0

        if fuel_mass2 > 0:
            thrust2 = stage2_thrust
            fuel_mass2 -= burn_rate2 * dt
        else:
            thrust2 = 0

        if fuel_mass1 <= 0 and mass > stage2_mass_dry:
            mass -= stage1_mass_dry  # Отделение второй ступени
            A /= 5  # Уменьшение площади поперечного сечения

        thrust = thrust1 + thrust2
        weight = mass * g

        # Расчёт скорости и предотвращение переполнения
        v_squared = vx**2 + vy**2
        if v_squared > 1e10:  # Ограничение на скорость, чтобы избежать переполнения
            v_squared = 1e10
        v = np.sqrt(v_squared)

        drag = 0.5 * rho * Cd * A * v_squared
        drag_x = drag * (vx / v) if v > 1e-6 else 0
        drag_y = drag * (vy / v) if v > 1e-6 else 0

        # Уравнения движения
        thrust_x = thrust * np.cos(angle_rad)
        thrust_y = thrust * np.sin(angle_rad)
        ax = (thrust_x - drag_x) / mass
        ay = (thrust_y - drag_y - weight) / mass

        # Обновление скоростей и координат
        vx += ax * dt
        vy += ay * dt
        x += vx * dt
        y += vy * dt

        # Обновление массы
        mass = stage1_mass_dry + stage2_mass_dry + fuel_mass1 + fuel_mass2

        # Обновление времени
        t += dt

        # Сохранение данных
        times.append(t)
        altitudeT.append(y)
        speedT.append(v)
        angleT.append(angle)
        massT.append(mass)

    # Сохранение графика в файл
    plt.figure(figsize=(10, 6))
    plt.plot(times, altitudeT, label="Высота", color='r')
    plt.title("Теоретический график высоты от времени")
    plt.xlim(0, 300)  # Фиксированная шкала времени
    plt.ylim(0, 350000)  # Фиксированная шкала высоты
    plt.xlabel("Время (с)")
    plt.ylabel("Высота (м)")
    plt.grid()
    plt.legend()
    plt.savefig('teoretical_trajectory.png')  # Сохранение графика в файл

    plt.figure(figsize=(10, 6))
    plt.plot(times, speedT, label="Скорость", color='r')
    plt.title("Теоретический график скорости от времени")
    plt.xlim(0, 300)  # Фиксированная шкала времени
    plt.ylim(0, 10000)  # Фиксированная шкала высоты
    plt.xlabel("Время (с)")
    plt.ylabel("Скорость (м/c)")
    plt.grid()
    plt.legend()
    plt.savefig('teoretical_speed.png')  # Сохранение графика в файл

    plt.figure(figsize=(10, 6))
    plt.plot(times, angleT, label="Угол", color='r')
    plt.title("Теоретический график угла от времени")
    plt.xlim(0, 300)  # Фиксированная шкала времени
    plt.ylim(-20, 100)  # Фиксированная шкала высоты
    plt.xlabel("Время (с)")
    plt.ylabel("Угол (градусы)")
    plt.grid()
    plt.legend()
    plt.savefig('teoretical_angle.png')  # Сохранение графика в файл

    plt.figure(figsize=(10, 6))
    plt.plot(times, massT, label="Масса", color='r')
    plt.title("Теоретический график массы от времени")
    plt.xlim(0, 300)  # Фиксированная шкала времени
    plt.ylim(0, 300000)  # Фиксированная шкала высоты
    plt.xlabel("Время (с)")
    plt.ylabel("Масса (кг)")
    plt.grid()
    plt.legend()
    plt.savefig('teoretical_mass.png')  # Сохранение графика в файл

if __name__ == "__main__":
    rocket_trajectory()
