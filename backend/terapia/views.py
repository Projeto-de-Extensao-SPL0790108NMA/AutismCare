import os
from pathlib import Path
import csv

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils.text import slugify
from django.db.models import Count, Max
from django.db.models.functions import TruncMonth, TruncDate
from .models import Paciente

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .forms import PacienteForm, AtividadeSessaoForm, AtividadeModeloForm, SelecionarAtividadeForm, DetalheAtividadeSessaoForm
from .models import Paciente, Sessao, AtividadeModelo, AtividadeSessao
from .serializers import (
    PacienteSerializer,
    SessaoSerializer,
    AtividadeModeloSerializer,
    AtividadeSessaoSerializer,
)

# =========================
# Páginas do Terapeuta
# =========================


@login_required
def dashboard(request):
    """Mostra sessões ativas do terapeuta."""
    sessoes_ativas = (
        Sessao.objects.filter(terapeuta=request.user, encerrada=False)
        .select_related("paciente")
        .order_by("-data_inicio")
    )
    return render(request, "terapia/dashboard.html", {"sessoes_ativas": sessoes_ativas})


@login_required
def lista_pacientes(request):
    pacientes = (
        Paciente.objects
        .filter(terapeuta=request.user)
        .annotate(
            sessoes_count=Count("sessao"),
            ultima_sessao=Max("sessao__data_inicio")
        )
        .order_by("nome")
    )
    return render(request, "terapia/lista_pacientes.html", {"pacientes": pacientes})

@login_required
def adicionar_paciente(request):
    if request.method == "POST":
        form = PacienteForm(request.POST)
        if form.is_valid():
            paciente = form.save(commit=False)
            paciente.terapeuta = request.user
            paciente.save()
            messages.success(request, "Paciente adicionado com sucesso.")
            return redirect("lista_pacientes")
        else:
            messages.error(request, "Formulário inválido. Verifique os campos.")
    else:
        form = PacienteForm()

    return render(request, "terapia/form_paciente.html", {"form": form})

@login_required
def editar_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id, terapeuta=request.user)
    if request.method == "POST":
        form = PacienteForm(request.POST, instance=paciente)
        if form.is_valid():
            form.save()
            messages.success(request, "Paciente atualizado com sucesso.")
            return redirect("lista_pacientes")
        else:
            messages.error(request, "Erro ao atualizar paciente.")
    else:
        form = PacienteForm(instance=paciente)
    return render(request, "terapia/form_paciente.html", {"form": form})

@login_required
def excluir_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id, terapeuta=request.user)
    paciente.delete()
    messages.success(request, "Paciente excluído com sucesso.")
    return redirect("lista_pacientes")
    

@login_required
def adicionar_atividade(request):
    if request.method == "POST":
        form = AtividadeModeloForm(request.POST)
        if form.is_valid():
            atividade = form.save(commit=False)
            atividade.terapeuta = request.user
            atividade.save()
            messages.success(request, "Atividade adicionada com sucesso.")
            return redirect("lista_atividades")
        messages.error(request, "Erro ao salvar atividade.")
    else:
        form = AtividadeModeloForm()
    return render(request, "terapia/form_atividade.html", {"form": form})

@login_required
def editar_atividade(request, atividade_id):
    atividade = get_object_or_404(AtividadeModelo, id=atividade_id, terapeuta=request.user)
    if request.method == "POST":
        form = AtividadeModeloForm(request.POST, instance=atividade)
        if form.is_valid():
            form.save()
            messages.success(request, "Atividade atualizada com sucesso.")
            return redirect("lista_atividades")
        else:
            messages.error(request, "Erro ao atualizar atividade.")
    else:
        form = AtividadeModeloForm(instance=atividade)
    return render(request, "terapia/form_atividade.html", {"form": form})

@login_required
def excluir_atividade(request, atividade_id):
    atividade = get_object_or_404(AtividadeModelo, id=atividade_id, terapeuta=request.user)
    atividade.delete()
    messages.success(request, "Atividade excluída com sucesso.")
    return redirect("lista_atividades")

