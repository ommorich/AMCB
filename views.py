import json
import numpy as np

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from .forms import BrakingForm
from .force_speed import force
from .models import CalculationHistory


# =========================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =========================

def save_history(source_page: str, source_data: dict, force_data: dict | None = None, motion_data: dict | None = None, title: str = ""):
    if not title:
        title = f"{dict(CalculationHistory.SOURCE_CHOICES).get(source_page, source_page)} от {timezone.now().strftime('%d.%m.%Y %H:%M')}"
    
    record = CalculationHistory.objects.create(
        source_page=source_page,
        title=title,
        source_data=json.dumps(source_data, ensure_ascii=False, indent=2),
        force_data=json.dumps(force_data, ensure_ascii=False) if force_data else "",
        motion_data=json.dumps(motion_data, ensure_ascii=False) if motion_data else "",
    )
    return record


def braking_force(v: float, wnn: float, m: float,
                  Gamma: int, Delta: float, Xm: float, Ym: float,
                  dh1: float, dh2: float, dm: float, N: int, mu: int, Bz: float):
    try:
        Ft, wnn = force(v, wnn, Gamma, Delta, Xm, Ym, dh1, dh2, dm, N, mu, Bz)
        g = Ft / m
        a = Ft * 9.8 / m
    except ZeroDivisionError:
        return 0, 0, 0, 0
    return -Ft * 9.8, g, a, Ft


def runge_kutta(v0: float, t_max: float, dt: float, m: float,
                Gamma: int, Delta: float, Xm: float, Ym: float, dh1: float,
                dh2: float, dm: float, N: int, mu: float, Bz: float, wnn=1):
    t_values = np.arange(0, t_max, dt)
    v_values, x_values = np.zeros_like(t_values), np.zeros_like(t_values)
    overload_values = np.zeros_like(t_values)
    acceleration_values = np.zeros_like(t_values)
    forces_values = np.zeros_like(t_values)

    v, x = v0, 0
    for i, t in enumerate(t_values):
        v_values[i], x_values[i] = v, x

        k1_v, g1, a1, Ft1 = braking_force(v, wnn, m, Gamma, Delta, Xm, Ym, dh1, dh2, dm, N, mu, Bz)
        k1_v, k1_x = (k1_v / m) * dt, v * dt

        k2_v, g2, a2, Ft2 = braking_force(v + 0.5 * k1_v, wnn, m, Gamma, Delta, Xm, Ym, dh1, dh2, dm, N, mu, Bz)
        k2_v, k2_x = (k2_v / m) * dt, (v + 0.5 * k1_v) * dt

        k3_v, g3, a3, Ft3 = braking_force(v + 0.5 * k2_v, wnn, m, Gamma, Delta, Xm, Ym, dh1, dh2, dm, N, mu, Bz)
        k3_v, k3_x = (k3_v / m) * dt, (v + 0.5 * k2_v) * dt

        k4_v, g4, a4, Ft4 = braking_force(v + k3_v, wnn, m, Gamma, Delta, Xm, Ym, dh1, dh2, dm, N, mu, Bz)
        k4_v, k4_x = (k4_v / m) * dt, (v + k3_v) * dt

        v += (k1_v + 2 * k2_v + 2 * k3_v + k4_v) / 6
        x += (k1_x + 2 * k2_x + 2 * k3_x + k4_x) / 6
        overload_values[i] = (g1 + 2 * g2 + 2 * g3 + g4) / 6
        acceleration_values[i] = (a1 + 2 * a2 + 2 * a3 + a4) / 6
        forces_values[i] = (Ft1 + 2 * Ft2 + 2 * Ft3 + Ft4) / 6

    return t_values, x_values, v_values, overload_values, acceleration_values, forces_values


