#!/usr/bin/env python3
# encoding: utf-8

#requirements:
# sudo yum install nmap
# sudo pip3 install python-libnmap

import configparser
import psycopg2
import sys
import os
from libnmap.parser import NmapParser

def connect():
    try:
        conn = psycopg2.connect(host=config.get('DATABASE', 'host'),database=config.get('DATABASE', 'database'), user=config.get('DATABASE', 'user'), password=config.get('DATABASE', 'password'))
    except:
        print ("I am unable to connect to the database")
    return conn


def already_exists(ip_address):
    connection = connect()
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM network_model WHERE ip_address = (%s)", (ip_address,))
    exists = cursor.fetchone()
    if exists is None:
        connection.close()
        return False
    else:
        connection.close()
        return True

def is_local_device(ip_address):
    interface = os.popen("ifconfig | grep -B1 " + ip_address +" | grep -o \"^\w*\"").read()
    if interface == "":
        return None
    else:
        return interface

def update(host):
    interface = is_local_device(host.address)
    if interface is not None:
        mac = os.popen("cat /sys/class/net/" + interface.rstrip() + "/address").read()
        mac = mac.rstrip()
    else:
        mac = host.mac

    osp = host.os_match_probabilities()
    op_system = "unknown"
    if osp:
        op_system = osp[0].name
    
    ports = open_ports = services = vulners = ""
    for port in host.get_ports():
        port = str(port) + "\n"
        ports += port
    
    for open_port in host.get_open_ports():
        open_port = str(open_port) + "\n"
        open_ports += open_port
    
    for service in host.services:
        service = str(service)
        index1 = service.find("[")
        index2 = service.rfind("]")
        services += (service[index1 + 1: index2] + "\n")

    for vulner in host.scripts_results:
        vulners += (str(vulner) + "\n")

    connection = connect()
    cursor = connection.cursor()
    cursor.execute("UPDATE network_model set mac_address = (%s), operation_system = (%s), ports = (%s), open_ports = (%s), services = (%s), vulnerabilities = (%s) WHERE ip_address = (%s)", 
    (mac, op_system, ports, open_ports, services, vulners, host.address))

    connection.commit()
    connection.close()
    print("Host with IP address %s updated!" % host.address)


def insert(host):
    ip = host.address
    interface = is_local_device(ip)
    if interface is not None:
        mac = os.popen("cat /sys/class/net/" + interface.rstrip() + "/address").read()
    else:
        mac = host.mac

    osp = host.os_match_probabilities()
    op_system = "unknown"
    if osp:
        op_system = osp[0].name

    ports = open_ports = services = vulners = ""
    for port in host.get_ports():
        port = str(port) + "\n"
        ports += port
    
    for open_port in host.get_open_ports():
        open_ports += (str(open_port) + "\n")
    
    for service in host.services:
        service = str(service)
        index1 = service.find("[")
        index2 = service.rfind("]")
        services += (service[index1 + 1: index2] + "\n")

    for vulner in host.scripts_results:
        vulners += (str(vulner) + "\n")

    connection = connect()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO network_model(ip_address, mac_address, operation_system, ports, open_ports, services, vulnerabilities) VALUES(%s,%s,%s,%s,%s,%s,%s)", 
    (ip, mac, op_system, ports, open_ports, services, vulners))

    connection.commit()
    connection.close()
    print("Host with IP address %s inserted!" % host.address)

# nmap -A -sV --script=vulscan.nse -oX testrun.xml 192.168.0.1/24
#os.system("nmap -A -sV --script=vulscan.nse -oX testrun.xml 192.168.0.1/24")

if len(sys.argv) != 2 or sys.argv[1] == "help":
    print("Available parrameters are:\n")
    print("\"path\" - full path to .xml file to by processed")
    print("\"help\" - to list all available parameters\n")
    sys.exit()

if '.xml' not in sys.argv[1]:
    print("File must be in .xml format generated by nmap tool!")
    sys.exit()

if not os.path.isfile(sys.argv[1]):
    print("Given argument is not a file!")
    sys.exit()


p = NmapParser.parse_fromfile(sys.argv[1])

#read configuration file
config = configparser.ConfigParser()
config.read('/var/www/html/secmon/config/secmon_config.ini')

for host in p.hosts:
    if already_exists(host.address):
        print("Robim UPDATE / EXISTUJE")
        update(host)
    else:
        print("Robim INSERT / NEEXISTUJE")
        insert(host)
