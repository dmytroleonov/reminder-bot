from datetime import datetime
import uuid

from telebot import formatting

from src.bot import constants

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from src.scheduler import scheduler

from apscheduler.job import Job
from apscheduler.triggers.cron import CronTrigger


def new_uuid() -> str:
    return str(uuid.uuid4())


def get_job(job_id: str) -> Job | None:
    return scheduler.get_job(job_id)


def from_now(time: datetime) -> str:
    td = time - datetime.now(tz=constants.TIMEZONE)
    seconds = int(td.total_seconds())
    minutes = seconds // 60
    hours = minutes // 60
    days = hours // 24
    months = days // 30
    years = days // 365

    if years > 0:
        return f"{years}y"
    if months > 0:
        return f"{months}mo"
    if days > 0:
        return f"{days}d"
    if hours > 0:
        return f"{hours}h"
    if minutes > 0:
        return f"{minutes}m"
    return f"{seconds}s"


def info_callback(job_id: str) -> str:
    return f"{constants.INFO_TASK_PREFIX}{job_id}"


def edit_message_callback(job_id: str) -> str:
    return f"{constants.EDIT_TASK_MESSAGE_PREFIX}{job_id}"


def edit_cron_callback(job_id: str) -> str:
    return f"{constants.EDIT_TASK_CRON_PREFIX}{job_id}"


def delete_callback(job_id: str) -> str:
    return f"{constants.DELETE_TASK_PREFIX}{job_id}"


def inline_keyboard_edit_message_button(job_id: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text="✏️", callback_data=edit_message_callback(job_id))


def inline_keyboard_edit_cron_button(job_id: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text="🔄", callback_data=edit_cron_callback(job_id))


def inline_keyboard_delete_button(job_id: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text="❌", callback_data=delete_callback(job_id))


def inline_keyboard_back_button() -> InlineKeyboardButton:
    return InlineKeyboardButton(text="◀️", callback_data=constants.LIST_CALLBACK)


def extract_job_id(query: CallbackQuery) -> str:
    return (query.data or "").split(":")[1]


def generate_list_markup(jobs: list[Job]) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=1)
    for job in jobs:
        time_left = from_now(job.next_run_time)
        task_message = job.kwargs["task_message"]
        text = f"{time_left}: {task_message}"
        task_button = InlineKeyboardButton(
            text=text, callback_data=info_callback(job.id)
        )
        markup.add(task_button)

    return markup


def get_crontab(trigger: CronTrigger):
    fields = trigger.fields
    minute = fields[CronTrigger.FIELD_NAMES.index("minute")]
    hour = fields[CronTrigger.FIELD_NAMES.index("hour")]
    day = fields[CronTrigger.FIELD_NAMES.index("day")]
    month = fields[CronTrigger.FIELD_NAMES.index("month")]
    day_of_week = fields[CronTrigger.FIELD_NAMES.index("day_of_week")]

    return f"{minute} {hour} {day} {month} {day_of_week}"


def has_prefix(data: str, prefix: str) -> bool:
    return data.startswith(prefix)


def is_delete_task_callback(query: CallbackQuery) -> bool:
    return has_prefix(query.data or "", constants.DELETE_TASK_PREFIX)


def is_edit_task_message_callback(query: CallbackQuery) -> bool:
    return has_prefix(query.data or "", constants.EDIT_TASK_MESSAGE_PREFIX)


def is_info_task_callback(query: CallbackQuery) -> bool:
    return has_prefix(query.data or "", constants.INFO_TASK_PREFIX)


def is_task_list_callback(query: CallbackQuery) -> bool:
    return query.data == constants.LIST_CALLBACK


def generate_info_message(job: Job) -> tuple[str, InlineKeyboardMarkup]:
    task_message = job.kwargs["task_message"]
    next_run_time = datetime.strftime(job.next_run_time, "%Y-%m-%d %H:%M")
    crontab = get_crontab(job.trigger)
    markup = InlineKeyboardMarkup(row_width=4)
    back_button = inline_keyboard_back_button()
    edit_message_button = inline_keyboard_edit_message_button(job.id)
    delete_button = inline_keyboard_delete_button(job.id)
    markup.add(back_button, edit_message_button, delete_button)
    text = (
        f"{task_message}\n"
        f"{formatting.hbold('Next run time')}: {next_run_time}\n"
        f"{formatting.hbold('Crontab')}: {crontab}"
    )

    return (text, markup)
