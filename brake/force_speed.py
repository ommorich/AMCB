import math
import numpy as np


def force(V: float, wn: int, Gamma: int, Delta: float, Xm: float, 
          Ym: float, dh1: float, dh2: float, dm: float, N: int, 
          mu: int, Bz: float, lya=2.5):
    """
    Функция расчета силы торможения от скорости в вихретоковой магнитной системе

    :param v: скорость, при которой расcчитывается сила
    :param wn: относительная величина магнитной индукции в начальный момент времени
    :param Gamma: удельная проводимость
    :param Xm: ширина магнита
    :param Ym: длинна магнита
    :param dh1: выступ шины 1-ого края
    :param dh2: выступ шины 2-ого края
    :param dm: расстояние между магнитами
    :param N: количество блоков в системе
    :param mu: магнитная приницаемость шины
    :param Bz: средняя индукция в зазоре
    :param lya: коэфициент для расчета времени релаксации поля всегда равен 2.5
    :return Ft, wnn:  силу торможения и обновленное значение относительной величины магнитной индукции в момент времени
    """
    
    dH1 = 1 if dh1 > 0 else -1 if dh1 < 0 else 0
    dH2 = 1 if dh2 > 0 else -1 if dh2 < 0 else 0

    #Размер активной области по оси Y
    H = Ym + (dh1*((1-dH1)/2)) + (dh2*((1-dH2)/2))
    A1 = H/2 + (dh1*((1+dH1))/2)
    A2 = H/2 + (dh2*((1+dH2))/2)

    Ya1 = A1 / 2 if A1 / 2 < H / 2 else H / 2
    Ya2 = A2 / 2 if A2 / 2 < H / 2 else H / 2

    #время жизни контура
    tj = Xm/(4*V)

    nu1 = (H+dh1*(1+dH1))/Xm
    nu2 = (H+dh2*(1+dH2))/Xm

    w1 = nu1 if nu1 - 1 > 0 else 1 / nu1 if nu1 - 1 != 0 else 1
    w2 = nu2 if nu2 - 1 > 0 else 1 / nu2 if nu2 - 1 != 0 else 1

    # сопротивления крайнего контура
    Rk = (((((w1-1 + math.pi/2)**2)/(4*w1-4+math.pi)) + (((w2-1 + math.pi/2)**2)/(4*w2-4+math.pi))) + math.pi/2) / (Gamma*Delta)

    Yh = dh1 + dh2 + Ym
    Yp = Yh/2

    l1 = Xm / 4 - (A1 / 2 * (1 - math.pi / 2)) if A1 / 2 < Xm / 4 else A1 / 2 - (Xm / 4 * (1 - math.pi / 2))
    l2 = Xm / 4 - (A2 / 2 * (1 - math.pi / 2)) if A2 / 2 < Xm / 4 else A2 / 2 - (Xm / 4 * (1 - math.pi / 2))

    # РАСЧЕТ КРАЕВОГО КОНТУРА
    # длинна средней линии краевого контура
    lcpk = l1 + l2 + math.pi*Yh/4

    # сечение рамки крайнего контура
    Rek = math.sqrt(lcpk/(Gamma*Rk))
    Xpk = (lcpk - Yh)/2

    # Индуктивности краевого контура
    Lbhxk = 2 * 10 ** -7 * Xpk * (math.asinh(Xpk / Rek) + Rek / Xpk - math.sqrt((Rek / Xpk) ** 2 + 1))
    Lbhyk = 2 * 10 ** -7 * Yp * (math.asinh(Yp / Rek) + Rek / Yp - math.sqrt((Rek / Yp) ** 2 + 1))
    Lbtxk = 0.5 * 10 ** -7 * mu * Xpk
    Lbtyk = 0.5 * 10 ** -7 * mu * Yp
    Mxxk = 2 * 10 ** -7 * Xpk * (math.asinh(Xpk / Yp) + Yp / Xpk - math.sqrt((Yp / Xpk) ** 2 + 1))
    Myyk = 2 * 10 ** -7 * Yp * (math.asinh(Yp / Xpk) + Xpk / Yp - math.sqrt((Xpk / Yp) ** 2 + 1))

    # Индуктивность и постоянная времени краевого контура
    Lk = 2 * (Lbhxk + Lbhyk + Lbtxk + Lbtyk - Mxxk - Myyk)
    tk = Lk / Rk if Rk != 0 else 0

    # коэффициент полноты развития токов крайнего контура
    Tettak = 1 + tk/tj * (math.exp((-tj/tk))-1)

    # РАСЧЕТ ЦЕНТРАЛЬНОГО КОНТУРА
    # сопротивления центрального контура
    Rc = 2 * (((((w1-1 + math.pi/2)**2)/(4*w1-4+math.pi)) + (((w2-1 + math.pi/2)**2)/(4*w2-4+math.pi))) + (dm*(1/A1 + 1/A2))/2) / (Gamma*Delta)

    # длинна средней линии центрального контура
    lcpc = 2*(l1 + l2 +dm)

    # сечение рамки центрального контура
    Rec = math.sqrt(lcpc/(Gamma*Rc))
    Xpc = (lcpc - Yh)/2

    # Индуктивности центрального контура
    Lbhxc = 2 * 10**(-7) * Xpc * (math.asinh(Xpc/Rec) + Rec/Xpc - math.sqrt((Rec/Xpc)**2 + 1))
    Lbhyc = 2 * 10**(-7) * Yp * (math.asinh(Yp/Rec) + Rec/Yp - math.sqrt((Rec/Yp)**2 + 1))
    Lbtxc = 0.5 * 10**(-7) * mu * Xpc
    Lbtyc = 0.5 * 10**(-7) * mu * Yp
    Mxxc = 2 * 10**(-7) * Xpc * (math.asinh(Xpc/Yp) + Yp/Xpc - math.sqrt((Yp/Xpc)**2 + 1))
    Myyc = 2 * 10**(-7) * Yp * (math.asinh(Yp/Xpc) + Xpc/Yp - math.sqrt((Xpc/Yp)**2 + 1))

    # индуктивность и постоянная времени центрального контура
    Lc = 2*(Lbhxc + Lbhyc + Lbtxc + Lbtyc - Mxxc - Myyc)
    tc = Lc/Rc

    # коэффициент полноты развития токов центрального контура
    Tettac = 1 + tc/tj * (math.exp((-tj/tc))-1)

    # РАСЧЕТ КОЭФФИЦИЕНТА kb
    tp = (Delta/math.pi)**2*Gamma*4*math.pi*10**(-7)*mu*lya
    Ex = (8/math.pi**2)*math.exp(-Xm/(V*tp))
    Ed = (8/math.pi**2)*math.exp(-dm/(V*tp))
    wnn = Ed**2*Ex*(wn*Ex+1-Ex) + Ed*(Ex-1)

    kb = 1 + (V*tp/(2*Xm))*(8/math.pi**2-Ex)*(wnn*(1-Ex*Ed)-2+Ed*(Ex-1))
    
    # сила торможения в ньютонах
    Ft = Bz**2 * (Ya1+Ya2)**2 * V * (2 * Tettak/Rk + 4*(2*N-1)*Tettac/Rc)* kb**2

    # сила торможения в кгс
    Ft /= 9.8

    return Ft, wnn





