import os
from optparse import OptionParser
from downpour2.core.daemon import Daemon


def main():

    parser = OptionParser()
    parser.add_option("-c", "--config", default="/etc/downpour.cfg",
                      dest="config", help="Configuration file")
    parser.add_option("-a", "--address", dest="interface",
                      help="Name or IP address to listen on")
    parser.add_option("-p", "--port", dest="port", type="int",
                      help="Port to listen on for web interface")
    parser.add_option("--pid-file", default="/var/run/downpour.pid", dest="pidfile",
                      help="File to write daemon's PID to")
    parser.add_option("--stderr", default="/dev/null", dest="stderr",
                      help="File for STDERR output")
    parser.add_option("--stdout", default="/dev/null", dest="stdout",
                      help="File for STDOUT output")
    parser.add_option("-u", "--user", dest="user", help="User to run as")
    parser.add_option("-g", "--group", dest="group", help="Group to run as")
    parser.add_option("--umask", default=077, dest="umask", type="int",
                      help="File creation mask")
    parser.add_option("-d", "--debug", action="store_true", dest="debug",
                      help="Don't detach, and display all output to STDOUT/STDERR")
    (options, args) = parser.parse_args()
    optdict = options.__dict__

    if options.debug:
        optdict['log'] = 'debug'
        from downpour2.core import application
        application.Application(optdict).run()
    else:
        d = Daemon('downpour2.core.application.Application', \
                   pidfile=options.pidfile, user=options.user, group=options.group, \
                   stdout=options.stdout, stderr=options.stderr)
        d.args = (optdict,)
        actions = {
            'start': d.start,
            'stop': d.stop,
            'restart': d.restart
        }
        if len(args):
            if args[0] in actions:
                actions[args[0]]()
            else:
                print "Valid actions: start|stop|restart"
        else:
            d.start()

if __name__ == '__main__':
    main()