def runge_kutta_step(v, x, dt, m, Gamma, Delta, Xm, Ym, dh1, dh2, dm, N, mu, Bz, wnn=1):
    k1_v, g1, a1, Ft1 = braking_force(v, wnn, m, Gamma, Delta, Xm, Ym, dh1, dh2, dm, N, mu, Bz)
    k1_v, k1_x = (k1_v / m) * dt, v * dt

    k2_v, g2, a2, Ft2 = braking_force(v + 0.5 * k1_v, wnn, m, Gamma, Delta, Xm, Ym, dh1, dh2, dm, N, mu, Bz)
    k2_v, k2_x = (k2_v / m) * dt, (v + 0.5 * k1_v) * dt

    k3_v, g3, a3, Ft3 = braking_force(v + 0.5 * k2_v, wnn, m, Gamma, Delta, Xm, Ym, dh1, dh2, dm, N, mu, Bz)
    k3_v, k3_x = (k3_v / m) * dt, (v + 0.5 * k2_v) * dt

    k4_v, g4, a4, Ft4 = braking_force(v + k3_v, wnn, m, Gamma, Delta, Xm, Ym, dh1, dh2, dm, N, mu, Bz)
    k4_v, k4_x = (k4_v / m) * dt, (v + k3_v) * dt

    v_new = v + (k1_v + 2 * k2_v + 2 * k3_v + k4_v) / 6
    x_new = x + (k1_x + 2 * k2_x + 2 * k3_x + k4_x) / 6

    overload = (g1 + 2 * g2 + 2 * g3 + g4) / 6
    acceleration = (a1 + 2 * a2 + 2 * a3 + a4) / 6
    force_val = (Ft1 + 2 * Ft2 + 2 * Ft3 + Ft4) / 6

    return v_new, x_new, overload, acceleration, force_val


def validate_points(points):
    if len(points) < 2:
        return "Минимум 2 точки"
    for p in points:
        if not isinstance(p.get('v'), (int, float)) or not isinstance(p.get('f'), (int, float)):
            return "Нечисловые значения"
        if p['v'] < 0:
            return "Скорость не может быть отрицательной"
    return None


def sort_points(points):
    return sorted(points, key=lambda p: p['v'])


def build_linear_interpolator(points):
    points_sorted = sort_points(points)

    def interpolate(v):
        if v <= points_sorted[0]['v']:
            return points_sorted[0]['f']
        if v >= points_sorted[-1]['v']:
            return points_sorted[-1]['f']

        for i in range(len(points_sorted) - 1):
            if points_sorted[i]['v'] <= v <= points_sorted[i + 1]['v']:
                dv = points_sorted[i + 1]['v'] - points_sorted[i]['v']
                df = points_sorted[i + 1]['f'] - points_sorted[i]['f']
                return points_sorted[i]['f'] + (v - points_sorted[i]['v']) * df / dv
        return points_sorted[0]['f']

    return interpolate


def rk4_generic(v0, t_max, dt, m, F):
    steps = int(t_max / dt) + 1
    t = np.zeros(steps)
    v = np.zeros(steps)
    x = np.zeros(steps)

    t[0] = 0
    v[0] = v0
    x[0] = 0

    for i in range(steps - 1):
        if v[i] <= 0:
            v[i + 1:] = 0
            x[i + 1:] = x[i]
            t[i + 1:] = t[i] + dt * np.arange(1, steps - i)
            break

        vi = v[i]

        k1v = -F(vi) / m
        k1x = vi

        k2v = -F(vi + 0.5 * dt * k1v) / m
        k2x = vi + 0.5 * dt * k1v

        k3v = -F(vi + 0.5 * dt * k2v) / m
        k3x = vi + 0.5 * dt * k2v

        k4v = -F(vi + dt * k3v) / m
        k4x = vi + dt * k3v

        v[i + 1] = vi + (dt / 6) * (k1v + 2 * k2v + 2 * k3v + k4v)
        x[i + 1] = x[i] + (dt / 6) * (k1x + 2 * k2x + 2 * k3x + k4x)
        t[i + 1] = t[i] + dt

        if v[i + 1] < 0:
            v[i + 1] = 0

    stop_idx = np.where(v <= 0)[0]
    if len(stop_idx) > 0:
        stop_time = float(t[stop_idx[0]])
        stop_distance = float(x[stop_idx[0]])
    else:
        stop_time = float(t[-1])
        stop_distance = float(x[-1])

    overload = [0]
    g = 9.8
    for i in range(1, len(v)):
        dtt = t[i] - t[i - 1]
        dv = abs(v[i] - v[i - 1])
        overload.append(dv / (dtt * g) if dtt != 0 else 0)

    return {
        't': t.tolist(),
        'v': v.tolist(),
        'x': x.tolist(),
        'stop_time': stop_time,
        'stop_distance': stop_distance,
        'overload': overload,
    }


def calculate_from_points(points, mass, v0, dt, t_max, force_unit='kgf'):
    err = validate_points(points)
    if err:
        return {'success': False, 'error': err}

    points_copy = [p.copy() for p in points]
    F = build_linear_interpolator(points_copy)
    result = rk4_generic(v0, t_max, dt, mass, F)

    force_curve = {
        'labels': [p['v'] for p in sort_points(points_copy)],
        'data': [p['f'] for p in sort_points(points_copy)],
    }

    motion_curve = {
        'time': result['t'],
        'distance': result['x'],
        'speed': result['v'],
        'overload': result['overload'],
    }

    return {
        'success': True,
        'data': result,
        'force_curve': force_curve,
        'motion_curve': motion_curve,
    }


