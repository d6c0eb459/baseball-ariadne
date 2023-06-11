function dev.test.unit() {
    python -m unittest discover
}

function dev.run.server() {
    # gunicorn --reload --bind 0.0.0.0 src.server:app
    uvicorn --reload --host 0.0.0.0 src.server:app
}

function dev.run.setup() {
    wget -qO- "https://github.com/rippinrobr/baseball-stats-db/releases/download/2018.02/baseballdatabank-2019-02-18-sqlite.tgz" | tar xvz
    cat baseballdatabank-2019-02-18-sqlite.sql | sqlite3 database.sqlite
    echo "Done"
}
