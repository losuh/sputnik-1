import matplotlib
matplotlib.use('Agg')  # Используем неблокирующий бэкенд
from time import sleep, time
import math
import krpc
import asyncio
import matplotlib.pyplot as plt

conn = krpc.connect(name='Launch into orbit')

vessel = conn.space_center.active_vessel
# Set up streams for telemetry
#ut = conn.add_stream(getattr, conn.space_center, 'ut')
altitude = conn.add_stream(getattr, vessel.flight(), 'mean_altitude', 'vertical_speed')
vertical_speed = conn.add_stream(getattr, vessel.flight(vessel.orbit.body.reference_frame), 'vertical_speed')
apoapsis = conn.add_stream(getattr, vessel.orbit, 'apoapsis_altitude')
#stage_1_resources = vessel.resources_in_decouple_stage(stage=1, cumulative=False)
#srb_fuel = conn.add_stream(stage_1_resources.amount, 'SolidFuel')

stage1_engines = [engine for engine in vessel.parts.engines if 'stage1' in engine.part.tag]

#fuel_tank = vessel.parts.with_tag('accelerator')[0]

# Получение объекта ресурса LiquidFuel
#liquid_fuel_resource = fuel_tank.resources.with_resource('Kerosene')[0]

# Получение текущего количества топлива
#current_fuel = liquid_fuel_resource.amount

#vessel.control.rcs = True
vessel.control.throttle = 0.0
target_periapsis = 200000
maneuver_start_altitude = 12000
maneuver_end_altitude = 110000
target_apoapsis = 900000
angle = 90.0
v_orb = 7790
r_earth = 6371 * 10**3
g = 9.81
orbit_angle = 65.1


times = []
altitudeT = []
speedT = []
massT = []
angleT = []


ap = vessel.auto_pilot
sleep(1)
print('Начало отсчёта')
sleep(1)
# Countdown...
print('3...')
sleep(1)
print('2...')
sleep(1)
print('1...')
sleep(1)
print('Запуск!')
start_time = time()

flag_accelerators_in_place = True
async def infinite_printer():
    while True:
        global vessel, flag_accelerators_in_place, angle
        if flag_accelerators_in_place == True and stage1_engines[0].thrust == 0:
            flag_accelerators_in_place = False
            vessel.control.activate_next_stage()
            sleep(1)
            ap.engage()
            sleep(1)
            ap.target_pitch_and_heading(angle, 90.0 + orbit_angle)
            sleep(1)
        print(stage1_engines[0].thrust)
        elapsed_time = time() - start_time
        print(f"Время с запуска = {elapsed_time:.2f}")
        vessel = conn.space_center.active_vessel
        current_stage = vessel.control.current_stage
        print(f"Текущая активная ступень: {current_stage}")
        #print('altitude', altitude())
        #print('apoapsis', vessel.orbit.apoapsis_altitude)
        #print('periapsis', vessel.orbit.periapsis_altitude)
        #print('speed', vessel.orbit.speed)
        #print('Vspeed', vertical_speed())
        #print('VVspeed', vessel.surface_velocity_reference_frame)
        #print('VVVspeed', vessel.orbit.argument_of_periapsis)
        #print('Orbitalspeed', vessel.orbit.orbital_speed)
        #print('Orbitalspeed100', vessel.orbit.orbital_speed_at(100))
        #print('liquid_fuel', vessel.resources.amount('LiquidFuel'))
        #print('drag', vessel.flight().drag)
        print('\n')

        times.append(elapsed_time)
        altitudeT.append(altitude())
        speedT.append(vessel.orbit.speed)
        massT.append(vessel.mass)
        angleT.append(angle)

        await asyncio.sleep(0.5)

async def main():
    global flag_accelerators_in_place, angle
    flag_accelerators_in_place = True
    asyncio.create_task(infinite_printer())
    vessel.control.throttle = 0.1
    vessel.control.activate_next_stage()
    await asyncio.sleep(2.86)
    vessel.control.activate_next_stage()
    ap.engage()
    ap.target_pitch_and_heading(90.0, 90.0 + orbit_angle)
    print('Угол изменён на 90')

    vessel.control.rcs = True
    vessel.control.sas = True

    while altitude() < maneuver_start_altitude:
        await asyncio.sleep(0.1)

    #ap.target_pitch_and_heading(85.0, 90.0 + orbit_angle)
    #print('Угол изменён на 85')

    angle = 90.0

    acceleration = 10.0
    t0 = time()
    speed = 0
    while angle > 0.0:
        try:
            angle = math.asin((math.sqrt(maneuver_end_altitude - altitude()) / math.sqrt(maneuver_end_altitude - maneuver_start_altitude))) * 57.2958
        except:
            angle = 0.0
        ap.target_pitch_and_heading(angle, 90.0 + orbit_angle)
        print(f'Угол изменён на {angle}')
        await asyncio.sleep(0.1)

    ap.target_pitch_and_heading(0.0, 90.0 + orbit_angle)

    while vessel.orbit.apoapsis_altitude < target_apoapsis or vessel.orbit.periapsis_altitude < target_periapsis:
        if altitude() > target_periapsis + 12000 and vertical_speed() > 50:
            angle = -10.0
            ap.target_pitch_and_heading(angle, 90.0 + orbit_angle)
        else:
            angle = 0.0
            ap.target_pitch_and_heading(angle, 90.0 + orbit_angle)
        await asyncio.sleep(0.1)

    vessel.control.throttle = 0.0
    sleep(2)
    vessel.control.activate_next_stage()
    sleep(1)
    vessel.control.activate_next_stage()

    plt.figure(figsize=(10, 6))
    plt.plot(times, altitudeT, label="Высота", color='b')
    plt.title("Теоретический график высоты от времени")
    plt.xlim(0, 300)  # Фиксированная шкала времени
    plt.ylim(0, 350000)  # Фиксированная шкала высоты
    plt.xlabel("Время (с)")
    plt.ylabel("Высота (м)")
    plt.grid()
    plt.legend()
    plt.savefig('real_trajectory.png')  # Сохранение графика в файл

    plt.figure(figsize=(10, 6))
    plt.plot(times, speedT, label="Скорость", color='b')
    plt.title("Теоретический график скорости от времени")
    plt.xlim(0, 300)  # Фиксированная шкала времени
    plt.ylim(0, 10000)  # Фиксированная шкала высоты
    plt.xlabel("Время (с)")
    plt.ylabel("Скорость (м/c)")
    plt.grid()
    plt.legend()
    plt.savefig('real_speed.png')  # Сохранение графика в файл

    plt.figure(figsize=(10, 6))
    plt.plot(times, angleT, label="Угол", color='b')
    plt.title("Теоретический график угла от времени")
    plt.xlim(0, 300)  # Фиксированная шкала времени
    plt.ylim(-20, 100)  # Фиксированная шкала высоты
    plt.xlabel("Время (с)")
    plt.ylabel("Угол (градусы)")
    plt.grid()
    plt.legend()
    plt.savefig('real_angle.png')  # Сохранение графика в файл

    plt.figure(figsize=(10, 6))
    plt.plot(times, massT, label="Масса", color='b')
    plt.title("Теоретический график массы от времени")
    plt.xlim(0, 300)  # Фиксированная шкала времени
    plt.ylim(0, 300000)  # Фиксированная шкала высоты
    plt.xlabel("Время (с)")
    plt.ylabel("Масса (кг)")
    plt.grid()
    plt.legend()
    plt.savefig('real_mass.png')  # Сохранение графика в файл

asyncio.run(main())
