sudo apt update
sudo apt install redis-server supervisor
# After this follow: https://sodocumentation.net/django/topic/7091/running-celery-with-supervisor#running-supervisor

# celery -A CoviRx worker --loglevel=debug --concurrency=4 -E -B
