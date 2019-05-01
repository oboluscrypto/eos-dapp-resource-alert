import json
import logging
import sys
from collections import deque
from datetime import datetime, timedelta
from time import sleep

import requests


class RPCApi:
    def __init__(self, endpoints, logger=None):
        self.endpoints = endpoints
        self.headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
        }
        self.logger = logger

    def get_account(self, account):
        data = {"account_name": account}

        res = requests.post(self.endpoints[0] + '/v1/chain/get_account', headers=self.headers, json=data)
        if not res.ok:
            if self.logger:
                self.logger.error(f"Error sending telegram message. Code: {res.status_code}", flush=sys.stderr)
            raise ConnectionError()
        return json.loads(res.content)


class AlertBot:
    def __init__(self, token: str, chat_id: str, telegram_endpoint: str):
        self.msgTimes = deque(maxlen=5)  # messages per minute
        self.headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
        }
        self.endpoint = telegram_endpoint + token
        self.chatId = chat_id
        self.nextAllowed = None

    def send_message(self, text):
        now = datetime.now()
        if self.nextAllowed and now < self.nextAllowed:
            return

        if len(self.msgTimes) and (now - self.msgTimes.popleft()).total_seconds() < 60:
            print(f"Sent too many messages", flush=sys.stderr)
            data = {"chat_id": self.chatId, "text": "Skipping some messages"}
            res = requests.post(self.endpoint + '/sendMessage', headers=self.headers, json=data)
            if not res.ok:
                print(f"Error sending telegram message. Code: {res.status_code}", flush=sys.stderr)
            self.nextAllowed = now + timedelta(seconds=60)

        self.nextAllowed = None
        data = {"chat_id": self.chatId, "text": text}
        res = requests.post(self.endpoint + '/sendMessage', headers=self.headers, json=data)
        self.msgTimes.append(datetime.now())
        if not res.ok:
            print(f"Error sending telegram message. Code: {res.status_code}", flush=sys.stderr)


class ContractMon(RPCApi):
    def __init__(self, endpoints, limits: dict, logger=None, bot: AlertBot = None):
        assert logger or bot, "Either telegram bot or logger must be set to see any warnings"
        self.logger = logger
        self.bot = bot
        self.limits = limits
        self.above_limit = False
        super().__init__(endpoints=endpoints)

    def get_resources(self, account):
        info = self.get_account(account)

        resmax = info["net_limit"]["max"]
        used = info["net_limit"]["used"]
        net = {"max": resmax, "used": used / resmax}

        resmax = info["cpu_limit"]["max"]
        used = info["cpu_limit"]["used"]
        cpu = {"max": resmax, "used": used / resmax}

        resmax = info["total_resources"]["ram_bytes"]
        used = info["ram_usage"]
        ram = {"max": resmax, "used": used / resmax}

        resources = dict(net=net, cpu=cpu, ram=ram)
        return resources

    def run(self, account):
        res = self.get_resources(account)
        cpu = res["cpu"]["used"] * 100
        net = res["net"]["used"] * 100
        ram = res["ram"]["used"] * 100
        print(res)
        text = f'({account}) CPU: {cpu:.1f}% NET: {net:.1f}% RAM: {ram:.1f}%'

        warn = False
        release = False
        if cpu > self.limits["cpu"] or net > self.limits["net"] or ram > self.limits["ram"]:
            if not self.above_limit:
                warn = True
            self.above_limit = True
        else:
            if self.above_limit:
                release = True
                self.above_limit = False

        if warn:
            text = f"Warning: " + text
            if self.bot:
                self.bot.send_message(text)
            if self.logger:
                self.logger.warn(text)
        elif release:
            text = "Dropped below limits: " + text
            if self.bot:
                self.bot.send_message(text)
            if self.logger:
                self.logger.warn(text)
        else:
            self.logger.info(text)


def main(log_path="/tmp/log.txt"):
    with open("./configs/eos-monitor.json") as fp:
        cfg = json.load(fp)
    bot = AlertBot(token=cfg["token"], chat_id=cfg["chat_id"], telegram_endpoint=cfg["telegram_endpoint"])
    logging.basicConfig(filename=log_path,
                        filemode='a',
                        format='%(asctime)s %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    monitor = ContractMon([cfg["node_endpoint"]], logger=logging, bot=bot, limits=cfg["limits"])
    while True:
        try:
            monitor.run(cfg["account"])
        except Exception as exc:
            logging.error(exc)
        sleep(60)


if __name__ == "__main__":
    main()
