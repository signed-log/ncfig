#!/usr/bin/env python3

"""
    NCFIG, auto-adds reverse proxy records to Cloudflare
    Copyright (C) 2021  Nicolas "stig124" FORMICHELLA

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
"""


import os
import CloudFlare
import validators
import requests as curl
import sys

nginxdir = "/etc/nginx/sites-enabled"


def envprocess():
    try:
        cf_token = os.environ.get('CF_API_KEY')
        cf_email = os.environ.get('CF_API_EMAIL')
        conf_env = os.environ.get('CONF')
    except TypeError:
        raise KeyError("No variables provided")
    if cf_token is not None and cf_email is None:
        try:
            cf = CloudFlare.CloudFlare(token=cf_token)
            zoneinfo = cf.zones.get()
        except CloudFlare.CloudFlareAPIError:
            raise LookupError("The provided API token is not valid ")
        except Exception:
            print("Something else went wrong")
        else:
            if os.path.isfile(conf_env):
                if sys.argv[1:] == '-p':
                    print("All records will get Cloudflare's proxiing enabled")
                    proxy = 1
                    return conf_env, cf_token, proxy
                else:
                    print("No proxiing will be enabled")
                    proxy = 0
                    return conf_env, cf_token, proxy
    elif cf_token is not None and cf_email is not None:
        raise RuntimeError("For security reasons, entering an API Global key is not supported ")
    else:
        raise EnvironmentError("Variable error, check your variables")


def getperms():
    if os.geteuid() == 0:
        return 0
    else:
        raise PermissionError("Script will not have the sufficient permissions to run")


def getconf():
    for files in os.listdir(nginxdir):
        cfile = input("Enter the full path) that you're using for the proxying ")
        if cfile in files or os.path.isfile(cfile):
            print("Using %s as base config file" % cfile)
            return cfile
        else:
            raise FileNotFoundError("Not a valid or non-existant file")


def config(cfile):
    array = []
    domains = []
    fdomains = []
    with open(cfile) as f:
        file = f.readlines()
    for line in file:
        if 'server_name' in line:
            line = line.strip()
            array.append(line)
    for idx, x in enumerate(array):
        x = x.rstrip()
        if "*" in x:
            r = x.split(' ')[1].replace(';', '').rstrip()
            fdomains.append(r)
            raw_domain = r.replace('*.', '')
        elif 'server_name' in x and "*" not in x:
            d = x.split(' ')[1].replace(';', '').rstrip()
            domains.append(d)
            fdomains.append(d)
        else:
            break
    if "*" in fdomains[0] and len(fdomains) == (len(domains) + 1):
        return raw_domain, domains


def cprocess(rdomains, sub):
    process_sub = []
    r = None
    rdomains = rdomains.replace('*.', '')
    replace_pattern = "." + rdomains
    for x in sub:
        r = x.replace(replace_pattern, '')
        process_sub.append(r)
        if len(sub) == len(process_sub):
            sub = process_sub
            return rdomain, sub
        else:
            continue


def cf(token, full, sub, ip, proxied):
    # Creating Zone
    cf_instance = CloudFlare.CloudFlare(token=token)
    zone_name = full
    try:
        r = cf_instance.zones.get(params={'name': zone_name})
    except CloudFlare.CloudFlareAPIError as e:
        exit('/zones.get %s - %d %s' % (zone_name, e, e))
    zone_id = r[0]['id']
    try:
        params = {'type': 'A'}
        r = cf_instance.zones.dns_records.get(zone_id, params=params)
    except CloudFlare.CloudFlareAPIError as e:
        exit('/dns.get %s - %d %s' % (zone_name, e, e))
    else:
        for x in r:
            for idy, y in enumerate(sub):
                if y in x['name']:
                    sub.remove(y)
                    sub2 = list(filter(None, sub))
                else:
                    continue
    print("Records will be added")
    for idz, z in enumerate(sub2):
        a = len(sub2)
        dns = {'name': z, 'type': 'A', 'content': ip, 'ttl': '1', 'proxied': bool(proxied)}
        try:
            cf_instance.zones.dns_records.post(zone_id, data=dns)
        except CloudFlare.exceptions.CloudFlareAPIError as e:
            exit('/zones.dns_records.post %s - %d %s - api call failed' % (z, e, e))
        else:
            continue
    return sub2, cf_instance, zone_id


def ip():
    with curl.get('http://ip-api.com/json/?fields=8192') as req:
        if req.status_code == 200:
            response = req.json()['query']
    try:
        validators.ipv4(response)
    except validators.ValidationFailure:
        print("Auto-query failed, enter your public IP")
        response = input("IP")
    ina = input("Your public IP is %s, is that correct? [ENTER | IP] " % response)
    if ina == '':
        print("All Good!")
    else:
        try:
            validators.ipv4(ina)
        except validators.ValidationFailure:
            print("IP is not a valid IPv4")
            ina = input("Do you want to retry? [ENTER (no) | IP (yes)] ")
            if validators.ipv4(ina) is True:
                response = ina
            else:
                print("Giving up")
                raise RuntimeError()

        else:
            response = ina
    ip = response
    return ip


def cf_check(subd, instance, zone_id):
    for x in subd:
        try:
            params = {'type': 'A', 'name': x}
            r = instance.zones.dns_records.get(zone_id, params=params)
        except CloudFlare.CloudFlareAPIError as e:
            raise RuntimeWarning("Record %s not implanted successfully" % x)
        else:
            continue
    print("The program has ran successfully")
    exit(0)


if __name__ == '__main__':
    getperms()
    cnflocation, cf_token, proxied = envprocess()
    ip = ip()
    rdomain, dom = config(cnflocation)
    rdomain, sub = cprocess(rdomain, dom)
    done, instance, zone_id = cf(cf_token, rdomain, sub, ip, proxied)
    cf_check(done, instance, zone_id)
