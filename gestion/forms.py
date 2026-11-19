from django import forms
from django.core.exceptions import ValidationError
from .models import Permiso, Asistencia, Correccion

class HtmlDateInput(forms.DateInput):
    input_type = 'date'

class HtmlDateTimeInput(forms.DateTimeInput):
    input_type = 'datetime-local'

class PermisoForm(forms.ModelForm):
    class Meta:
        model = Permiso
        fields = ['tipo', 'inicio', 'fin', 'motivo', 'documento']
        widgets = {'inicio': HtmlDateInput, 'fin': HtmlDateInput, 'motivo': forms.Textarea(attrs={'rows': 4}), 'documento': forms.TextInput(attrs={'placeholder': 'Descripción del documento (opcional)'})}
    def __init__(self, *args, empleado=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.empleado = empleado
    def clean(self):
        data = super().clean()
        if self.empleado:
            item = Permiso(empleado=self.empleado, **{key: data[key] for key in self.Meta.fields if key in data})
            try: item.full_clean()
            except ValidationError as exc:
                for field, errors in exc.error_dict.items():
                    for err in errors:
                        self.add_error(field if field in self.fields else None, err)
        return data

class CorreccionForm(forms.Form):
    motivo = forms.ChoiceField(choices=Correccion.MOTIVOS)
    justificacion = forms.CharField(min_length=50, widget=forms.Textarea(attrs={'rows': 4}))
    entrada = forms.SplitDateTimeField(widget=forms.SplitDateTimeWidget(date_attrs={'type': 'date'}, time_attrs={'type': 'time'}))
    salida = forms.SplitDateTimeField(required=False, widget=forms.SplitDateTimeWidget(date_attrs={'type': 'date'}, time_attrs={'type': 'time'}))
    def clean(self):
        data = super().clean()
        if data.get('entrada') and data.get('salida') and data['salida'] <= data['entrada']:
            raise forms.ValidationError('La salida debe ser posterior a la entrada.')
        return data
