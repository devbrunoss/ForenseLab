import hashlib
import html
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .config import CORS_ORIGINS, DEMO_MODE, MAX_UPLOAD, ROOT, STORAGE
from .db import Base, Session as SessionLocal, engine, get_db
from .models import Audit, Case, Evidence, Timeline

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ForenseLab API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["*"],
)


def seed_demo_data():
    """Create one synthetic case on first boot of an empty demo database."""
    if not DEMO_MODE:
        return

    db = SessionLocal()
    try:
        if db.scalar(select(func.count()).select_from(Case)):
            return

        sample = ROOT / "examples" / "synthetic-lab" / "sample-note.txt"
        if not sample.is_file():
            return

        STORAGE.mkdir(parents=True, exist_ok=True)
        storage_name = f"{uuid.uuid4().hex}.bin"
        content = sample.read_bytes()
        (STORAGE / storage_name).write_bytes(content)

        case = Case(
            title="Caso demonstrativo — Amostra sintética",
            description="Caso fictício criado automaticamente para apresentar as funcionalidades do ForenseLab. Não representa uma investigação real.",
            priority="low",
        )
        db.add(case)
        db.flush()

        evidence = Evidence(
            case_id=case.id,
            original_name="sample-note.txt",
            storage_name=storage_name,
            size=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
        )
        db.add(evidence)
        db.add(Timeline(
            case_id=case.id,
            occurred_at=datetime.now(timezone.utc),
            description="Amostra sintética importada para demonstração.",
            source="Laboratório demonstrativo ForenseLab",
        ))
        db.add(Audit(
            case_id=case.id,
            action="demo.initialized",
            description="Dados sintéticos de demonstração inicializados.",
        ))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


seed_demo_data()


class CaseIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    priority: str = "medium"


class TimelineIn(BaseModel):
    occurred_at: datetime
    description: str = Field(min_length=1)
    source: str = "Não informado"


@app.get("/api/health")
def health():
    return {"status": "ok", "demo_mode": DEMO_MODE}


def log(db, case_id, action, description):
    db.add(Audit(case_id=case_id, action=action, description=description))


@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db)):
    return {
        "cases": db.scalar(select(func.count()).select_from(Case)) or 0,
        "evidence": db.scalar(select(func.count()).select_from(Evidence)) or 0,
        "open": db.scalar(select(func.count()).select_from(Case).where(Case.status == "open")) or 0,
    }


@app.post("/api/cases", status_code=201)
def create_case(data: CaseIn, db: Session = Depends(get_db)):
    c = Case(**data.model_dump())
    db.add(c)
    db.flush()
    log(db, c.id, "case.created", "Caso criado")
    db.commit()
    db.refresh(c)
    return c


@app.get("/api/cases")
def cases(db: Session = Depends(get_db)):
    return db.scalars(select(Case).order_by(Case.created_at.desc())).all()


@app.get("/api/cases/{case_id}")
def case_detail(case_id: str, db: Session = Depends(get_db)):
    c = db.get(Case, case_id)
    if not c:
        raise HTTPException(404, "Caso não encontrado")
    return c


@app.patch("/api/cases/{case_id}/status")
def set_status(case_id: str, status: str, db: Session = Depends(get_db)):
    c = db.get(Case, case_id)
    if not c:
        raise HTTPException(404, "Caso não encontrado")
    if status not in {"open", "in_analysis", "closed", "archived"}:
        raise HTTPException(422, "Status inválido")
    c.status = status
    log(db, c.id, "case.status_changed", f"Status alterado para {status}")
    db.commit()
    return c


