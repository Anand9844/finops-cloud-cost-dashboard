import os, tempfile
import pytest

@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setenv('FINOPS_DB_PATH', str(tmp_path / 'test.db'))
    import importlib, app as app_module
    importlib.reload(app_module)
    app_module.app.config.update(TESTING=True)
    with app_module.app.test_client() as client:
        yield client

def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.get_json()['status'] == 'ok'

def test_dashboard_has_demo_mode_and_metrics(client):
    data = client.get('/api/dashboard').get_json()
    assert data['mode'] == 'SIMULATED DEMO DATA'
    assert data['month_spend'] >= 0
    assert len(data['service_labels']) > 0

def test_budget_update(client):
    response = client.post('/api/settings', json={'monthly_budget': 250})
    assert response.status_code == 200
    assert client.get('/api/settings').get_json()['monthly_budget'] == 250

def test_reject_invalid_budget(client):
    assert client.post('/api/settings', json={'monthly_budget': -2}).status_code == 400

def test_weekly_csv(client):
    response = client.get('/report/weekly.csv')
    assert response.status_code == 200
    assert b'Estimated cost (USD)' in response.data

def test_prometheus_metrics(client):
    response = client.get('/metrics')
    assert response.status_code == 200
    assert b'finops_month_to_date_cost_usd' in response.data