@login_required
def adicionar_atividade_sessao(request, sessao_id):
    sessao = get_object_or_404(Sessao, id=sessao_id)
    atividade_id = request.GET.get('atividade_id')

    if atividade_id:
        atividade_modelo = get_object_or_404(AtividadeModelo, id=atividade_id)
        if request.method == 'POST':
            form = DetalheAtividadeSessaoForm(request.POST)
            if form.is_valid():
                atividade_sessao = form.save(commit=False)
                atividade_sessao.sessao = sessao
                atividade_sessao.atividade_modelo = atividade_modelo
                atividade_sessao.save()
                return redirect('detalhes_sessao', sessao_id=sessao.id)
        else:
            form = DetalheAtividadeSessaoForm()
        return render(request, 'adicionar_atividade_sessao.html', {
            'sessao': sessao,
            'atividade_modelo': atividade_modelo,
            'form': form,
        })

@login_required
def historico_sessoes(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id, terapeuta=request.user)
    sessoes = Sessao.objects.filter(paciente=paciente).order_by("-data_inicio")
    return render(
        request,
        "terapia/historico_sessoes.html",
        {"paciente": paciente, "sessoes": sessoes},
    )


# -------------------------
# EXPORTAÇÃO
# -------------------------


# =========================
# Sessões e Atividades
# =========================


@login_required
def iniciar_sessao(request, paciente_id):
    """
    Corrigido: não cria sessão no GET.
    GET: mostra lista de AtividadeModelo para o terapeuta escolher.
    POST: cria a sessão e vincula as atividades selecionadas.
    """
    paciente = get_object_or_404(Paciente, id=paciente_id, terapeuta=request.user)

    # se já houver sessão aberta, manda pra registrar
    sessao_ativa = Sessao.objects.filter(
        paciente=paciente, terapeuta=request.user, encerrada=False
    ).first()
    if sessao_ativa:
        messages.warning(request, "Já existe uma sessão ativa para este paciente.")
        return redirect("registrar_atividades_sessao", sessao_id=sessao_ativa.id)

    atividades_modelo = AtividadeModelo.objects.filter(
        terapeuta=request.user
    ).order_by("descricao")

    if request.method == "POST":
        ids = request.POST.getlist("atividades")  # checkboxes name="atividades"
        if not ids:
            messages.info(request, "Selecione ao menos uma atividade.")
            return render(
                request,
                "terapia/selecionar_atividades_sessao.html",
                {"paciente": paciente, "atividades_modelo": atividades_modelo},
            )

        # cria a sessão aqui (somente no POST)
        sessao = Sessao.objects.create(paciente=paciente, terapeuta=request.user, encerrada=False)

        # vincula cada atividade selecionada
        for atividade_id in ids:
            atividade_modelo = get_object_or_404(
                AtividadeModelo, id=atividade_id, terapeuta=request.user
            )
            AtividadeSessao.objects.create(sessao=sessao, atividade_modelo=atividade_modelo)

        messages.success(request, "Sessão iniciada com atividades selecionadas.")
        return redirect("registrar_atividades_sessao", sessao_id=sessao.id)

    # GET: só exibe as opções
    return render(
        request,
        "terapia/selecionar_atividades_sessao.html",
        {"paciente": paciente, "atividades_modelo": atividades_modelo},
    )

# DETALHES DA SESSÃO + ATIVIDADES
@login_required
def detalhes_sessao(request, sessao_id):
    sessao = get_object_or_404(Sessao, id=sessao_id)
    atividades_sessao = AtividadeSessao.objects.filter(sessao=sessao)

    return render(request, 'detalhes_sessao.html', {
        'sessao': sessao,
        'atividades_sessao': atividades_sessao,
    })

