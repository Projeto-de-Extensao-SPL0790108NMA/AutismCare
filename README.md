# 🧩 AppABA — Plataforma para Gerenciar Terapias ABA

📘 Apresentação
O AppABA consiste em um sistema web criado com o objetivo de apoiar terapeutas no monitoramento e na avaliação do avanço de pacientes utilizando a metodologia ABA (Applied Behavior Analysis), ou Análise do Comportamento Aplicada.
O sistema possibilita o registro de sessões, o acréscimo de atividades com resultados considerados positivos ou negativos, e a visualização de relatórios gráficos que demonstram o desempenho de cada paciente ao longo do tempo.

A solução foi pensada para profissionais e clínicas que desejam organizar o processo terapêutico de uma maneira descomplicada, segura e com uma apresentação visual intuitiva.

---

🧱 Estrutura Geral

O projeto adota uma estrutura modular, com a divisão entre o backend (Django) e o frontend (HTML/Bootstrap/Chart.js), garantindo integração completa por meio de templates e APIs REST.

| Camada | Tecnologias | Função |
|--------|--------------|--------|
| Backend | Django 5.2, Django REST Framework, SQLite/PostgreSQL | Gerenciamento da lógica, autenticação, armazenamento de dados e API REST |
| Frontend | Bootstrap 5.3, HTML5, CSS3, JavaScript, Chart.js | Interface amigável, responsiva e interativa para os terapeutas |
| Banco de Dados | SQLite (dev) / PostgreSQL (produção) | Armazenamento de informações sobre pacientes, sessões e atividades |
| Controle de Versão | Git + GitHub | Trabalho colaborativo entre equipes (branches `develop`, `feature/*`, `main`) |
| Ambiente | VSCode + venv | Ambiente de desenvolvimento local isolado |

---

⚙️ Processo de Instalação e Execução Local

# 🔧 Pré-requisitos
- Python 3.11 ou versão mais recente
- pip
- Git
- VSCode
- (Opcional) Docker + PostgreSQL
- (Opcional) sqlite3 CLI para examinar o banco de dados local

# 🧩 Instruções

```bash
# 1. Clonar o repositório
git clone https://github.com/Kalls09/AppABA.git
cd AppABA/backend

# 2. Criar ambiente virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Instalar as dependências
pip install -r requirements.txt

# 4. Executar as migrações
python manage.py migrate

# 5. Criar um superusuário (para acessar /admin)
python manage.py createsuperuser

# 6. Iniciar o servidor local
python manage.py runserver
```
