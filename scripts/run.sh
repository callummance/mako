#!/usr/bin/env sh

BACKUP_SCRIPT="python3 /backup_script/backup.py"

# Add cron jobs to crontab file
DAILY_CRON_TIME="0 1 * * *"
WEEKLY_CRON_TIME="0 0 * * 0"

echo "${DAILY_CRON_TIME} ${BACKUP_SCRIPT} -d >> /mako.log 2>&1" > /crontab.conf
echo "${WEEKLY_CRON_TIME} ${BACKUP_SCRIPT} -w >> /mako.log 2>&1" >> /crontab.conf
crontab /crontab.conf

# Run initial daily and weekly backups
${BACKUP_SCRIPT} -w
${BACKUP_SCRIPT} -d

# Run cron
exec crond -f