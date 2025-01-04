## Run as a service with systemd

Run the django as a service using systemd. The following script can generate a unit file.

```bash
sudo cat <<EOF > /etc/systemd/system/subs.service
[Unit]
Description=Walless Subscription
Wants=network-online.target
After=network-online.target nss-lookup.target

[Service]
Type=exec
User=$USER
WorkingDirectory=$WALLESS_ROOT/site/walless
ExecStart=$WALLESS_VENV/bin/python3 manage.py runserver 127.0.0.1:9011
TimeoutStopSec=infinity
Restart=on-failure

Environment="WALLESS_ROOT=$WALLESS_ROOT"
Environment="WALLESS_VENV=$WALLESS_VENV"
Environment="EARLY_SETUP=1"
Environment="GHPAT=$GHPAT"

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl --now enable subs
```

## Reserve proxy with nginx

Nginx is used to provide reversed proxy and fine-grained control.
Here we provide a config file, which can be saved to files such as `/etc/nginx/available/walless.conf`.
Run the following command to set it up.

```bash
DOMAINS="
example.com 
*.example.org
"

sudo cat <<EOF > /etc/nginx/available/walless.conf
server {
    server_name
$DOMAINS
        ;

    listen 127.0.0.1:10302;
    charset utf-8;
    client_max_body_size 100M;
    rewrite ^/ssr/(.*)$ /$1;
    # for static files
    location = /favicon.ico {
        alias $WALLESS_ROOT/site/static_files/favicon.ico;
    }
    location /static {
        alias $WALLESS_ROOT/site/static_files;
    }
    location = /robots.txt {
        alias $WALLESS_ROOT/site/robos.txt;
    }
    # redirect the root location
    location = / {
        return 301 https://\$host/verify;
    }
    # verify user identity for auth page
    location /a/ {
        proxy_pass http://127.0.0.1:9011;
        auth_basic Restricted;
        auth_basic_user_file /etc/nginx/auth;
    }
    # for the rest of the valid requests, redirect to 9011
    location ~ ^/(verify$|verify/$|clash|profile|reset|admin).* {
        # location / {
        proxy_pass http://127.0.0.1:9011;
        proxy_set_header Host \$host;
        proxy_set_header X-real-ip \$remote_addr;
    }
    location /status {
        stub_status on;
    }
    # reject other requests
    location / {
        return 404;
    }
}
EOF

ln -s ../available/walless.config /etc/nginx/enabled/walless.config
sudo systemctl enable --now nginx
sudo nginx -s reload
```


## HTTPS with HAProxy

HAProxy can be used to provide HTTPS. A config file is
```bash
sudo cat <<EOF > /etc/haproxy/haproxy.cfg
global
    maxconn 65535
    stats timeout 1m
    stats socket /var/run/haproxy.sock mode 600 level admin
    ssl-default-bind-ciphersuites TLS_AES_128_GCM_SHA256

defaults
    mode tcp
    maxconn 65535
    timeout connect 5s
    timeout client  1m
    timeout server  1m

listen https
    mode http
    bind *:443 ssl crt $WALLESS_ROOT/ca/pem alpn h2,http/1.1
    bind :::443 ssl crt $WALLESS_ROOT/ca/pem alpn h2,http/1.1
    server nginx 127.0.0.1:10302
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now haproxy
```

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
