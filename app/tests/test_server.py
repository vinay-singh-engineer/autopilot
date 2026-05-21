import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["AUTOPILOT_USERNAME"] = "testuser"
os.environ["AUTOPILOT_PASSWORD"] = "testpass"
os.environ["AUTOPILOT_SECRET_KEY"] = "test-secret"

import server  # noqa: E402


@pytest.fixture
def client(tmp_path):
    server.app.config["TESTING"] = True
    server.app.config["SECRET_KEY"] = "test-secret"
    server.JOB_CONFIG_FILE = str(tmp_path / "jobs.json")
    server.JOB_STATUS_FILE = str(tmp_path / "status.json")
    server.SETTINGS_FILE   = str(tmp_path / "settings.json")
    server.LOG_DIR = str(tmp_path / "logs")

    jobs = {
        "test_job": {
            "path": "jobs/nightly_backup.py",
            "enabled": True,
            "cron": "0 2 * * *",
            "info": "Test job"
        }
    }
    settings = {
        "app": {"logRetention": 7},
        "webhook": {"enabled": False, "url": ""},
        "healthCheck": {"url": ""}
    }
    with open(server.JOB_CONFIG_FILE, "w") as f:
        json.dump(jobs, f)
    with open(server.JOB_STATUS_FILE, "w") as f:
        json.dump({}, f)
    with open(server.SETTINGS_FILE, "w") as f:
        json.dump(settings, f)

    with server.app.test_client() as c:
        yield c


def _login(client):
    return client.post(
        "/autopilot/login",
        data={"username": "testuser", "password": "testpass"},
        follow_redirects=True
    )


def test_login_valid(client):
    resp = _login(client)
    assert resp.status_code == 200


def test_login_invalid(client):
    resp = client.post("/autopilot/login", data={"username": "bad", "password": "wrong"})
    assert resp.status_code == 200
    assert b"Invalid credentials" in resp.data


def test_index_unauthenticated(client):
    resp = client.get("/autopilot", follow_redirects=False)
    assert resp.status_code == 302


def test_index_authenticated(client):
    _login(client)
    resp = client.get("/autopilot")
    assert resp.status_code == 200


def test_main_unauthenticated(client):
    resp = client.get("/autopilot/main", follow_redirects=False)
    assert resp.status_code == 302


def test_main_authenticated(client):
    _login(client)
    resp = client.get("/autopilot/main")
    assert resp.status_code == 200


def test_toggle_job_disables(client):
    _login(client)
    resp = client.post("/autopilot/main/toggle/test_job", follow_redirects=True)
    assert resp.status_code == 200
    with open(server.JOB_CONFIG_FILE) as f:
        assert json.load(f)["test_job"]["enabled"] is False


def test_toggle_unknown_job(client):
    _login(client)
    resp = client.post("/autopilot/main/toggle/nonexistent")
    assert resp.status_code == 404


def test_logout(client):
    _login(client)
    resp = client.post("/autopilot/logout")
    assert resp.status_code == 200
    resp2 = client.get("/autopilot", follow_redirects=False)
    assert resp2.status_code == 302


def test_toggle_job_enables(client):
    _login(client)
    client.post("/autopilot/main/toggle/test_job")  # disable
    resp = client.post("/autopilot/main/toggle/test_job", follow_redirects=True)  # re-enable
    assert resp.status_code == 200
    with open(server.JOB_CONFIG_FILE) as f:
        assert json.load(f)["test_job"]["enabled"] is True


def test_run_unknown_job(client):
    _login(client)
    resp = client.post("/autopilot/main/run/nonexistent")
    assert resp.status_code == 404


def test_index_uptime_no_runs(client):
    _login(client)
    resp = client.get("/autopilot")
    assert resp.status_code == 200
    assert b"no runs recorded yet" in resp.data


def test_index_uptime_with_success(client):
    _login(client)
    with open(server.JOB_STATUS_FILE, "w") as f:
        json.dump({"test_job": {"status": "Success", "running": False,
                                "start_time": "01-01-2026 00:00:00",
                                "end_time": "01-01-2026 00:00:01"}}, f)
    resp = client.get("/autopilot")
    assert resp.status_code == 200
    assert b"100.0%" in resp.data


def test_index_uptime_with_failure(client):
    _login(client)
    with open(server.JOB_STATUS_FILE, "w") as f:
        json.dump({"test_job": {"status": "Failure", "running": False,
                                "start_time": "01-01-2026 00:00:00",
                                "end_time": "01-01-2026 00:00:01"}}, f)
    resp = client.get("/autopilot")
    assert resp.status_code == 200
    assert b"0.0%" in resp.data


def test_settings_unauthenticated(client):
    resp = client.get("/autopilot/settings", follow_redirects=False)
    assert resp.status_code == 302


def test_settings_get(client):
    _login(client)
    resp = client.get("/autopilot/settings")
    assert resp.status_code == 200
    assert b"Webhook" in resp.data


def test_settings_save(client):
    _login(client)
    resp = client.post("/autopilot/settings", data={
        "webhook_enabled": "on",
        "webhook_url": "https://hooks.example.com/test",
        "log_retention": "14",
        "health_check_url": "http://localhost:5000/autopilot/login",
    }, follow_redirects=False)
    assert resp.status_code == 302
    settings = json.loads(open(server.SETTINGS_FILE).read())
    assert settings["webhook"]["enabled"] is True
    assert settings["webhook"]["url"] == "https://hooks.example.com/test"
    assert settings["app"]["logRetention"] == 14


def test_settings_test_webhook_disabled(client):
    _login(client)
    resp = client.post("/autopilot/settings/test")
    assert resp.status_code == 200
    assert b"disabled" in resp.data
