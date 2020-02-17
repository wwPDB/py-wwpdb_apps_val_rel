#
# File:  ValidationServiceHandler (adapted from DetachedMessageConsumerExample.py)
# Date:  9-Sep-2016
#
#  Contolling wrapper for validation service consumer client -
#
#  Updates:
#       23-Sep-2016 jdw integrated with val_ws_server package
#       23-Sep-2016 jdw replace deprecated OptionParser
#       10-Jul-2018 ep  use default connection URL instead of SSL exclusive
#
##

import sys
import os
import platform
import time
import json
import logging


try:
    from argparse import ArgumentParser as ArgParser
except ImportError:
    from optparse import OptionParser as ArgParser

# from optparse import OptionParser

from wwpdb.utils.detach.DetachedProcessBase import DetachedProcessBase
from wwpdb.utils.message_queue.MessageConsumerBase import MessageConsumerBase
from wwpdb.utils.message_queue.MessageQueueConnection import MessageQueueConnection
from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId
from wwpdb.apps.val_rel.config.ValConfig import ValConfig
from wwpdb.apps.val_rel.ValidateRelease import (
    runValidation,
)


# from wwpdb.apps.val_ws_server.validate.Validate import Validate

logger = logging.getLogger()
logging.basicConfig(
    level=logging.INFO,
    format="\n%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s",
)
logging.getLogger("pika").setLevel(logging.INFO)


class MessageConsumer(MessageConsumerBase):
    def __init__(self, amqpUrl):
        super(MessageConsumer, self).__init__(amqpUrl)

    def workerMethod(self, msgBody, deliveryTag=None):
        try:
            logger.debug("Message body %r", msgBody)
            pD = json.loads(msgBody)
        except Exception as e:
            logger.error("Message format error - discarding %r", str(e))
            return False
        #
        successFlag = True
        try:
            logger.info("Message body %r", pD)
            runValidation().run_process(pD)
        except Exception as e:
            logger.exception("Failed service execution %r", str(e))

        return successFlag


class MessageConsumerWorker(object):
    def __init__(self, siteID):
        self.__siteID = siteID
        self.__setup()

    def __setup(self):
        mqc = MessageQueueConnection()
        url = mqc._getDefaultConnectionUrl()
        self.__mc = MessageConsumer(amqpUrl=url)
        vc = ValConfig(self.__siteID)
        self.__mc.setQueue(queueName=vc.queue_name, routingKey=vc.routing_key)
        self.__mc.setExchange(exchange=vc.exchange, exchangeType="topic")
        #

    def run(self):
        """  Run async consumer
        """
        startTime = time.time()
        logger.info("Starting ")
        try:
            try:
                logger.info("Run consumer worker starts")
                self.__mc.run()
            except KeyboardInterrupt:
                self.__mc.stop()
        except Exception as e:
            logger.exception("MessageConsumer failing %r", str(e))

        endTime = time.time()
        logger.info("Completed (%f seconds)", (endTime - startTime))

    def suspend(self):
        logger.info("Suspending consumer worker... ")
        self.__mc.stop()


class MyDetachedProcess(DetachedProcessBase):
    """  This class implements the run() method of the DetachedProcessBase() utility class.

         Illustrates the use of python logging and various I/O channels in detached process.
    """

    def __init__(
            self,
            pidFile="/tmp/DetachedProcessBase.pid",
            stdin=os.devnull,
            stdout=os.devnull,
            stderr=os.devnull,
            wrkDir="/",
            siteID=None,
            gid=None,
            uid=None
    ):
        super(MyDetachedProcess, self).__init__(
            pidFile=pidFile,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            wrkDir=wrkDir,
            gid=gid,
            uid=uid,
        )
        self.__mcw = MessageConsumerWorker(siteID)

    def run(self):
        logger.info("STARTING detached run method")
        self.__mcw.run()

    def suspend(self):
        logger.info("SUSPENDING detached process")
        try:
            self.__mcw.suspend()
        except Exception as e:
            logger.error("SUSPENDING failed %r", str(e))


