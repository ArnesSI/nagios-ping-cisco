# nagios-ping-cisco
Ping a destination from a Cisco IOS router

This script will login to a Cisco IOS switch or router and preform a ping command.

## Requirements

* [netmiko] (https://github.com/ktbyers/netmiko)
* [pynag] (http://pynag.org/)

If you are using pip, the following command will install all requirements:

    pip install netmiko pynag

## Command line options

    -H HOST               Host to connect to (default: localhost)
    -l USERNAME           Username to login with
    -p PASSWORD           Password to login with
    --dest=DESTINATION    Destination to ping (default: localhost)
    --source=SOURCE       Source address or interface to ping from
    --probe-timeout=PROBE_TIMEOUT
                          Timeout to wait for response (default: 2)
    --size=SIZE           Packet size (default: 100)
    --count=COUNT         Packets to send (default: 5)
    --threshold=range     Thresholds in standard nagios threshold format

The options map to a cisco CLI command as follows:

    ping <DESTINATION> repeat <COUNT> size <SIZE> timeout <PROBE_TIMEOUT> source <SOURCE>

## Example

    check_ping_cisco.py -H myrouter -l admin -p password --dest 8.8.8.8 --threshold metric=rta,ok=0.0..2.0,warning=2.0..4.0,critical=10.0..inf --threshold metric=pl,ok=0..1,warning=1..20,critical=20..100 --count 10

This command will ping Google's DNS server from myrouter with 10 packets. The threshold are:


 | OK | Warning | Critical
------- | ------- | ------- | --------
**Average round trip time (rta)** | 0 to 2 ms | 2 to 4 ms | above 4 ms
**Packet loss (pl)** | 0 to 1 % | 1 to 20 | above 20 %

## Icinga or Nagios configuration

This check needs login credentials to login to a router. It is recomended that you store this info in the [resource.cfg file] (http://docs.icinga.org/latest/en/sample-resource.html).

Define a check command:

    define command {
                    command_name                          check_ping_cisco
                    command_line                          $USER10$/check_ping_cisco.py -H $ARG1$ -l $USER21$ -p $USER22$ --dest $ARG2$ --threshold metric=rta,ok=0.0..10.0,warning=10.0..40.0,critical=40.0..inf --threshold metric=pl,ok=0..1,warning=1..25,critical=25..100
    }

Use the command in a service or host definition:

    define service {
                    host_name               myrouter
                    service_description     google_dns
                    check_command           check_ping_cisco!$HOSTADDRESS$!8.8.8.8
    }
