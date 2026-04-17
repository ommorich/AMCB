from django.db import models

class CalculationHistory(models.Model):
    SOURCE_CHOICES = [
        ('brake_view', 'Непрерывное интегрирование'),
        ('brake_form2', 'Пошаговое интегрирование'),
        ('brake_form3', 'Импорт из файла'),
    ]
    
    source_page = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    title = models.CharField(max_length=255, default="", blank=True)
    source_data = models.TextField()
    force_data = models.TextField(blank=True)
    motion_data = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title or self.get_source_page_display()} - {self.created_at.strftime('%d.%m.%Y %H:%M')}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'История расчета'
        verbose_name_plural = 'История расчетов'