@app.post("/api/cases/{case_id}/evidence", status_code=201)
async def upload(case_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    c = db.get(Case, case_id)
    if not c:
        raise HTTPException(404, "Caso não encontrado")

    STORAGE.mkdir(parents=True, exist_ok=True)
    name = uuid.uuid4().hex + ".bin"
    path = STORAGE / name
    digest = hashlib.sha256()
    size = 0
    try:
        with path.open("xb") as out:
            while chunk := await file.read(256 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD:
                    raise HTTPException(413, f"Limite de upload excedido ({MAX_UPLOAD} bytes)")
                digest.update(chunk)
                out.write(chunk)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    finally:
        await file.close()

    e = Evidence(
        case_id=case_id,
        original_name=Path(file.filename or "evidence").name[:255],
        storage_name=name,
        size=size,
        sha256=digest.hexdigest(),
    )
    try:
        db.add(e)
        db.flush()
        log(db, c.id, "evidence.imported", f"Evidência importada: {e.original_name}")
        db.commit()
        db.refresh(e)
    except Exception:
        db.rollback()
        path.unlink(missing_ok=True)
        raise
    return e


@app.get("/api/cases/{case_id}/evidence")
def evidence(case_id: str, db: Session = Depends(get_db)):
    if not db.get(Case, case_id):
        raise HTTPException(404, "Caso não encontrado")
    return db.scalars(select(Evidence).where(Evidence.case_id == case_id)).all()


@app.post("/api/evidence/{evidence_id}/verify")
def verify(evidence_id: str, db: Session = Depends(get_db)):
    e = db.get(Evidence, evidence_id)
    if not e:
        raise HTTPException(404, "Evidência não encontrada")
    p = STORAGE / e.storage_name
    if not p.is_file():
        result = "unavailable"
        actual = None
    else:
        h = hashlib.sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        actual = h.hexdigest()
        result = "intact" if actual == e.sha256 else "divergence"
    e.integrity_status = result
    log(db, e.case_id, "evidence.verified", f"Verificação: {result}")
    db.commit()
    return {"result": result, "registered_sha256": e.sha256, "calculated_sha256": actual}


@app.post("/api/cases/{case_id}/timeline", status_code=201)
def add_timeline(case_id: str, data: TimelineIn, db: Session = Depends(get_db)):
    if not db.get(Case, case_id):
        raise HTTPException(404, "Caso não encontrado")
    t = Timeline(case_id=case_id, **data.model_dump())
    db.add(t)
    log(db, case_id, "timeline.created", "Evento de linha do tempo criado")
    db.commit()
    db.refresh(t)
    return t


@app.get("/api/cases/{case_id}/timeline")
def timeline(case_id: str, db: Session = Depends(get_db)):
    if not db.get(Case, case_id):
        raise HTTPException(404, "Caso não encontrado")
    return db.scalars(select(Timeline).where(Timeline.case_id == case_id).order_by(Timeline.occurred_at)).all()


@app.get("/api/audit")
def audit(db: Session = Depends(get_db)):
    return db.scalars(select(Audit).order_by(Audit.created_at.desc()).limit(300)).all()


def build_report(case_id: str, db: Session):
    c = db.get(Case, case_id)
    if not c:
        raise HTTPException(404, "Caso não encontrado")
    ev = db.scalars(select(Evidence).where(Evidence.case_id == case_id)).all()
    tl = db.scalars(select(Timeline).where(Timeline.case_id == case_id).order_by(Timeline.occurred_at)).all()
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "case": {"id": c.id, "title": c.title, "description": c.description, "status": c.status},
        "evidence": [
            {"name": x.original_name, "size": x.size, "sha256": x.sha256, "integrity_status": x.integrity_status}
            for x in ev
        ],
        "timeline": [
            {"occurred_at": str(x.occurred_at), "recorded_at": str(x.recorded_at),
             "description": x.description, "source": x.source}
            for x in tl
        ],
        "limitation": "A correspondência do hash demonstra que o arquivo armazenado corresponde ao hash registrado. Não comprova autenticidade, autoria ou procedência da evidência.",
    }


@app.get("/api/cases/{case_id}/report.json")
def report(case_id: str, db: Session = Depends(get_db)):
    data = build_report(case_id, db)
    log(db, case_id, "report.generated", "Relatório JSON gerado")
    db.commit()
    return data


@app.get("/api/cases/{case_id}/report.html", response_class=HTMLResponse)
def report_html(case_id: str, db: Session = Depends(get_db)):
    data = build_report(case_id, db)
    log(db, case_id, "report.generated", "Relatório HTML gerado")
    db.commit()
    case = data["case"]
    title = html.escape(case["title"])
    description = html.escape(case["description"] or "Sem descrição informada")
    status = html.escape(case["status"])
    generated = html.escape(data["generated_at"])
    evidence_rows = "".join(
        "<tr><td>" + html.escape(item["name"]) + "</td><td>" + str(item["size"]) +
        " bytes</td><td><code>" + html.escape(item["sha256"]) + "</code></td><td>" +
        html.escape(item["integrity_status"] or "Não verificado") + "</td></tr>"
        for item in data["evidence"]
    ) or '<tr><td colspan="4">Nenhuma evidência registrada.</td></tr>'
    timeline_rows = "".join(
        "<tr><td>" + html.escape(item["occurred_at"]) + "</td><td>" +
        html.escape(item["description"]) + "</td><td>" + html.escape(item["source"]) + "</td></tr>"
        for item in data["timeline"]
    ) or '<tr><td colspan="3">Nenhum evento registrado.</td></tr>'
    limitation = html.escape(data["limitation"])
    page = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Relatório — {title}</title>
<style>
:root{{--bg:#0b1220;--panel:#111d2d;--line:#26384d;--text:#e8eef5;--muted:#9aadc0;--accent:#65dcb9}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font:14px Arial,sans-serif;line-height:1.6}}
main{{max-width:1100px;margin:40px auto;padding:0 22px}}header,.card{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:24px;margin-bottom:18px}}
.kicker{{color:var(--accent);font-size:11px;letter-spacing:2px}}h1{{margin:8px 0}}h2{{font-size:17px;margin:0 0 15px}}.meta{{color:var(--muted);font-size:12px}}
table{{width:100%;border-collapse:collapse;overflow-wrap:anywhere}}th,td{{padding:12px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}}th{{color:var(--accent);font-size:11px;text-transform:uppercase}}code{{font-size:11px;word-break:break-all}}.warning{{border-left:3px solid #e3b65e;padding:12px;background:#2a261b;color:#e9d7a9}}
button{{background:var(--accent);border:0;padding:10px 14px;border-radius:7px;font-weight:bold;cursor:pointer}}@media print{{body{{background:white;color:#111}}header,.card{{background:white;border-color:#ccc}}.meta{{color:#555}}th{{color:#176b56}}button{{display:none}}.warning{{background:#fff8e8;color:#333}}}}
</style></head><body><main><header><div class="kicker">FORENSELAB · RELATÓRIO DE CASO</div><h1>{title}</h1>
<p>{description}</p><div class="meta">Status: {status} · Gerado em: {generated}</div><p><button onclick="window.print()">Imprimir / Salvar em PDF</button></p></header>
<section class="card"><h2>1. Evidências</h2><table><thead><tr><th>Arquivo</th><th>Tamanho</th><th>SHA-256</th><th>Integridade</th></tr></thead><tbody>{evidence_rows}</tbody></table></section>
<section class="card"><h2>2. Linha do tempo</h2><table><thead><tr><th>Data/hora do evento</th><th>Descrição</th><th>Fonte</th></tr></thead><tbody>{timeline_rows}</tbody></table></section>
<section class="card"><h2>3. Limitações e observações</h2><p class="warning">{limitation}</p><p class="meta">ID do caso: {html.escape(case["id"])}</p></section>
</main></body></html>"""
    return HTMLResponse(page)