@login_required
def registrar_atividades_sessao(request, sessao_id):
    """
    Mostra atividades já vinculadas na sessão e permite adicionar MAIS,
    exibindo apenas as que ainda não foram adicionadas.
    """
    sessao = get_object_or_404(Sessao, id=sessao_id, terapeuta=request.user)

    if sessao.encerrada:
        messages.warning(request, "Sessão já encerrada.")
        return redirect("dashboard")

    # já na sessão
    atividades_sessao = AtividadeSessao.objects.filter(sessao=sessao).select_related("atividade_modelo").order_by("-data_registro")
    ids_ja_vinculados = list(atividades_sessao.values_list("atividade_modelo_id", flat=True))

    # disponíveis p/ adicionar (exclui as que já estão)
    atividades_disponiveis = AtividadeModelo.objects.filter(
        terapeuta=request.user
    ).exclude(id__in=ids_ja_vinculados).order_by("descricao")

    if request.method == "POST":
        ids = request.POST.getlist("atividades")
        if not ids:
            messages.info(request, "Selecione ao menos uma atividade.")
            return redirect("registrar_atividades_sessao", sessao_id=sessao.id)

        for atividade_id in ids:
            atividade_modelo = get_object_or_404(
                AtividadeModelo, id=atividade_id, terapeuta=request.user
            )
            AtividadeSessao.objects.get_or_create(
                sessao=sessao, atividade_modelo=atividade_modelo
            )

        messages.success(request, "Atividades adicionadas à sessão.")
        return redirect("registrar_atividades_sessao", sessao_id=sessao.id)

    return render(
        request,
        "terapia/registrar_atividade.html",
        {
            "sessao": sessao,
            "atividades_sessao": atividades_sessao,
            "atividades_disponiveis": atividades_disponiveis,  # <== use isto no template
        },
    )

@login_required
def registrar_detalhes_atividade(request, atividade_sessao_id):
    atividade_sessao = get_object_or_404(
        AtividadeSessao, id=atividade_sessao_id, sessao__terapeuta=request.user
    )

    if request.method == "POST":
        form = DetalheAtividadeSessaoForm(request.POST, instance=atividade_sessao)
        if form.is_valid():
            form.save()
            messages.success(request, "Detalhes da atividade atualizados.")
            if request.headers.get("HX-Request"):
                atividades = AtividadeSessao.objects.filter(
                    sessao=atividade_sessao.sessao
                ).order_by("-data_registro")
                return render(
                    request,
                    "terapia/_lista_atividades.html",
                    {"atividades": atividades},
                )
            return redirect("registrar_atividades_sessao", sessao_id=atividade_sessao.sessao.id)

    else:
        form = DetalheAtividadeSessaoForm(instance=atividade_sessao)

    return render(
        request,
        "terapia/form_detalhes_atividade.html",
        {"form": form, "atividade": atividade_sessao},
    )

@login_required
def encerrar_sessao(request, sessao_id):
    sessao = get_object_or_404(Sessao, id=sessao_id, terapeuta=request.user)

    if not sessao.encerrada:
        sessao.encerrada = True
        sessao.save()
        messages.success(request, "Sessão encerrada com sucesso.")
    else:
        messages.info(request, "Sessão já está encerrada.")

    if request.headers.get("HX-Request"):
        return render(request, "terapia/_status_sessao.html", {"sessao": sessao})

    atividades = AtividadeSessao.objects.filter(sessao=sessao).order_by("-data_registro")

    media_root = getattr(settings, "MEDIA_ROOT", os.path.join(os.getcwd(), "media"))
    reports_dir = os.path.join(media_root, "reports")
    Path(reports_dir).mkdir(parents=True, exist_ok=True)

    paciente_nome = sessao.paciente.nome if sessao.paciente else "paciente"
    safe_nome = slugify(f"sessao-{sessao.id}-{paciente_nome}")
    filename = f"{safe_nome}.html"
    filepath = os.path.join(reports_dir, filename)

    html_string = render_to_string(
        "terapia/relatorio_sessao.html",
        {"sessao": sessao, "atividades": atividades, "gerado_por": request.user},
    )
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_string)

    media_url = getattr(settings, "MEDIA_URL", "/media/")
    report_url = os.path.join(media_url, "reports", filename)

    return render(
        request,
        "terapia/dashboard.html",
        {"sessao": sessao, "atividades": atividades, "report_url": report_url},
    )

