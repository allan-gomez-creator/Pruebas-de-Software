from django import forms

from .models import Tarea

MSG_OBLIGATORIO = 'Este campo es obligatorio.'


class TareaForm(forms.ModelForm):
    """Formulario para crear una tarea (HU-03)."""

    class Meta:
        model = Tarea
        fields = ['nombre', 'descripcion', 'fecha_inicio', 'fecha_fin', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej. Entregar informe'}),
            'descripcion': forms.Textarea(attrs={'rows': 4}),
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }
        error_messages = {
            'nombre': {'required': 'El nombre es obligatorio.'},
            'fecha_inicio': {'required': 'La fecha de inicio es obligatoria.',
                             'invalid': 'Ingresa una fecha de inicio válida.'},
            'fecha_fin': {'required': 'La fecha de fin es obligatoria.',
                          'invalid': 'Ingresa una fecha de fin válida.'},
            'estado': {'required': 'Selecciona un estado.',
                       'invalid_choice': 'Estado no permitido: elige Pendiente, En progreso o Completada.'},
        }

    def clean(self):
        cleaned = super().clean()
        inicio = cleaned.get('fecha_inicio')
        fin = cleaned.get('fecha_fin')
        if inicio and fin and fin < inicio:
            self.add_error('fecha_fin', 'La fecha de fin no puede ser anterior a la fecha de inicio.')
        return cleaned