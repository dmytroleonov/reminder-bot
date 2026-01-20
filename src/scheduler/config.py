from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from src.bot import constants

jobstores = {"default": SQLAlchemyJobStore(url="sqlite:///jobs.sqlite")}
executors = {"default": ThreadPoolExecutor(20), "processpool": ProcessPoolExecutor(5)}
job_defaults = {"coalesce": False, "max_instances": 3}

scheduler = BackgroundScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone=constants.TIMEZONE,
)
