# ForenseLab

Plataforma local e educacional para organização de casos, registro de evidências digitais, verificação de integridade por SHA-256, linha do tempo, auditoria e geração de relatórios.

> **Uso responsável:** utilize somente arquivos próprios, sintéticos ou para os quais você tenha autorização explícita. O ForenseLab é um projeto educacional e não substitui procedimentos periciais formais.

## Funcionalidades

- Dashboard com indicadores básicos.
- Cadastro e consulta de casos.
- Importação de evidências com armazenamento local e cálculo SHA-256.
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

## Relatórios

Na tela de um caso, use **Abrir relatório HTML** para visualizar ou imprimir/salvar em PDF. **Exportar JSON** disponibiliza os dados estruturados.

## Integridade e limitações

O SHA-256 permite comparar o conteúdo atual do arquivo armazenado com o hash calculado na importação. `intact` significa correspondência; `divergence` indica diferença; `unavailable` indica que o arquivo armazenado não foi encontrado. Isso, isoladamente, **não comprova autenticidade, autoria, origem ou cadeia de custódia formal**.

O projeto foi concebido para execução local. Antes de qualquer uso real, avalie controles adicionais de acesso, proteção do banco de dados, backups, retenção, trilhas de auditoria resistentes a adulteração e procedimentos documentados de cadeia de custódia.

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
