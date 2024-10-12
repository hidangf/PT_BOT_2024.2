import os
import psycopg2
import re
import logging
import paramiko
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import CallbackContext, ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, filters, ContextTypes
# Загрузка переменных окружения из .env файла
load_dotenv()

# Настройка логирования
logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
max_message_length = 4096
last_found = []
EMAIL_TEXT=1
PHONE_TEXT=0
PASSWORD=2
PACKAGE=3
PUSH_EMAILS=4
PUSH_PHONES=5
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Я - бот! Или, как говорится, Hey there, Im using Telegram')

async def ssh_connect(command):
    host = os.getenv('RM_HOST')
    port = int(os.getenv('RM_PORT'))
    username = os.getenv('RM_USER')
    password = os.getenv('RM_PASSWORD')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname=host, port=port, username=username, password=password)
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode()
        return output.strip() or stderr.read().decode()
    except Exception as e:
        return f"Ошибка при подключении: {str(e)}"
    finally:
        client.close()

async def ssh_database_connect(command):
    host = os.getenv('DB_HOST')
    port = int(os.getenv('RM_PORT'))
    username = os.getenv('DB_HOST_USER')
    password = os.getenv('DB_HOST_PASSWORD')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname=host, port=port, username=username, password=password)
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode()
        return output.strip() or stderr.read().decode()
    except Exception as e:
        return f"Ошибка при подключении: {str(e)}"
    finally:
        client.close()


async def get_repl_logs_docker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = "docker exec db_container grep 'replication' /var/log/postgresql/postgresql.log | tail -n 100"
    output = await ssh_connect(command)
    await update.message.reply_text(f"Логи репликации:\n")
    for i in range(0, len(output), max_message_length):
        part = output[i:i + max_message_length]
        await update.message.reply_text(part)