@login_required
def relatorio_sessao(request, sessao_id):
    sessao = get_object_or_404(Sessao, id=sessao_id, terapeuta=request.user)
    atividades = AtividadeSessao.objects.filter(sessao=sessao).order_by("-data_registro")
    return render(request, "terapia/relatorio_sessao.html", {"sessao": sessao, "atividades": atividades})

@login_required
def relatorio_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id, terapeuta=request.user)

    # Filtros de data via GET
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    atividades = AtividadeSessao.objects.filter(sessao__paciente=paciente)

    if data_inicio and data_fim:
        atividades = atividades.filter(data_registro__date__range=[data_inicio, data_fim])

    # Agrupar por atividade e resposta
    dados = (
        atividades.values("atividade_modelo__descricao", "resposta")
        .annotate(total=Count("id"))
        .order_by("atividade_modelo__descricao")
    )

    # Preparar para gráfico
    atividades_labels = sorted(set(d["atividade_modelo__descricao"] for d in dados))
    positivas = []
    negativas = []

    for atividade in atividades_labels:
        pos = next((d["total"] for d in dados if d["atividade_modelo__descricao"] == atividade and d["resposta"] == "positiva"), 0)
        neg = next((d["total"] for d in dados if d["atividade_modelo__descricao"] == atividade and d["resposta"] == "negativa"), 0)
        positivas.append(pos)
        negativas.append(neg)

    # Histórico detalhado (dia a dia)
    historico = (
        atividades.annotate(dia=TruncDate("data_registro"))
        .values("dia", "atividade_modelo__descricao", "resposta")
        .order_by("dia")
    )

    evolucao = (
        atividades.annotate(dia=TruncDate("data_registro"))
        .values("dia", "resposta")
        .annotate(total=Count("id"))
        .order_by("dia")
    )

    dias_labels = sorted(set([e["dia"].strftime("%d/%m/%Y") for e in evolucao]))
    positivos_dia = []
    negativos_dia = []

    for dia in dias_labels:
        pos = next((e["total"] for e in evolucao if e["dia"].strftime("%d/%m/%Y") == dia and e["resposta"] == "positiva"), 0)
        neg = next((e["total"] for e in evolucao if e["dia"].strftime("%d/%m/%Y") == dia and e["resposta"] == "negativa"), 0)
        positivos_dia.append(pos)
        negativos_dia.append(neg)

    context = {
        "paciente": paciente,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "atividades_labels": atividades_labels,
        "positivas": positivas,
        "negativas": negativas,
        "historico": historico,
        "dias_labels": dias_labels,
        "positivos_dia": positivos_dia,
        "negativos_dia": negativos_dia,
    }
    return render(request, "terapia/relatorio_paciente.html", context)

# =========================
# Atividades Modelo
# =========================

@login_required
def lista_atividades(request):
    atividades = AtividadeModelo.objects.filter(terapeuta=request.user)
    return render(request, "terapia/lista_atividades.html", {"atividades": atividades})

@login_required
def lista_atividades_modelo(request):
    atividades = AtividadeModelo.objects.filter(terapeuta=request.user).order_by(
        "descricao"
    )
    return render(
        request, "terapia/lista_atividades_modelo.html", {"atividades": atividades}
    )