def parse_csv_flexible(text):
    import csv
    from io import StringIO

    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if not lines:
        return []

    first = lines[0]
    if ';' in first:
        delimiter = ';'
    elif '\t' in first:
        delimiter = '\t'
    else:
        delimiter = ','

    def to_number(s):
        if not s:
            return None
        s = s.strip().strip('"')
        s = s.replace(' ', '')
        if ',' in s and '.' not in s:
            s = s.replace(',', '.')
        try:
            return float(s)
        except ValueError:
            return None

    reader = csv.reader(StringIO(text), delimiter=delimiter)
    rows = list(reader)

    start_idx = 0
    if len(rows[0]) >= 2:
        if to_number(rows[0][0]) is None or to_number(rows[0][1]) is None:
            start_idx = 1

    points = []
    for row in rows[start_idx:]:
        if len(row) < 2:
            continue
        v = to_number(row[0])
        f = to_number(row[1])
        if v is not None and f is not None:
            points.append({'v': v, 'f': f})

    return points


# =========================
# СТРАНИЦЫ РАСЧЁТОВ
# =========================

def brake_view(request):
    if request.method == 'POST':
        form = BrakingForm(request.POST)
        if form.is_valid():
            m = form.cleaned_data['mass']
            v0 = form.cleaned_data['initial_speed']
            t_max = form.cleaned_data['time_max']
            dt = form.cleaned_data['dt']
            Gamma = float(form.cleaned_data['gamma'])
            Delta = form.cleaned_data['delta']
            Xm = form.cleaned_data['xm']
            Ym = form.cleaned_data['ym']
            dh1 = form.cleaned_data['dh1']
            dh2 = form.cleaned_data['dh2']
            dm = form.cleaned_data['dm']
            N = form.cleaned_data['n']
            mu = form.cleaned_data['mu']
            Bz = form.cleaned_data['bz']
            
            # Получаем название расчета
            calc_title = request.POST.get('calc_title', '').strip()

            t_values, x_values, v_values, overload_values, acceleration_values, forces_values = runge_kutta(
                v0, t_max, dt, m, Gamma, Delta, Xm, Ym, dh1, dh2, dm, N, mu, Bz
            )

            force_data = {
                'labels': v_values.tolist(),
                'data': forces_values.tolist(),
            }
            motion_data = {
                'time': t_values.tolist(),
                'distance': x_values.tolist(),
                'speed': v_values.tolist(),
                'overload': overload_values.tolist(),
            }

            record = save_history(
                source_page='brake_view',
                title=calc_title,
                source_data={
                    'mass': m,
                    'initial_speed': v0,
                    'time_max': t_max,
                    'dt': dt,
                    'gamma': Gamma,
                    'delta': Delta,
                    'xm': Xm,
                    'ym': Ym,
                    'dh1': dh1,
                    'dh2': dh2,
                    'dm': dm,
                    'n': N,
                    'mu': mu,
                    'bz': Bz,
                },
                force_data=force_data,
                motion_data=motion_data,
            )

            context = {
                'form': form,
                'force_data': json.dumps(force_data),
                'motion_data': json.dumps(motion_data),
                'history_id': record.id,
            }
            return render(request, 'brake/brake_form.html', context)
    else:
        form = BrakingForm()

    return render(request, 'brake/brake_form.html', {'form': form})


