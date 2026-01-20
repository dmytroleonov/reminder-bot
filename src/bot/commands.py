from src.bot import constants
from src.bot.config import bot
from src.bot.jobs import send_task_reminder
from src.bot.utils import (
    generate_info_message,
    get_job,
    new_uuid,
    generate_list_markup,
    extract_job_id,
    is_task_list_callback,
    is_delete_task_callback,
    is_info_task_callback,
    is_edit_task_message_callback,
)
from src.bot.security import protected

from src.scheduler import scheduler
from src.scheduler.utils import get_jobs

from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.base import JobLookupError

from telebot import formatting
from telebot.types import (
    InaccessibleMessage,
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
)


@bot.message_handler(commands=["start"])
def start(message: Message) -> None:
    bot.send_message(chat_id=message.chat.id, text=constants.START_RESPONSE)


@bot.message_handler(commands=["my_id"])
def get_user_id(message: Message) -> None:
    if not message.from_user:
        return

    bot.send_message(chat_id=message.chat.id, text=str(message.from_user.id))


@bot.message_handler(commands=["list"])
@protected
def list_tasks(message: Message) -> None:
    jobs = get_jobs(message.chat.id)
    if not jobs:
        bot.send_message(chat_id=message.chat.id, text=constants.NO_TASKS)
        return

    markup = generate_list_markup(jobs)
    bot.send_message(
        chat_id=message.chat.id, text=constants.YOUR_TASKS, reply_markup=markup
    )


@bot.callback_query_handler(func=is_task_list_callback)
def list_tasks_callback(query: CallbackQuery) -> None:
    if not query.message:
        return

    jobs = get_jobs(query.message.chat.id)
    if not jobs:
        bot.edit_message_text(
            chat_id=query.message.chat.id,
            text=constants.NO_TASKS,
            reply_markup=InlineKeyboardMarkup(),
        )
        return

    markup = generate_list_markup(jobs)
    bot.edit_message_text(
        chat_id=query.message.chat.id,
        message_id=query.message.id,
        text=constants.YOUR_TASKS,
        reply_markup=markup,
    )


@bot.callback_query_handler(func=is_edit_task_message_callback)
def edit_task_message(query: CallbackQuery) -> None:
    if not query.message or isinstance(query.message, InaccessibleMessage):
        return

    job_id = extract_job_id(query)
    job = get_job(job_id)
    if not job:
        return

    old_task_message = job.kwargs["task_message"]
    bot.edit_message_text(
        chat_id=query.message.chat.id,
        message_id=query.message.id,
        text=formatting.hcode(old_task_message),
        parse_mode="HTML",
    )
    bot.register_next_step_handler(
        message=query.message, callback=edit_task_message_handler, job_id=job_id
    )


def edit_task_message_handler(message: Message, *, job_id: str) -> None:
    new_task_message = (message.text or "").lower()
    if new_task_message == constants.CANCEL_COMMAND:
        bot.send_message(
            chat_id=message.chat.id, text=constants.TASK_EDIT_MESSAGE_CANCELLED
        )
        return

    try:
        job = scheduler.modify_job(
            job_id=job_id,
            kwargs={"chat_id": message.chat.id, "task_message": new_task_message},
        )
    except JobLookupError:
        bot.send_message(chat_id=message.chat.id, text=constants.TASK_NOT_FOUND)
        return

    text, markup = generate_info_message(job)
    bot.send_message(
        chat_id=message.chat.id,
        text=text,
        reply_markup=markup,
        parse_mode="HTML",
    )


@bot.callback_query_handler(func=is_delete_task_callback)
def delete_task(query: CallbackQuery) -> None:
    if not query.message:
        return

    job_id = extract_job_id(query)
    try:
        scheduler.remove_job(job_id)
    except JobLookupError:
        pass
    finally:
        jobs = get_jobs(query.message.chat.id)
        if not jobs:
            if isinstance(query.message, InaccessibleMessage):
                return

            bot.delete_message(
                chat_id=query.message.chat.id, message_id=query.message.id
            )
            return

    markup = generate_list_markup(jobs)
    bot.edit_message_text(
        chat_id=query.message.chat.id,
        message_id=query.message.id,
        text=constants.YOUR_TASKS,
        reply_markup=markup,
    )


@bot.callback_query_handler(func=is_info_task_callback)
def task_info(query: CallbackQuery) -> None:
    if not query.message:
        return

    job_id = extract_job_id(query)
    job = get_job(job_id)
    if not job:
        bot.answer_callback_query(
            callback_query_id=query.id, text=constants.TASK_NOT_FOUND
        )
        return

    text, markup = generate_info_message(job)
    bot.edit_message_text(
        chat_id=query.message.chat.id,
        message_id=query.message.id,
        text=text,
        reply_markup=markup,
        parse_mode="HTML",
    )


@bot.message_handler(func=lambda message: True)
@protected
def add_task(message: Message) -> None:
    bot.send_message(
        chat_id=message.chat.id, text=constants.CRON_FORMAT, parse_mode="HTML"
    )
    bot.register_next_step_handler(
        message=message, callback=choose_time, task_message=message.text
    )


def choose_time(message: Message, *, task_message: str) -> None:
    crontab = (message.text or "").lower()
    if crontab == constants.CANCEL_COMMAND:
        bot.send_message(
            chat_id=message.chat.id, text=constants.TASK_CREATION_CANCELLED
        )
        return

    try:
        trigger = CronTrigger.from_crontab(crontab, timezone=scheduler.timezone)
    except ValueError:
        bot.send_message(chat_id=message.chat.id, text=constants.INVALID_CRON_FORMAT)
        bot.register_next_step_handler(
            message=message, callback=choose_time, task_message=task_message
        )
        return

    scheduler.add_job(
        func=send_task_reminder,
        trigger=trigger,
        kwargs={"chat_id": message.chat.id, "task_message": task_message},
        id=new_uuid(),
    )
    bot.send_message(chat_id=message.chat.id, text=constants.TASK_CREATED)