def main():
    # adding a conservative permission mask for this
    # os.umask(0o022)
    #
    #  Setup logging  --
    now = time.strftime("%Y-%m-%d", time.localtime())

    description = "Validation release service handler"
    parser = ArgParser(description=description)
    # py 2/3 issue  for optparse.OptionParser add an `add_argument` method for
    # compatibility with argparse.ArgumentParser
    try:
        parser.add_argument = parser.add_option
    except AttributeError:
        pass

    parser.add_argument(
        "--start",
        default=False,
        action="store_true",
        dest="startOp",
        help="Start consumer client process",
    )
    parser.add_argument(
        "--stop",
        default=False,
        action="store_true",
        dest="stopOp",
        help="Stop consumer client process",
    )
    parser.add_argument(
        "--restart",
        default=False,
        action="store_true",
        dest="restartOp",
        help="Restart consumer client process",
    )
    parser.add_argument(
        "--status",
        default=False,
        action="store_true",
        dest="statusOp",
        help="Report consumer client process status",
    )

    # parser.add_argument("-v", "--verbose", default=False, action="store_true", dest="verbose", help="Enable verbose output")
    parser.add_argument(
        "--debug",
        default=1,
        type=int,
        dest="debugLevel",
        help="Debug level (default: 1 [0-3]",
    )
    parser.add_argument(
        "--instance",
        default=1,
        type=int,
        dest="instanceNo",
        help="Instance number [1-n]",
    )
    parser.add_argument("--siteID", default=getSiteId(), type=str, help="wwPDB site ID")
    #
    # (options, args) = parser.parse_args()

    options = parser.parse_args()
    if isinstance(options, tuple):
        args = options[0]
    else:
        args = options
    del options

    # siteId = getSiteId(defaultSiteId=None)
    siteId = args.siteID
    cI = ConfigInfo(siteId)

    #    topPath = cI.get('SITE_WEB_APPS_TOP_PATH')
    topSessionPath = cI.get("SITE_WEB_APPS_TOP_SESSIONS_PATH")

    #
    myFullHostName = platform.uname()[1]
    myHostName = str(myFullHostName.split(".")[0]).lower()
    #
    wsLogDirPath = os.path.join(topSessionPath, "rel-val-logs")
    if not os.path.exists(wsLogDirPath):
        os.makedirs(wsLogDirPath)

    #
    pidFilePath = os.path.join(
        wsLogDirPath, myHostName + "_" + str(args.instanceNo) + ".pid"
    )
    stdoutFilePath = os.path.join(
        wsLogDirPath, myHostName + "_" + str(args.instanceNo) + "_stdout.log"
    )
    stderrFilePath = os.path.join(
        wsLogDirPath, myHostName + "_" + str(args.instanceNo) + "_stderr.log"
    )
    wfLogFilePath = os.path.join(
        wsLogDirPath, myHostName + "_" + str(args.instanceNo) + "_" + now + ".log"
    )
    #
    logger = logging.getLogger(name="root")
    logging.captureWarnings(True)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s"
    )
    handler = logging.FileHandler(wfLogFilePath)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    #
    lt = time.strftime("%Y %m %d %H:%M:%S", time.localtime())
    #
    if args.debugLevel > 2:
        logger.setLevel(logging.DEBUG)
    elif args.debugLevel > 0:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.ERROR)
    #
    #
    myDP = MyDetachedProcess(
        pidFile=pidFilePath,
        stdout=stdoutFilePath,
        stderr=stderrFilePath,
        wrkDir=wsLogDirPath,
        siteID=siteId
    )

    if args.startOp:
        sys.stdout.write(
            "+DetachedMessageConsumer() starting consumer service at %s\n" % lt
        )
        logger.info("DetachedMessageConsumer() starting consumer service at %s", lt)
        myDP.start()
    elif args.stopOp:
        sys.stdout.write(
            "+DetachedMessageConsumer() stopping consumer service at %s\n" % lt
        )
        logger.info("DetachedMessageConsumer() stopping consumer service at %s", lt)
        myDP.stop()
    elif args.restartOp:
        sys.stdout.write(
            "+DetachedMessageConsumer() restarting consumer service at %s\n" % lt
        )
        logger.info("DetachedMessageConsumer() restarting consumer service at %s", lt)
        myDP.restart()
    elif args.statusOp:
        sys.stdout.write(
            "+DetachedMessageConsumer() reporting status for consumer service at %s\n"
            % lt
        )
        sys.stdout.write(myDP.status())
    else:
        pass


if __name__ == "__main__":
    main()
