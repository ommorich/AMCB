from django.db import models


class CalculationHistory(models.Model):
    PAGE_CHOICES = [
        ('brake_view', 'Непрерывное интегрирование'),
        ('brake_form2', 'Пошаговое интегрирование'),
        ('brake_form3', 'Импорт из файла'),
    ]

    created_at = models.DateTimeField(auto_now_add=True)
    source_page = models.CharField(max_length=50, choices=PAGE_CHOICES)
    title = models.CharField(max_length=255, blank=True)

    source_data = models.TextField()
    force_data = models.TextField(blank=True)
    motion_data = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'История расчёта'
        verbose_name_plural = 'История расчётов'

    def __str__(self):
        return f'#{self.id} {self.source_page} {self.created_at:%d.%m.%Y %H:%M:%S}'