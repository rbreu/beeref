USER_VERSION = 2
APPLICATION_ID = 2060242126


SCHEMA = [
    """
    CREATE TABLE items (
        id INTEGER PRIMARY KEY,
        type TEXT NOT NULL,
        x REAL DEFAULT 0,
        y REAL DEFAULT 0,
        z REAL DEFAULT 0,
        scale REAL DEFAULT 1,
        rotation REAL DEFAULT 0,
        flip INTEGER DEFAULT 1,
        data JSON
    )
    """,
    """
    CREATE TABLE sqlar (
        name TEXT PRIMARY KEY,
        item_id INTEGER NOT NULL,
        mode INT,
        mtime INT default current_timestamp,
        sz INT,
        data BLOB,
        FOREIGN KEY (item_id)
          REFERENCES items (id)
             ON DELETE CASCADE
             ON UPDATE NO ACTION
    )
    """,
]


MIGRATIONS = {
    2: [
        "ALTER TABLE items ADD COLUMN data JSON",
        "UPDATE items SET data = json_object('filename', filename)",
    ],
}
