from app.db.session import _connect_args


def test_connect_args_detect_sqlite_urls_case_insensitively() -> None:
    assert _connect_args("sqlite:///./app.db") == {"check_same_thread": False}
    assert _connect_args("SQLite:///./app.db") == {"check_same_thread": False}
    assert _connect_args("sqlite+pysqlite:///./app.db") == {"check_same_thread": False}


def test_connect_args_omit_sqlite_args_for_non_sqlite_urls() -> None:
    assert _connect_args("postgresql://user:password@localhost/app") == {}
