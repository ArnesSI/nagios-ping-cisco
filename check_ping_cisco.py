#!/usr/bin/env python
#
# MIT License
#
# Copyright (c) 2016 Matej Vadnjal <matej@arnes.si>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
#
# Check ping from Cisco IOS device.
#
# Example call:
# check_ping_cisco.py -H myrouter -l admin -p admin --dest 8.8.8.8 --threshold metric=rta,ok=0.0..2.0,warning=2.0..4.0,critical=10.0..inf --threshold metric=pl,ok=0..1,warning=1..20,critical=20..100 --count 10
#

from pynag.Plugins import PluginHelper, ok, warning, critical, unknown
import re
import netmiko

def ping(device, destination, source=None, ttl=255, timeout=2, size=100, count=5, debug=False):
    result = {}
    command = 'ping %s' % destination
    if size:
        command += ' size %d' % size
    if count:
        command += ' repeat %d' % count
    if timeout is not None:
        command += ' timeout %d' % timeout
    if source:
        command += ' source %s' % source
    if debug:
        print 'CMD: %s' % command
    output = device.send_command(command)
    if '\n% ' in output or output.startswith('% '):
        result['error'] = output
    else:
        result['success'] = {
            'probes_sent': 0,
            'probes_sent': 0,
            'packet_loss': 0,
            'rtt_min': 0.0,
            'rtt_max': 0.0,
            'rtt_avg': 0.0,
            'rtt_stddev': 0.0,
            'results': []
        }
        # Success rate is 10 percent (1/10), round-trip min/avg/max = 1/1/1 ms
        # Success rate is 0 percent (0/5)
        probes = re.search(r'.*Success rate .+ \((?P<probes_received>\d+)\/(?P<probes_sent>\d+)\)', output, re.MULTILINE)
        if probes:
            probes_sent = int(probes.group('probes_sent'))
            probes_received = int(probes.group('probes_received'))
            result['success']['probes_sent'] = probes_sent
            result['success']['packet_loss'] = int((probes_sent - probes_received)/float(probes_sent)*100)
            results_array = []
            for i in range(probes_received):
                results_array.append({'ip_address': unicode(destination), 'rtt': 0.0})
            result['success'].update({'results': results_array})
        rtt = re.search(r'.* = (?P<rtt_min>\d+)\/(?P<rtt_avg>\d+)\/(?P<rtt_max>\d+).*', output, re.MULTILINE)
        if rtt:
            result['success']['rtt_min'] = float(rtt.group('rtt_min'))
            result['success']['rtt_avg'] = float(rtt.group('rtt_avg'))
            result['success']['rtt_max'] = float(rtt.group('rtt_max'))
    return result


helper = PluginHelper()
helper.parser.add_option("-H", help="Host to connect to (default: %default)", dest="host", default='localhost')
helper.parser.add_option("-l", help="Username to login with", dest="username")
helper.parser.add_option("-p", help="Password to login with", dest="password")
helper.parser.add_option("--dest", help="Destination to ping (default: %default)", dest="destination", default="localhost")
helper.parser.add_option("--source", help="Source address or interface to ping from", dest="source")
#helper.parser.add_option("--ttl", help="TTL to set (default: %default)", dest="ttl", default=255) # not implemented on Cisco IOS
helper.parser.add_option("--probe-timeout", help="Timeout to wait for response (default: %default)", dest="probe_timeout", default=2, type="int")
helper.parser.add_option("--size", help="Packet size (default: %default)", dest="size", default=100, type="int")
helper.parser.add_option("--count", help="Packets to send (default: %default)", dest="count", default=5, type="int")
helper.parse_arguments()

conf = {
    'device_type':'cisco_ios',
    'host':helper.options.host,
    'username':helper.options.username,
    'password':helper.options.password
}
device = netmiko.ConnectHandler(**conf)
result = ping(
    device=device,
    destination=helper.options.destination,
    source=helper.options.source or None,
    #ttl=helper.options.,
    timeout=helper.options.probe_timeout,
    size=helper.options.size,
    count=helper.options.count,
    debug=helper.options.show_debug
)
if helper.options.show_debug:
    print result

if 'error' in result:
    helper.status(critical)
    helper.add_summary('%s: unable to ping' % helper.options.destination)
    helper.add_long_output(result['error'])
elif 'success' in result:
    success = result['success']
    helper.status(ok)
    helper.add_summary('%s: rta %.1fms, pl %d%%' % (helper.options.destination, success['rtt_avg'], success['packet_loss']))
    helper.add_metric('pl', success['packet_loss'], uom='%')
    helper.add_metric('rta', success['rtt_avg'], uom='ms')
else:
    helper.status(unknown)
    helper.add_summary('Unrecognized result from ping function')
    helper.add_long_output(str(result))

helper.check_all_metrics()
helper.exit()
