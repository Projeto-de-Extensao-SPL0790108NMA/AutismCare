from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'pacientes', views.PacienteViewSet, basename='paciente')
router.register(r'sessoes', views.SessaoViewSet, basename='sessao')
router.register(r'atividades-modelo', views.AtividadeModeloViewSet, basename='atividade_modelo')
router.register(r'atividades-sessao', views.AtividadeSessaoViewSet, basename='atividade_sessao')

urlpatterns = [
    # Páginas
    path('dashboard/', views.dashboard, name='dashboard'),
    path('adicionar/', views.adicionar_paciente, name='adicionar_paciente'),

    # Pacientes
    path("pacientes/", views.lista_pacientes, name="lista_pacientes"),
    path("pacientes/adicionar/", views.adicionar_paciente, name="adicionar_paciente"),
    path("pacientes/<int:paciente_id>/editar/", views.editar_paciente, name="editar_paciente"),
    path("pacientes/<int:paciente_id>/excluir/", views.excluir_paciente, name="excluir_paciente"),
    path("paciente/<int:paciente_id>/relatorio/", views.relatorio_paciente, name="relatorio_paciente"),

    # Sessões
    path('iniciar_sessao/<int:paciente_id>/', views.iniciar_sessao, name='iniciar_sessao'),
    path('sessao/<int:sessao_id>/registrar/', views.registrar_atividades_sessao, name='registrar_atividades_sessao'),
    path('atividade_sessao/<int:atividade_sessao_id>/detalhes/', views.registrar_detalhes_atividade, name='registrar_detalhes_atividade'),
    path('sessao/<int:sessao_id>/encerrar/', views.encerrar_sessao, name='encerrar_sessao'),
    path('sessao/<int:sessao_id>/relatorio/', views.relatorio_sessao, name='relatorio_sessao'),
    path('pacientes/<int:paciente_id>/historico/', views.historico_sessoes, name='historico_sessoes'),
    path("sessao/<int:sessao_id>/", views.detalhes_sessao, name="detalhes_sessao"),

    # Exportar relatórios
    path("relatorios/sessoes/", views.exportar_sessoes_csv, name="exportar_sessoes"),
    path("relatorios/atividades/", views.exportar_atividades_csv, name="exportar_atividades"),

    # Editar / Excluir
    path("sessao/<int:sessao_id>/editar/", views.editar_sessao, name="editar_sessao"),
    path("atividade/<int:atividade_id>/editar/", views.editar_atividade, name="editar_atividade"),
    path("atividade/<int:atividade_id>/excluir/", views.excluir_atividade, name="excluir_atividade"),

    # Atividades
    path("atividades/", views.lista_atividades, name="lista_atividades"),
    path("atividades/adicionar/", views.adicionar_atividade, name="adicionar_atividade"),
    path("atividades/<int:atividade_id>/editar/", views.editar_atividade, name="editar_atividade"),
    path("atividades/<int:atividade_id>/excluir/", views.excluir_atividade, name="excluir_atividade"),

    # Atividades Modelo
    path('atividades-modelo/', views.lista_atividades_modelo, name='lista_atividades_modelo'),
    path('atividades-modelo/novo/', views.criar_atividade_modelo, name='criar_atividade_modelo'),
    
     # Auth (se estiver usando estas views)
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # API
    path('api/', include(router.urls)),
]
