from django import forms
from django.contrib.auth.forms import AuthenticationForm


class CustomAuthForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'username-field',
            'placeholder': 'Имя пользователя',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'password-field',
            'placeholder': 'Пароль',
        })
    )


class BrakingForm(forms.Form):
    mass = forms.FloatField(label='Масса (кг)', min_value=0)
    initial_speed = forms.FloatField(label='Начальная скорость (м/с)', min_value=0)
    time_max = forms.FloatField(label='Максимальное время (с)', min_value=0, initial=1)
    dt = forms.FloatField(label='Шаг времени (с)', min_value=0, initial=0.001)

    gamma = forms.FloatField(label='Gamma (удельная проводимость)', min_value=0)
    delta = forms.FloatField(label='Delta (толщина шины)', min_value=0)
    xm = forms.FloatField(label='Xm (размер магнита по оси X)', min_value=0)
    ym = forms.FloatField(label='Ym (размер магнита по оси Y)', min_value=0)
    dh1 = forms.FloatField(label='dh1 (выступ шины 1-ого края)', min_value=0, initial=0.006)
    dh2 = forms.FloatField(label='dh2 (выступ шины 2-ого края)', min_value=0, initial=0.006)
    dm = forms.FloatField(label='dm (расстояние между магнитами)', min_value=0)
    n = forms.IntegerField(label='N (количество блоков в системе)', min_value=0, initial=10)
    mu = forms.FloatField(label='Mu (магнитная проницаемость шины)', min_value=0, initial=1)
    bz = forms.FloatField(label='Bz (индукция в рабочем зазоре)', min_value=0)