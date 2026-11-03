def test_health_and_case(client):
    assert client.get("/api/health").json()["status"]=="ok"
    r=client.post("/api/cases",json={"title":"Caso de teste","description":"sintético"})
    assert r.status_code==201
    assert r.json()["title"]=="Caso de teste"

def test_html_report_is_readable_and_not_raw_json(client):
    created = client.post('/api/cases', json={'title': 'Caso <sintético>', 'description': 'Teste de relatório'})
    assert created.status_code == 201
    case_id = created.json()['id']
    response = client.get(f'/api/cases/{case_id}/report.html')
    assert response.status_code == 200
    assert 'text/html' in response.headers['content-type']
    assert 'Relatório de caso' in response.text or 'RELATÓRIO DE CASO' in response.text
    assert '&lt;sintético&gt;' in response.text
    assert '<pre' not in response.text

def test_timeline_and_audit(client):
    created = client.post('/api/cases', json={'title': 'Caso de linha do tempo'})
    case_id = created.json()['id']
    event = client.post(f'/api/cases/{case_id}/timeline', json={
        'occurred_at': '2026-11-03T10:00:00Z',
        'description': 'Coleta de evidência sintética',
        'source': 'Laboratório de teste'
    })
    assert event.status_code == 201
    assert len(client.get(f'/api/cases/{case_id}/timeline').json()) == 1
    audit = client.get('/api/audit').json()
    assert any(item['action'] == 'timeline.created' for item in audit)