@login_required
def editar_atividade_modelo(request, atividade_id):
    atividade = get_object_or_404(AtividadeModelo, id=atividade_id, terapeuta=request.user)
    if request.method == "POST":
        form = AtividadeModeloForm(request.POST, instance=atividade)
        if form.is_valid():
            form.save()
            messages.success(request, "Atividade atualizada com sucesso.")
            return redirect("lista_atividades")
        messages.error(request, "Erro ao atualizar atividade.")
    else:
        form = AtividadeModeloForm(instance=atividade)
    return render(request, "terapia/form_atividade.html", {"form": form})

@login_required
def criar_atividade_modelo(request):
    if request.method == "POST":
        form = AtividadeModeloForm(request.POST)
        if form.is_valid():
            atividade = form.save(commit=False)
            atividade.terapeuta = request.user
            atividade.save()
            messages.success(request, "Atividade modelo criada com sucesso.")
            return redirect("lista_atividades_modelo")
    else:
        form = AtividadeModeloForm()
    return render(request, "terapia/form_atividade_modelo.html", {"form": form})

@login_required
def excluir_atividade_modelo(request, atividade_id):
    atividade = get_object_or_404(AtividadeModelo, id=atividade_id, terapeuta=request.user)
    atividade.delete()
    messages.success(request, "Atividade excluída com sucesso.")
    return redirect("lista_atividades")

# =========================
# Autenticação
# =========================


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("dashboard")
        messages.error(request, "Usuário ou senha inválidos.")
    return render(request, "terapia/registration/login.html")

@login_required
def logout_view(request):
    logout(request)
    return redirect("login")

# =========================
# API REST Framework (ViewSets)
# =========================

@login_required
def exportar_sessoes_csv(request):
    sessoes = Sessao.objects.filter(terapeuta=request.user).select_related("paciente")
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="sessoes.csv"'
    writer = csv.writer(response)
    writer.writerow(["Paciente", "Data Início", "Encerrada"])
    for s in sessoes:
        writer.writerow([s.paciente.nome, s.data_inicio, s.encerrada])
    return response

@login_required
def exportar_atividades_csv(request, sessao_id):
    sessao = get_object_or_404(Sessao, id=sessao_id, terapeuta=request.user)
    registros = AtividadeSessao.objects.filter(sessao=sessao).select_related("atividade_modelo")
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="sessao_{sessao_id}_atividades.csv"'
    writer = csv.writer(response)
    writer.writerow(["Atividade", "Resposta", "Horário"])
    for r in registros:
        writer.writerow([r.atividade_modelo.descricao, r.resposta, r.tempo_registro])
    return response

@login_required
def editar_sessao(request, sessao_id):
    sessao = get_object_or_404(Sessao, id=sessao_id, terapeuta=request.user)
    if request.method == "POST":
        form = SessaoForm(request.POST, instance=sessao)
        if form.is_valid():
            form.save()
            messages.success(request, "Sessão editada com sucesso.")
            return redirect("lista_sessoes")
    else:
        form = SessaoForm(instance=sessao)
    return render(request, "app_aba/form_sessao.html", {"form": form})

class PacienteViewSet(viewsets.ModelViewSet):
    queryset = Paciente.objects.all()
    serializer_class = PacienteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(terapeuta=self.request.user)

    def perform_create(self, serializer):
        serializer.save(terapeuta=self.request.user)

class SessaoViewSet(viewsets.ModelViewSet):
    queryset = Sessao.objects.all()
    serializer_class = SessaoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(terapeuta=self.request.user)

    def perform_create(self, serializer):
        serializer.save(terapeuta=self.request.user)

class AtividadeModeloViewSet(viewsets.ModelViewSet):
    queryset = AtividadeModelo.objects.all()
    serializer_class = AtividadeModeloSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(terapeuta=self.request.user)

    def perform_create(self, serializer):
        serializer.save(terapeuta=self.request.user)

class AtividadeSessaoViewSet(viewsets.ModelViewSet):
    queryset = AtividadeSessao.objects.all()
    serializer_class = AtividadeSessaoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(sessao__terapeuta=self.request.user)

    def perform_create(self, serializer):
        serializer.save()