async def get_emails(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = await postgre_query("SELECT * FROM emails", 0)
    if data != None:
        await update.message.reply_text(text=data)
    else:
        await update.message.reply_text(text="Нечего выводить!")

async def get_phones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = await postgre_query("SELECT * FROM phones", 0)
    if data != None:
        await update.message.reply_text(text=data)
    else:
        await update.message.reply_text(text="Нечего выводить!")

async def postgre_query(query, t: int):
    data = None
    connection = None
    host = os.getenv('DB_HOST')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    port = int(os.getenv('DB_PORT'))
    database = os.getenv('DB_DATABASE')
    try:
        connection = psycopg2.connect(user=user, password=password, host=host, port=port, dbname=database)
        cursor = connection.cursor()
        cursor.execute(query)
        if t == 0:
            data = cursor.fetchall()
        else:
            data = "OK"
            connection.commit()
    except Exception as e:
        return f"Ошибка при подключении: {str(e)}"
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
    return data

async def get_df(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = "df -h"
    output = await ssh_connect(command)
    await update.message.reply_text(f"Состояние файловой системы:\n{output}")

async def get_free(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = "free -h"
    output = await ssh_connect(command)
    await update.message.reply_text(f"Состояние оперативной памяти:\n{output}")

async def get_mpstat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = "mpstat"
    output = await ssh_connect(command)
    await update.message.reply_text(f"Производительность системы:\n{output}")

async def get_w(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = "w"
    output = await ssh_connect(command)
    await update.message.reply_text(f"Активные пользователи:\n{output}")

async def get_auths(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = "last -n 10"
    output = await ssh_connect(command)
    await update.message.reply_text(f"Последние 10 входов в систему:\n{output}")

async def get_critical(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = "journalctl -p crit -n 5"
    output = await ssh_connect(command)
    await update.message.reply_text(f"Последние 5 критических событий:\n{output}")

async def get_ps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = "ps aux"
    output = await ssh_connect(command)
    await update.message.reply_text(f"Список запущенных процессов:\n")
    for i in range(0, len(output), max_message_length):
        part = output[i:i + max_message_length]
        await update.message.reply_text(part)

async def get_ss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = "ss -tuln"
    output = await ssh_connect(command)
    await update.message.reply_text(f"Используемые порты:\n")
    for i in range(0, len(output), max_message_length):
        part = output[i:i + max_message_length]
        await update.message.reply_text(part)


async def get_apt_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = "apt list --installed"
    output = await ssh_connect(command)

    for i in range(0, len(output), max_message_length):
        part = output[i:i + max_message_length]
        await update.message.reply_text(part)

async def get_apt_list_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Введите имя пакета для поиска.')
    return PACKAGE
async def search_package(update: Update, context: ContextTypes.DEFAULT_TYPE):
    package_name = update.message.text
    command = f"apt list --installed | grep {package_name}"
    output = await ssh_connect(command)
    await update.message.reply_text(f"Результаты поиска:\n{output}")
    return ConversationHandler.END

async def get_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = "systemctl list-units --type=service --state=running"
    output = await ssh_connect(command)
    await update.message.reply_text(f"Запущенные сервисы:\n{output}")


async def find_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Пожалуйста, отправьте текст для поиска email-адресов.')
    return EMAIL_TEXT

async def process_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_found
    text = update.message.text
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, text)
    last_found = emails.copy()
    if emails:
        await update.message.reply_text(f'Найденные email-адреса: {", ".join(emails)}')
    else:
        await update.message.reply_text('Email-адреса не найдены.')
        return ConversationHandler.END
    await update.message.reply_text('Хотите добавить эти адреса в базу данных? (Напишите Да или Нет)')
    
    return PUSH_EMAILS

async def push_emails(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text

    if choice not in ['Да', 'Нет']:
        await update.message.reply_text(text="Неправильный выбор")
        return ConversationHandler.END

    if choice == 'Нет':
        return ConversationHandler.END
    global last_found
    sql="INSERT INTO emails(email) VALUES"
    for i in range(len(last_found)):
        sql += f"(\'{last_found[i]}\')"
        if i == len(last_found) - 1:
            sql += ';'
        else:
            sql += ','
    data = await postgre_query(sql, 1)
    if data == None:
        await update.message.reply_text(text="Ошибка при добавлении адреса");
    else:
        await update.message.reply_text(text="OK");
    return ConversationHandler.END




async def get_release(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = "lsb_release -a"
    output = await ssh_connect(command)
    await update.message.reply_text(f"Информация о релизе:\n{output}")

async def get_uname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = "uname -a"
    output = await ssh_connect(command)
    await update.message.reply_text(f"Информация о системе:\n{output}")

async def get_uptime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = "uptime"
    output = await ssh_connect(command)
    await update.message.reply_text(f"Время работы системы:\n{output}")

async def verify_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Пожалуйста, отправьте пароль для проверки.')
    return PASSWORD  # Переходим в состояние PASSWORD

async def receive_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text

    password_pattern = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()])[A-Za-z\d!@#$%^&*()]{8,}$'

    if re.match(password_pattern, password):
        await update.message.reply_text('Пароль сложный.')
    else:
        await update.message.reply_text('Пароль простой. Убедитесь, что он содержит минимум 8 символов, включая заглавные буквы, строчные буквы, цифры и специальные символы.')

    return ConversationHandler.END  # Завершаем разговор
async def find_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Пожалуйста, отправьте текст для поиска номеров телефонов.')
    return PHONE_TEXT  # Переходим на этап ожидания текста

async def process_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_found
    text = update.message.text
    phone_pattern = r'(?:\+7|8)(?:[\s\-]?\(?(\d{3})\)?[\s\-]?)(\d{3})[\s\-]?(\d{2})[\s\-]?(\d{2})'
    phone_numbers = re.findall(phone_pattern, text)

    if phone_numbers:
        formatted_numbers = [f"8{match[0]}{match[1]}{match[2]}{match[3]}" for match in phone_numbers]
        await update.message.reply_text(f'Найденные номера телефонов: {", ".join(formatted_numbers)}')
    else:
        await update.message.reply_text('Номера телефонов не найдены.')
        return ConversationHandler.END
    last_found = formatted_numbers.copy()
    await update.message.reply_text('Хотите добавить эти номера в базу данных? (Напишите Да или Нет)')
    return PUSH_PHONES

async def push_phones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text

    if choice not in ['Да', 'Нет']:
        await update.message.reply_text(text="Неправильный выбор")
        return ConversationHandler.END

    if choice == 'Нет':
        return ConversationHandler.END
    global last_found
    sql="INSERT INTO phones(phone_number) VALUES"
    for i in range(len(last_found)):
        sql += f"(\'{last_found[i]}\')"
        if i == len(last_found) - 1:
            sql += ';'
        else:
            sql += ','
    data = await postgre_query(sql, 1)
    if data == None:
        await update.message.reply_text(text="Ошибка при добавлении номера");
    else:
        await update.message.reply_text(text="OK");
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Операция отменена.')
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Доступные команды:\n"
        "/start - Запустить бота\n"
        "/help - Показать это сообщение\n"
        "/find_email - Найти email-адреса в тексте\n"
        "/find_phone_number - Найти номера телефонов в тексте\n"
        "/verify_password - Проверить сложность пароля\n"
        "/get_release - Показать информацию о релизе системы\n"
        "/get_uname - Показать архитектуру процессора, имя хоста и версию ядра\n"
        "/get_uptime - Показать время работы системы\n"
        "/get_df - Показать информацию о состоянии файловой системы\n"
        "/get_free - Показать информацию о состоянии оперативной памяти\n"
        "/get_mpstat - Показать производительность системы\n"
        "/get_w - Показать информацию о работающих пользователях\n"
        "/get_auths - Показать последние 10 входов в систему\n"
        "/get_critical - Показать последние 5 критических событий\n"
        "/get_ps - Показать информацию о запущенных процессах\n"
        "/get_ss - Показать информацию об используемых портах\n"
        "/get_apt_list - Показать установленные пакеты\n"
        "/get_apt_list_search - Показать информацию о конкретном пакете\n"
        "/get_services - Показать запущенные сервисы\n"
        "/get_emails - Вывести email-адреса из базы данных\n"
        "/get_phones - Вывести номера телефонов из базы данных\n"
        "/get_repl_logs - Вывести логи о репликации\n"
    )
    await update.message.reply_text(help_text)

async def get_repl_logs_normal_env(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = "cat /var/log/postgresql/postgresql-14-main.log | grep -i replication"
    output = await ssh_database_connect(command)
    await update.message.reply_text(f"Найденные логи:\n")
    for i in range(0, len(output), max_message_length):
        part = output[i:i + max_message_length]
        await update.message.reply_text(part)

def inside_docker():
    try:
        with open('/proc/1/cgroup', 'r') as f:
            return 'docker' in f.read()
    except FileNotFoundError:
        return False

async def get_repl_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if inside_docker():
        await get_repl_logs_docker(update, context)
    else:
        await get_repl_logs_normal_env(update, context)

if __name__ == '__main__':
    application = ApplicationBuilder().token(os.getenv('TOKEN')).build()

        
    conversation_handler = ConversationHandler(
        entry_points=[
            CommandHandler('find_email', find_email),
            CommandHandler('find_phone_number', find_phone_number),
            CommandHandler('verify_password', verify_password),
            CommandHandler('get_apt_list_search', get_apt_list_search)
        ],
        states={
            PUSH_EMAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, push_emails)],
            PUSH_PHONES: [MessageHandler(filters.TEXT & ~filters.COMMAND, push_phones)],
            EMAIL_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_email)],
            PHONE_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_phone_number)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_password)],
            PACKAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_package)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )


    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('get_df', get_df))
    application.add_handler(CommandHandler('get_free', get_free))
    application.add_handler(CommandHandler('get_mpstat', get_mpstat))
    application.add_handler(CommandHandler('get_w', get_w))
    application.add_handler(CommandHandler('get_auths', get_auths))
    application.add_handler(CommandHandler('get_critical', get_critical))
    application.add_handler(CommandHandler('get_ps', get_ps))
    application.add_handler(CommandHandler('get_ss', get_ss))
    application.add_handler(CommandHandler('get_apt_list', get_apt_list))
    application.add_handler(CommandHandler('search_package', search_package))
    application.add_handler(CommandHandler('get_services', get_services))
    application.add_handler(CommandHandler('get_release', get_release))
    application.add_handler(CommandHandler('get_uname', get_uname))
    application.add_handler(CommandHandler('get_uptime', get_uptime))
    application.add_handler(CommandHandler('get_repl_logs', get_repl_logs))
    application.add_handler(CommandHandler('get_emails', get_emails))
    application.add_handler(CommandHandler('get_phones', get_phones))
    application.add_handler(conversation_handler)
    application.run_polling()

