import unittest
import time
import os
import signal
from subprocess import Popen
import requests
import yaml

from walless_utils import load_config


class SubsTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../walless'))
        os.chdir(path)
        cls.process = Popen(['python', 'manage.py', 'runserver', '127.0.0.1:9012'])
        time.sleep(5)
        cls.http_prefix = 'http://127.0.0.1:9012/'
        cls.sess = requests.Session()
        cls.cfg = load_config()
        print('Turned on Django.')

    @classmethod
    def tearDownClass(cls):
        cls.process.send_signal(signal.SIGTERM)
        time.sleep(2)
        cls.process.kill()
        time.sleep(2)
        print('Turned off Django.')

    def test_00_ping(self):
        ret = self.sess.get(self.http_prefix + 'ping')
        self.assertEqual(ret.status_code, 200)

    def get_test_case(self, test_name: str):
        self.assertTrue(test_name in self.cfg['test_cases'])
        return self.cfg['test_cases'][test_name]

    def sub(self, email, password, **kwargs):
        link = self.http_prefix + f'clash/{email}/{password}'
        if kwargs:
            args = []
            for k, v in kwargs.items():
                args.append(f'{k}={v}')
            link += '?' + '&'.join(args)
        ret = self.sess.get(link)
        self.assertEqual(ret.status_code, 200)
        parsed = yaml.load(ret.text, Loader=yaml.SafeLoader)
        return parsed

    def normal_test(self, test_case, group: str):
        self.sub(test_case['email'], test_case['password'], provider='false')
        sub = self.sub(test_case['email'], test_case['password'], provider='true')
        self.assertEqual(len(sub['proxy-providers']), 1)
        servers = self.sub(test_case['email'], test_case['password'], group=group)
        self.assertGreater(len(servers['proxies']), 0)
        if len(servers['proxies']) == 1:
            server = servers['proxies'][0]
            self.assertNotEqual(server['name'], 'disabled')

    def test_10_c_user(self):
        test_case = self.get_test_case('c_user')
        self.normal_test(test_case, 'gfw')

    def test_20_back2china(self):
        test_case = self.get_test_case('back2china')
        self.normal_test(test_case, 'gaol')

    def test_30_care_user(self):
        test_case = self.get_test_case('care_user')
        self.normal_test(test_case, 'gfw')

    def test_40_a_user(self):
        test_case = self.get_test_case('a_user')
        self.normal_test(test_case, 'gfw')

    def test_50_wrong_user(self):
        links = [
            self.http_prefix + 'clash/c_test_user@wallesspku.com/wrong_password',
            self.http_prefix + 'clash/wrong_email@wallesspku.com/wrong_password',
        ]
        for link in links:
            ret = self.sess.get(link)
            self.assertEqual(ret.status_code, 404)


if __name__ == '__main__':
    unittest.main()
