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
import argparse

parser = argparse.ArgumentParser(description='Links nginx reverse proxying with Cloudflare')
parser.add_argument('-p', '--proxy', action='store_true', dest='proxy', default=False, help='Enables '
                                                                                            'Cloudflare '
                                                                                            'Proxying on every '
                                                                                            'subdomain')
parser.add_argument('-y', '--yes', action='store_true', dest='inter', default=False, help='Run program '
                                                                                          'non-interactively')
parser.add_argument('-r', '--rootless', action='store_true', dest='perm', default=False, help='If you\'re sure '
                                                                                              'that your '
                                                                                              'config file is '
                                                                                              'readable by you '
                                                                                              '(the user), '
                                                                                              'skips '
                                                                                              'permission '
                                                                                              'check')
args = parser.parse_args()


def envprocess():
    """
    Grab credentials off the environnement variables and test the authentication to the Cloudflare API
    :return str conf_env: Extracted config file path
    :return str cf_token: Raw CF API token
    :return bool proxy: Enables (if True) Cloudflare's proxying
    :raise LookupError: If the API call fails
    :raise EnvironmentError: If no variable if provided
    :raise RuntimeError: If a Global API key is provided (this is the case when an email is provided)
    """
    cf_token = os.environ.get('CF_API_KEY')
    cf_email = os.environ.get('CF_API_EMAIL')
    conf_env = os.environ.get('CONF')
    if cf_token is not None and cf_email is None:
        try:
            cf = CloudFlare.CloudFlare(token=cf_token)
            zoneinfo = cf.zones.get()
        except CloudFlare.CloudFlareAPIError:
            raise LookupError("The provided API token is not valid ")
        else:
            if os.path.isfile(conf_env):
                if args.proxy is True:
                    print("All records will get Cloudflare's proxying enabled")
                    proxy = True
                    return conf_env, cf_token, proxy
                else:
                    print("No proxying will be enabled")
                    proxy = False
                    return conf_env, cf_token, proxy
    elif cf_token is not None and cf_email is not None:
        raise RuntimeError("For security reasons, entering an API Global key is not supported ")
    else:
        raise EnvironmentError("Variable error, check your variables")


def getperms():
    """
    Checks if the users has sufficient permissions to run the script
    This is done to cope with default nginx config file being only readable by root
    :raise PermissionError: When the script is not ran as root
    """
    if os.geteuid() == 0 or args.perm is True:
        return 0
    else:
        raise PermissionError("Script will not have the sufficient permissions to run")


def config(cfile):
    """
    Process given config file to extract main domain name (the CF's zone_name)
    :param str cfile: Config file path
    :return str raw_domain: Zone Name (main domain)
    :return list domains: Sub-Domains to process
    """
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
    """
    Processes the list of subdomains to strip the main domain
    :param str rdomains: Zone Name (main domain)
    :param list sub: Sub-Domains to process
    :return str rdomain: Main domain stripped of the *
    :return list sub: Processed subdomains, ready to be added
    """
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
    """
    Adds the records to CloudFlare
    :param str token: CF API token
    :param str full: Zone Name
    :param list sub: Subdomains to add
    :param str ip: Public IP
    :param bool proxied: If proxying is enabled
    :return list sub2: List of processed subdomains (duplicated already DNS records are stripped)
    :return object cf_instance: Already declared CF instance
    :return str zone_id: DNS Zone ID
    """
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
    print("Records will be added for subdomains")
    [print(x) for x in sub2]
    for z in sub2:
        dns = {'name': z, 'type': 'A', 'content': ip, 'ttl': '1', 'proxied': bool(proxied)}
        try:
            cf_instance.zones.dns_records.post(zone_id, data=dns)
        except CloudFlare.exceptions.CloudFlareAPIError as e:
            exit('/zones.dns_records.post %s - %d %s - api call failed' % (z, e, e))
        else:
            continue
    return sub2, cf_instance, zone_id


def ip():
    """
    Query seeip.org to grab Public IP
    :return str ip: Given IP adress
    """
    with curl.get('https://ip4.seeip.org/jsonip?') as req:
        if req.status_code == 200:
            response = req.json()['ip']
    try:
        validators.ipv4(response)
    except validators.ValidationFailure:
        print("Auto-query failed, enter your public IP")
        response = input("IP")
    if args.inter is True:
        print("All Good!")
    elif args.inter is False:
        ina = input("Your public IPv4 is %s, is that correct? [ENTER | IP] " % response)
        if ina == '':
            print('All Good!')
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
    """
    Checks if the records had been successfully ran
    :param list subd: List of processed subdomains
    :param object instance: Already declared CF instance
    :param zone_id: DNS Zone ID
    :return: Nothing
    :raise: RuntimeWarning: When record has not been successfully implemented
    """
    if len(subd) == 0:
        print("All records already present, exiting")
        exit(0)
    else:
        for x in subd:
            try:
                params = {'type': 'A', 'name': x}
                r = instance.zones.dns_records.get(zone_id, params=params)
            except CloudFlare.CloudFlareAPIError as e:
                raise RuntimeWarning("Record %s not implemented successfully" % x)
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
