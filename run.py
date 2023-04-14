from app.views import app
from apscheduler.schedulers.background import BackgroundScheduler
from app.views import get_date_to_use, save_exchange_rate

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=save_exchange_rate, trigger="cron", hour=14, minute=30, args=(get_date_to_use(), {}, "app/exchange_rates.json"))
    scheduler.start()
    app.run(debug=True)
