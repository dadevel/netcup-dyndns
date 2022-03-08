#!/usr/bin/env python3
from typing import Any, Callable
import dataclasses
import json
import os
import socket
import sys
import unittest.mock

import requests


def main() -> None:
    try:
        netcup_customer_number = os.environ['NETCUP_CUSTOMER_NUMBER']
        netcup_api_key = os.environ['NETCUP_API_KEY']
        netcup_api_password = os.environ['NETCUP_API_PASSWORD']
        netcup_domain = os.environ['NETCUP_DOMAIN']
        netcup_hostname = os.environ['NETCUP_HOSTNAME']
        netcup_disable_ipv6 = os.environ.get('NETCUP_DISABLE_IPV6', 'no').lower() in ('y', 'yes', 'true', '1')
    except KeyError as e:
        log(f'error: env var {e} not defined')
        exit(1)

    ipify = IPify()
    netcup = Netcup(netcup_customer_number, netcup_api_key, netcup_api_password)
    log('authenticating against netcup')
    netcup.login()
    log('fetching public ip address from ipify')
    expected4 = ipify.fetch_ipv4()
    expected6 = None if netcup_disable_ipv6 else ipify.fetch_ipv6()
    log('fetching current dns records from netcup')
    record4, actual4, record6, actual6 = netcup.fetch_dns_record(netcup_domain, netcup_hostname)
    if actual4 != expected4 or actual6 != expected6:
        log('updating dns records at netcup')
        netcup.update_dns_records(netcup_domain, netcup_hostname, record4, expected4, record6, expected6)
    else:
        log('no dns record update required')


# docs: https://www.ipify.org
# thanks to https://stackoverflow.com/a/43950235 for the trick with monkey patching socket.getaddrinfo
@dataclasses.dataclass
class IPify:
    endpoint: str = 'https://api64.ipify.org'
    socket_getaddrinfo: Callable = socket.getaddrinfo

    def fetch_ipv4(self) -> str:
        with unittest.mock.patch('socket.getaddrinfo', side_effect=self._getaddrinfo4):
            return self._get_text(self.endpoint)

    def fetch_ipv6(self) -> str:
        with unittest.mock.patch('socket.getaddrinfo', side_effect=self._getaddrinfo6):
            return self._get_text(self.endpoint)

    def _getaddrinfo4(self, host, port, family=0, type=0, proto=0, flags=0):
        return self.socket_getaddrinfo(host=host, port=port, family=socket.AF_INET, type=type, proto=proto, flags=flags)

    def _getaddrinfo6(self, host, port, family=0, type=0, proto=0, flags=0):
        return self.socket_getaddrinfo(host=host, port=port, family=socket.AF_INET6, type=type, proto=proto, flags=flags)

    @staticmethod
    def _get_text(url: str) -> str:
        response = requests.get(url)
        response.raise_for_status()
        return response.text


# docs: https://ccp.netcup.net/run/webservice/servers/endpoint.php
@dataclasses.dataclass
class Netcup:
    customer_number: str
    key: str
    password: str
    endpoint: str = 'https://ccp.netcup.net/run/webservice/servers/endpoint.php?JSON'
    session: str|None = None

    def login(self) -> str:
        response = self._request('login', apipassword=self.password)
        self.session = response['responsedata']['apisessionid']
        return self.session

    def fetch_dns_record(self, domain: str, hostname: str) -> tuple[str|None, str|None, str|None, str|None]:
        record4, destination4, record6, destination6 = None, None, None, None
        response = self.fetch_dns_records(domain)
        for record in response['responsedata']['dnsrecords']:
            if record['hostname'] == hostname:
                if record['type'] == 'A':
                    record4, destination4 = record['id'], record['destination']
                elif record['type'] == 'AAAA':
                    record6, destination6 = record['id'], record['destination']
        return record4, destination4, record6, destination6

    def fetch_dns_records(self, domain: str) -> dict[str, Any]:
        return self._request('infoDnsRecords', domainname=domain)

    def update_dns_records(self, domain: str, hostname: str, record4: str|None, destination4: str|None, record6: str|None, destination6: str|None) -> None:
        recordset = []
        if record4 and destination4:
            recordset.append(dict(id=record4, hostname=hostname, destination=destination4, type='A'))
        if record6 and destination6:
            recordset.append(dict(id=record6, hostname=hostname, destination=destination6, type='AAAA'))
        self.update_dns_recordset(domain, recordset)

    def update_dns_recordset(self, domain: str, records: list[dict[str, Any]]) -> dict[str, Any]:
        return self._request('updateDnsRecords', domainname=domain, dnsrecordset=dict(dnsrecords=records))

    def _request(self, action: str, **params: Any) -> Any:
        params = dict(params, customernumber=self.customer_number, apikey=self.key)
        if self.session:
            params.update(apisessionid=self.session)
        response = requests.post(self.endpoint, json=dict(action=action, param=params))
        response.raise_for_status()
        data = response.json()
        if data.get('status') != 'success':
            raise RuntimeError(f'netcup api error: {json.dumps(data)}')
        return data


def log(message: str) -> None:
    print(message, file=sys.stderr)


if __name__ == '__main__':
    main()
