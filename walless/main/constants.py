GROUPS = {
    "info": "🔔 Info",
    "gfw": "🧱 GFW",
    "acceleration": "🚀 Accel."
}

FLAGS = {
    "US": "🇺🇸",
    "LU": "🇱🇺",
    "HK": "🇭🇰",
    "CN": "🇨🇳",
    "SG": "🇸🇬",
    "KR": "🇰🇷",
    "JP": "🇯🇵",
    "AU": "🇦🇺",
    "DE": "🇩🇪",
    "RU": "🇷🇺",
}

HEALTH_CHECK_CFGS = {
    'gfw': {'enable': True, 'interval': 3600, 'url': 'http://cp.cloudflare.com/'},
    'acceleration': {'enable': True, 'interval': 3600, 'url': 'http://cp.cloudflare.com/'},
    'gaol': {'enable': True, 'interval': 600, 'url': 'http://pan.baidu.com/'},
}

PROVIDER_GROUPS = ['info', 'gfw', 'gaol']

DEFAULT_DNS = {
    'enable': True,
    'listen': '0.0.0.0:53',
    'default-nameserver': [
        '114.114.114.114',
        '8.8.8.8',
    ],
    'enhanced-mode': 'fake-ip',
    'fake-ip-range': '198.18.0.1/16',
    'nameserver': [
        '223.5.5.5',
        '8.8.8.8',
        '101.6.6.6',
        '119.29.29.29',
        '162.105.129.122'
    ],
    'fallback': [
        'https://dns.rubyfish.cn/dns-query',
        'https://101.6.6.6:8443/resolve',
    ],
    'fallback-filter': {
        'geoip': True,
        'ipcidr': [
            '0.0.0.0/8',
            '10.0.0.0/8',
            '100.64.0.0/10',
            '127.0.0.0/8',
            '169.254.0.0/16',
            '172.16.0.0/12',
            '192.0.0.0/24',
            '192.0.2.0/24',
            '192.168.0.0/16',
            '198.18.0.0/15',
            '198.51.100.0/24',
            '203.0.113.0/24'
        ]
    }
}

CONFIG_TEMPLATE = {
    'mixed-port': 7890,
    'port': 7891,
    'socks-port': 7892,
    'allow-lan': False,
    'mode': 'Rule',
    'log-level': 'info',
    'external-controller': '127.0.0.1:9090',
    'ipv6': True,
    'proxies': list(),
    'proxy-groups': list(),
    'proxy-providers': dict(),
}

GROUP_ORDER = ['gfw', 'info', 'acceleration']

MAX_EMAIL_HEADER_LENGTH = 4096
