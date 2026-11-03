# ForenseLab

Plataforma educacional para organização de casos, registro de evidências digitais, verificação de integridade por SHA-256, linha do tempo, auditoria e geração de relatórios.

> **Uso responsável:** utilize somente arquivos próprios, sintéticos ou para os quais você tenha autorização explícita. O ForenseLab é um projeto educacional e não substitui procedimentos periciais formais.

## Demonstração pública

O ForenseLab pode ser publicado como uma demonstração pública com dados sintéticos. A instância de demonstração é compartilhada: qualquer visitante pode visualizar, criar ou alterar registros. **Não envie dados pessoais, informações confidenciais ou evidências reais.** Utilize exclusivamente arquivos fictícios e sem informações sensíveis.

Quando `DEMO_MODE=true`, a API cria um caso demonstrativo com a amostra versionada em `examples/synthetic-lab/sample-note.txt`, somente se o banco estiver vazio. O limite padrão de upload nesse modo é 5 MiB.

A configuração de demonstração não fornece autenticação, isolamento entre visitantes, proteção contra abuso em escala ou garantias de disponibilidade. O banco SQLite e os arquivos armazenados em sistemas de arquivos efêmeros podem ser perdidos em reinicializações, redeploys ou substituições da instância. A demo não é adequada para investigações reais nem para armazenamento de evidências.

## Funcionalidades

- Dashboard com indicadores básicos.
- Cadastro e consulta de casos.
- Importação de evidências com armazenamento e cálculo SHA-256.
- Verificação posterior do hash registrado (`intact`, `divergence` ou `unavailable`).
- Linha do tempo por caso.
- Histórico de auditoria das ações principais.
- Relatórios HTML para leitura/impressão e exportação JSON.

## Requisitos

- Python 3.11 ou superior.
- Node.js 20 ou superior e npm.

## Executar em desenvolvimento

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e '.[dev]'
pytest -q
uvicorn app.main:app --reload --host 127.0.0.1
```

API: `http://127.0.0.1:8000`  
Documentação: `http://127.0.0.1:8000/docs`

### Frontend (outro terminal)

```bash
cd frontend
npm install
npm run dev
```

Interface: `http://localhost:5173`

## Deploy no Render

O arquivo `render.yaml` descreve um serviço web para a API e um site estático para o frontend.

1. No Render, crie um Blueprint apontando para este repositório e selecione a branch `main` ou a branch de deploy revisada.
2. Confirme a criação dos serviços `forenselab-api` e `forenselab-web`.
3. Após o site estático receber seu domínio `.onrender.com`, configure no serviço da API a variável `CORS_ORIGINS` com a origem completa do frontend, por exemplo `https://seu-site.onrender.com` (sem barra no final).
4. Confirme no serviço estático que `VITE_API_BASE_URL` aponta para o host público da API. A configuração do Blueprint usa a referência do serviço quando suportada; caso contrário, informe a URL completa manualmente, incluindo `https://`.
5. Faça um redeploy dos dois serviços e teste `/api/health`, dashboard, upload de um arquivo sintético pequeno, verificação SHA-256 e relatórios.

### Variáveis de ambiente da API

- `DEMO_MODE=true`: ativa o aviso e o seed de dados sintéticos.
- `MAX_UPLOAD_BYTES=5242880`: limite de upload padrão de 5 MiB.
- `CORS_ORIGINS`: origens permitidas separadas por vírgula; informe o domínio real do frontend.
- `DATABASE_URL`: URL do banco. O padrão é SQLite local.
- `STORAGE_DIR`: diretório de armazenamento de evidências.
- `PORT`: porta fornecida automaticamente pelo Render.

### Limitações da hospedagem

A configuração inicial usa SQLite e armazenamento em arquivos no filesystem da instância. Em planos sem disco persistente, esses dados são efêmeros e podem desaparecer. Mesmo com disco persistente, uma única instância e SQLite não oferecem uma arquitetura multiusuário robusta. A demo é compartilhada e pode ser modificada por qualquer visitante.

## Relatórios

Na tela de um caso, use **Abrir relatório HTML** para visualizar ou imprimir/salvar em PDF. **Exportar JSON** disponibiliza os dados estruturados.

## Integridade e limitações

O SHA-256 permite comparar o conteúdo atual do arquivo armazenado com o hash calculado na importação. `intact` significa correspondência; `divergence` indica diferença; `unavailable` indica que o arquivo armazenado não foi encontrado. Isso, isoladamente, **não comprova autenticidade, autoria, origem ou cadeia de custódia formal**.

Antes de qualquer uso real, avalie controles adicionais de acesso, proteção do banco de dados, backups, retenção, trilhas de auditoria resistentes a adulteração e procedimentos documentados de cadeia de custódia.

## Estrutura

```text
backend/       API FastAPI, modelos, configuração e testes
frontend/      Interface React + TypeScript
storage/       Arquivos de evidência armazenados localmente
docs/          Documentação técnica e de segurança
examples/      Arquivos sintéticos para demonstração
```

## Licença

MIT — consulte `LICENSE`.
