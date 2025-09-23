from django import forms
from .models import Paciente, Sessao, AtividadeModelo, AtividadeSessao

class SelecionarAtividadeForm(forms.ModelForm):
    class Meta:
        model = AtividadeSessao
        fields = ['atividade_modelo']
        labels = {'atividade_modelo': 'Atividade'}

class DetalheAtividadeSessaoForm(forms.ModelForm):
    class Meta:
        model = AtividadeSessao
        fields = ['detalhes', 'resposta']
        labels = {
            'detalhes': 'Detalhes da Atividade',
            'resposta': 'Resposta',
        }

# =========================
# Pacientes e Sessões
# =========================
class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ['nome', 'data_nascimento']

# =========================
# Atividades Modelo
# =========================
class AtividadeModeloForm(forms.ModelForm):
    class Meta:
        model = AtividadeModelo
        fields = ['descricao']  # O positivo/negativo é decidido na sessão


# =========================
# Atividades da Sessão
# =========================
class AtividadeSessaoForm(forms.ModelForm):
    class Meta:
        model = AtividadeSessao
        fields = ['atividade_modelo', 'resposta']  # mantém só o que o usuário deve escolher

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # carrega apenas atividades modelo
        self.fields['atividade_modelo'].queryset = AtividadeModelo.objects.all()
        self.fields['atividade_modelo'].label = "Selecione a atividade"
        self.fields['resposta'].label = "Resposta (P/N)"