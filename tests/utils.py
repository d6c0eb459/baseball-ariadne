def init_db(db):
    data = [
        ("1", "Andy", "Anderson", 2000, "CAN"),
        ("2", "Bob", "Ball", 2001, "CAN"),
        ("3", "Bill", "Baker", 2002, "USA"),
        ("4", "Charlie", "Cho", 2003, "CAN"),
    ]

    db.insert("INSERT INTO 'People' VALUES(?, ?, ?, ?, ?)", data)

    data = [
        ("1", 10, 20, 2, 2, 3, 4),
        ("1", 90, 21, 3, 8, 7, 6),
        ("2", 50, 22, 3, 6, 7, 8),
        ("3", 10, 23, 4, 2, 3, 4),
        ("3", 10, 24, 2, 2, 3, 4),
        ("3", 10, 23, 3, 2, 3, 4),
        ("4", 50, 22, 2, 6, 7, 8),
    ]

    db.insert("INSERT INTO 'Batting' VALUES(?, ?, ?, ?, ?, ?, ?)", data)
