# wallesspku

## Cron Jobs

The following jobs should be run using tools such as crontab.

```bash
DJANGO_PATH=/path/to/walless

# generate report of today; run every day
cd $DJANGO_PATH && python3 manage.py daily_stats

# apply the db to dns servers; run every 10 minutes
cd $DJANGO_PATH && python3 manage.py sync_dns

# migrate traffic logs to user balance and traffic table. run every minute
cd $DJANGO_PATH/scripts && python3 traffic_migration.py

# reset user user balance; run every day
cd $DJANGO_PATH/scripts && python3 increment_balance.py

# scrub the database; run every day
cd $DJANGO_PATH/scripts && python3 scrub_db.py -o /path/to/save

# update certificates; run every week
# this script is not uploaded to GitHub as it contains some credentials; will update it in the future
cd $DJANGO_PATH/scripts && bash update_ca.sh
```

