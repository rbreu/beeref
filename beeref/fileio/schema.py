SCHEMA = [
    """
    CREATE TABLE items (
        id INTEGER PRIMARY KEY,
        type TEXT NOT NULL,
        pos_x REAL DEFAULT 0,
        pos_y REAL DEFAULT 0,
        scale REAL DEFAULT 1,
        rotation REAL DEFAULT 0,
        flip_h INTEGER DEFAULT 0,
        flip_v INTEGER DEFAULT 0,
        filename TEXT
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