def brake_form2(request):
    if request.method == "POST":
        data = json.loads(request.body)

        v = float(data.get("v") or 10)
        x = float(data.get("x") or 0)
        dt = float(data.get("dt") or 0.01)
        m = float(data.get("mass") or 1000)
        Gamma = float(data.get("gamma") or 1.0)
        Delta = float(data.get("delta") or 0.1)
        Xm = float(data.get("xm") or 0.2)
        Ym = float(data.get("ym") or 0.1)
        dh1 = float(data.get("dh1") or 0.006)
        dh2 = float(data.get("dh2") or 0.006)
        dm = float(data.get("dm") or 0.05)
        N = int(data.get("n") or 10)
        mu = float(data.get("mu") or 1.5)
        Bz = float(data.get("bz") or 0.2)
        
        # Получаем название расчета
        calc_title = data.get('calc_title', '').strip()

        v_new, x_new, overload, acceleration, force_val = runge_kutta_step(
            v, x, dt, m, Gamma, Delta, Xm, Ym, dh1, dh2, dm, N, mu, Bz
        )

        if v_new is not None and x_new is not None and force_val is not None:
            force_data = {
                'labels': [v, v_new],
                'data': [force_val, force_val],
            }
            motion_data = {
                'time': [0, dt],
                'distance': [x, x_new],
                'speed': [v, v_new],
                'overload': [overload, overload],
            }

            record = save_history(
                source_page='brake_form2',
                title=calc_title,
                source_data={
                    'v': v,
                    'x': x,
                    'dt': dt,
                    'mass': m,
                    'gamma': Gamma,
                    'delta': Delta,
                    'xm': Xm,
                    'ym': Ym,
                    'dh1': dh1,
                    'dh2': dh2,
                    'dm': dm,
                    'n': N,
                    'mu': mu,
                    'bz': Bz,
                },
                force_data=force_data,
                motion_data=motion_data,
            )

            return JsonResponse({
                "v": v_new,
                "x": x_new,
                "overload": overload,
                "acceleration": acceleration,
                "force": force_val,
                "history_id": record.id,
                "history_url": reverse("brake:history_detail", args=[record.id]),
            })

        return JsonResponse({"error": "Ошибка вычислений"}, status=400)

    form = BrakingForm()
    return render(request, "brake/brake_form2.html", {"form": form})


@csrf_exempt
def api_calculate_rk4(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        data = json.loads(request.body)

        points = data.get('points', [])
        mass = float(data.get('mass', 10000))
        v0 = float(data.get('v0', 30))
        dt = float(data.get('dt', 0.02))
        t_max = float(data.get('tMax', 30))
        force_unit = data.get('forceUnit', 'kgf')
        
        # Получаем название расчета
        calc_title = data.get('calc_title', '').strip()

        result = calculate_from_points(points, mass, v0, dt, t_max, force_unit)

        if result['success']:
            record = save_history(
                source_page='brake_form3',
                title=calc_title,
                source_data={
                    'points': points,
                    'mass': mass,
                    'v0': v0,
                    'dt': dt,
                    'tMax': t_max,
                    'forceUnit': force_unit,
                },
                force_data=result['force_curve'],
                motion_data=result['motion_curve'],
            )

            return JsonResponse({
                **result,
                "history_id": record.id,
                "history_url": reverse("brake:history_detail", args=[record.id]),
            })

        return JsonResponse(result, status=400)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
def api_upload_csv(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        data = json.loads(request.body)
        csv_text = data.get('csv', '')
        points = parse_csv_flexible(csv_text)

        if len(points) >= 2:
            return JsonResponse({
                'success': True,
                'points': points
            })

        return JsonResponse({
            'success': False,
            'error': 'Не удалось распознать точки. Нужно минимум 2 точки'
        }, status=400)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def brake_form3(request):
    return render(request, 'brake/brake_form3.html')


# =========================
# ИСТОРИЯ
# =========================

def history_page(request):
    records = CalculationHistory.objects.all()
    return render(request, 'brake/history_page.html', {'records': records})


def history_detail(request, pk):
    record = get_object_or_404(CalculationHistory, pk=pk)

    force_data = json.loads(record.force_data) if record.force_data else None
    motion_data = json.loads(record.motion_data) if record.motion_data else None
    source_data = json.loads(record.source_data) if record.source_data else None

    return render(request, 'brake/history_detail.html', {
        'record': record,
        'force_data': json.dumps(force_data, ensure_ascii=False) if force_data else 'null',
        'motion_data': json.dumps(motion_data, ensure_ascii=False) if motion_data else 'null',
        'source_data': source_data,
    })



# Добавьте в конец файла views.py, перед импортами убедитесь, что есть:
from django.views.decorators.http import require_http_methods

@csrf_exempt
@require_http_methods(["DELETE"])
def api_delete_history(request, pk):
    """Удаление одной записи из истории"""
    try:
        record = get_object_or_404(CalculationHistory, pk=pk)
        record_id = record.id
        record_title = record.title or f"Запись #{record_id}"
        record.delete()
        return JsonResponse({
            'success': True, 
            'message': f'Запись "{record_title}" удалена'
        })
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def api_delete_all_history(request):
    """Удаление всех записей из истории"""
    try:
        count, _ = CalculationHistory.objects.all().delete()
        return JsonResponse({
            'success': True, 
            'message': f'Удалено {count} записей'
        })
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': str(e)
        }, status=500)