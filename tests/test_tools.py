from unittest.mock import MagicMock

from agent import tools


class FakeCursor:
    description = [("order_id",), ("status",)]

    def __init__(self, row=None):
        self.row = row
        self.executed = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.committed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True


class FakeConnectionManager:
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self.conn

    def __exit__(self, exc_type, exc, tb):
        return False


def test_get_order_status_returns_json(monkeypatch):
    cursor = FakeCursor(row=("ORD-001", "in_transit", "BlueDart", "BD123", 0, 0.1, "2026-06-17"))
    monkeypatch.setattr(tools, "get_db_connection", lambda: FakeConnectionManager(FakeConnection(cursor)))

    result = tools.get_order_status.invoke({"order_id": "ORD-001"})

    assert "ORD-001" in result
    assert "in_transit" in result


def test_send_merchant_alert_logs_status(monkeypatch):
    cursor = FakeCursor()
    conn = FakeConnection(cursor)
    monkeypatch.setattr(tools, "get_db_connection", lambda: FakeConnectionManager(conn))
    monkeypatch.setattr(tools, "send_whatsapp_alert", MagicMock(return_value=True))

    result = tools.send_merchant_alert.invoke(
        {"order_id": "ORD-001", "alert_type": "STUCK_ORDER", "message": "Check order"}
    )

    assert "Alert sent" in result
    assert conn.committed is True
