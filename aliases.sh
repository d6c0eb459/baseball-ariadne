function dev.run.server {
    gunicorn --reload --bind 0.0.0.0 server:app
}
