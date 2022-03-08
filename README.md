# netcup-dyndns

A simple Python script that dynamically updates DNS records hosted by [Netcup](https://netcup.de/).

# Setup

a) With [pipx](https://github.com/pypa/pipx/).

~~~ bash
pipx install 'git+https://github.com/dadevel/netcup-dyndns.git@main'
~~~

b) With `pip`.

~~~ bash
pip3 install --user --upgrade 'git+https://github.com/dadevel/netcup-dyndns.git@main'
~~~

c) As standalone script.

~~~ bash
curl -o ~/.local/bin/netcup-dyndns https://raw.githubusercontent.com/dadevel/netcup-dyndns/main/netcupdyndns/main.py
chmod +x ~/.local/bin/netcup-dyndns
~~~

# Usage

Configuration is done via environment variables.

Variable | Description
---------|------------
`NETCUP_CUSTOMER_NUMBER` | your customer number, e.g. `123456`
`NETCUP_API_KEY` | your API key
`NETCUP_API_PASSWORD` | your API password
`NETCUP_DOMAIN` | your DNS zone, e.g. `example.com`
`NETCUP_HOSTNAME` | the hostname of your subdomain, e.g. `blog` if your subdomain is `blog.example.com`
`NETCUP_DISABLE_IPV6` | no `AAAA` record will be created if `true`

To generate an API key and password go to your [Customer Control Panel](https://www.customercontrolpanel.de/daten_aendern.php?sprung=api).

A Systemd timer and an accompanying service is available [here](./extras/systemd/).
