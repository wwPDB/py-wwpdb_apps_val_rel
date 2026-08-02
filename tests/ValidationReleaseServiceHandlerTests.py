import unittest
from unittest.mock import MagicMock, patch

from wwpdb.apps.val_rel.service.ValidationReleaseServiceHandler import (
    MessageConsumer,
    MessageConsumerWorker,
    MessageSubscriber,
    MessageSubscriberWorker,
    MyDetachedProcess,
)

SITE_ID = "WWPDB_DEPLOY_TEST"
MODULE = "wwpdb.apps.val_rel.service.ValidationReleaseServiceHandler"


class MessageConsumerWorkerMethodTests(unittest.TestCase):
    """MessageConsumerBase.__init__ only stores plain attributes (no real AMQP
    connection is opened), so constructing MessageConsumer directly is safe.
    Only runValidation -- the real wwpdb.apps.validation entry point this
    calls -- needs mocking.
    """

    def setUp(self) -> None:
        rv_patcher = patch(f"{MODULE}.runValidation")
        self.mock_rv_class = rv_patcher.start()
        self.addCleanup(rv_patcher.stop)
        self.mock_rv = MagicMock()
        self.mock_rv_class.return_value = self.mock_rv

        self.consumer = MessageConsumer(amqpUrl="amqp://unused", priority=False)

    def test_invalid_json_returns_false(self) -> None:
        ret = self.consumer.workerMethod("not json")
        self.assertFalse(ret)
        self.mock_rv_class.assert_not_called()

    def test_valid_json_runs_validation_and_returns_true(self) -> None:
        ret = self.consumer.workerMethod('{"pdbID": "1abc"}')
        self.assertTrue(ret)
        self.mock_rv.run_process.assert_called_once_with({"pdbID": "1abc"})

    def test_run_process_exception_is_caught_and_still_returns_true(self) -> None:
        self.mock_rv.run_process.side_effect = RuntimeError("boom")
        ret = self.consumer.workerMethod('{"pdbID": "1abc"}')
        self.assertTrue(ret)


class MessageSubscriberWorkerMethodTests(unittest.TestCase):
    """Unlike MessageConsumerBase, MessageSubscriberBase.__init__ opens a real
    pika connection immediately (connect() -> channel() -> queue_declare()).
    connect() is patched at the class level so construction stays local/offline;
    only workerMethod's own logic (JSON parsing + runValidation) is exercised.
    """

    def setUp(self) -> None:
        rv_patcher = patch(f"{MODULE}.runValidation")
        self.mock_rv_class = rv_patcher.start()
        self.addCleanup(rv_patcher.stop)
        self.mock_rv = MagicMock()
        self.mock_rv_class.return_value = self.mock_rv

        connect_patcher = patch(
            "wwpdb.utils.message_queue.MessageSubscriberBase.MessageSubscriberBase.connect",
            return_value=MagicMock(),
        )
        connect_patcher.start()
        self.addCleanup(connect_patcher.stop)

        self.subscriber = MessageSubscriber(amqpUrl="amqp://unused")

    def test_invalid_json_returns_false(self) -> None:
        ret = self.subscriber.workerMethod("not json")
        self.assertFalse(ret)
        self.mock_rv_class.assert_not_called()

    def test_valid_json_runs_validation_and_returns_true(self) -> None:
        ret = self.subscriber.workerMethod('{"emdbID": "EMD-1234"}')
        self.assertTrue(ret)
        self.mock_rv.run_process.assert_called_once_with({"emdbID": "EMD-1234"})

    def test_run_process_exception_is_caught_and_still_returns_true(self) -> None:
        self.mock_rv.run_process.side_effect = RuntimeError("boom")
        ret = self.subscriber.workerMethod('{"emdbID": "EMD-1234"}')
        self.assertTrue(ret)


class MessageConsumerWorkerTests(unittest.TestCase):
    """MessageQueueConnection.__init__ touches real site config (getSiteId +
    ConfigInfo), so it's mocked here along with ValConfig and MessageConsumer
    itself, isolating MessageConsumerWorker's own setup/run/suspend logic.
    """

    def setUp(self) -> None:
        mqc_patcher = patch(f"{MODULE}.MessageQueueConnection")
        self.mock_mqc_class = mqc_patcher.start()
        self.addCleanup(mqc_patcher.stop)
        self.mock_mqc = MagicMock()
        self.mock_mqc._getDefaultConnectionUrl.return_value = "amqp://resolved"  # noqa: SLF001 pylint: disable=protected-access
        self.mock_mqc_class.return_value = self.mock_mqc

        vc_patcher = patch(f"{MODULE}.ValConfig")
        mock_vc_class = vc_patcher.start()
        self.addCleanup(vc_patcher.stop)
        self.mock_vc = MagicMock()
        self.mock_vc.queue_name = "the_queue"
        self.mock_vc.routing_key = "the_routing_key"
        self.mock_vc.exchange = "the_exchange"
        mock_vc_class.return_value = self.mock_vc

        mc_patcher = patch(f"{MODULE}.MessageConsumer")
        self.mock_mc_class = mc_patcher.start()
        self.addCleanup(mc_patcher.stop)
        self.mock_mc = MagicMock()
        self.mock_mc_class.return_value = self.mock_mc

    def test_setup_builds_consumer_with_resolved_url_and_priority(self) -> None:
        MessageConsumerWorker(siteID=SITE_ID, priority=True)
        self.mock_mc_class.assert_called_once_with(amqpUrl="amqp://resolved", priority=True)

    def test_setup_configures_queue_and_exchange_from_val_config(self) -> None:
        MessageConsumerWorker(siteID=SITE_ID)
        self.mock_mc.setQueue.assert_called_once_with(queueName="the_queue", routingKey="the_routing_key")
        self.mock_mc.setExchange.assert_called_once_with(exchange="the_exchange", exchangeType="topic")

    def test_run_calls_consumer_run(self) -> None:
        worker = MessageConsumerWorker(siteID=SITE_ID)
        worker.run()
        self.mock_mc.run.assert_called_once()

    def test_run_stops_consumer_on_keyboard_interrupt(self) -> None:
        self.mock_mc.run.side_effect = KeyboardInterrupt()
        worker = MessageConsumerWorker(siteID=SITE_ID)
        worker.run()  # should not raise
        self.mock_mc.stop.assert_called_once()

    def test_run_swallows_generic_exception(self) -> None:
        self.mock_mc.run.side_effect = RuntimeError("boom")
        worker = MessageConsumerWorker(siteID=SITE_ID)
        worker.run()  # should not raise

    def test_suspend_calls_consumer_stop(self) -> None:
        worker = MessageConsumerWorker(siteID=SITE_ID)
        worker.suspend()
        self.mock_mc.stop.assert_called_once()


class MessageSubscriberWorkerTests(unittest.TestCase):
    def setUp(self) -> None:
        mqc_patcher = patch(f"{MODULE}.MessageQueueConnection")
        self.mock_mqc_class = mqc_patcher.start()
        self.addCleanup(mqc_patcher.stop)
        self.mock_mqc = MagicMock()
        self.mock_mqc._getDefaultConnectionUrl.return_value = "amqp://resolved"  # noqa: SLF001 pylint: disable=protected-access
        self.mock_mqc_class.return_value = self.mock_mqc

        ms_patcher = patch(f"{MODULE}.MessageSubscriber")
        self.mock_ms_class = ms_patcher.start()
        self.addCleanup(ms_patcher.stop)
        self.mock_ms = MagicMock()
        self.mock_ms_class.return_value = self.mock_ms

    def test_setup_builds_subscriber_and_adds_exchange(self) -> None:
        MessageSubscriberWorker(siteID=SITE_ID, exchange_name="some_exchange")
        self.mock_ms_class.assert_called_once_with(amqpUrl="amqp://resolved")
        self.mock_ms.add_exchange.assert_called_once_with("some_exchange")

    def test_run_calls_subscriber_run(self) -> None:
        worker = MessageSubscriberWorker(siteID=SITE_ID, exchange_name="some_exchange")
        worker.run()
        self.mock_ms.run.assert_called_once()

    def test_run_stops_subscriber_on_keyboard_interrupt(self) -> None:
        self.mock_ms.run.side_effect = KeyboardInterrupt()
        worker = MessageSubscriberWorker(siteID=SITE_ID, exchange_name="some_exchange")
        worker.run()  # should not raise
        self.mock_ms.stop.assert_called_once()

    def test_run_reraises_generic_exception(self) -> None:
        self.mock_ms.run.side_effect = RuntimeError("boom")
        worker = MessageSubscriberWorker(siteID=SITE_ID, exchange_name="some_exchange")
        with self.assertRaises(Exception):  # noqa: B017
            worker.run()

    def test_suspend_calls_subscriber_stop(self) -> None:
        worker = MessageSubscriberWorker(siteID=SITE_ID, exchange_name="some_exchange")
        worker.suspend()
        self.mock_ms.stop.assert_called_once()


class MyDetachedProcessTests(unittest.TestCase):
    """MessageConsumerWorker/MessageSubscriberWorker are mocked wholesale --
    they each have their own dedicated test coverage above, and mocking them
    avoids MyDetachedProcess's construction reaching real site config again.
    """

    def setUp(self) -> None:
        mcw_patcher = patch(f"{MODULE}.MessageConsumerWorker")
        self.mock_mcw_class = mcw_patcher.start()
        self.addCleanup(mcw_patcher.stop)
        self.mock_mcw = MagicMock()
        self.mock_mcw_class.return_value = self.mock_mcw

        msw_patcher = patch(f"{MODULE}.MessageSubscriberWorker")
        self.mock_msw_class = msw_patcher.start()
        self.addCleanup(msw_patcher.stop)
        self.mock_msw = MagicMock()
        self.mock_msw_class.return_value = self.mock_msw

    def test_no_subscribe_builds_consumer_worker(self) -> None:
        MyDetachedProcess(siteID=SITE_ID, priority=True, subscribe=None)
        self.mock_mcw_class.assert_called_once_with(SITE_ID, priority=True)
        self.mock_msw_class.assert_not_called()

    def test_subscribe_builds_subscriber_worker(self) -> None:
        MyDetachedProcess(siteID=SITE_ID, subscribe="some_exchange")
        self.mock_msw_class.assert_called_once_with(SITE_ID, exchange_name="some_exchange")
        self.mock_mcw_class.assert_not_called()

    def test_run_delegates_to_worker(self) -> None:
        process = MyDetachedProcess(siteID=SITE_ID, subscribe=None)
        process.run()
        self.mock_mcw.run.assert_called_once()

    def test_suspend_delegates_to_worker(self) -> None:
        process = MyDetachedProcess(siteID=SITE_ID, subscribe=None)
        process.suspend()
        self.mock_mcw.suspend.assert_called_once()

    def test_suspend_swallows_worker_exception(self) -> None:
        self.mock_mcw.suspend.side_effect = RuntimeError("boom")
        process = MyDetachedProcess(siteID=SITE_ID, subscribe=None)
        process.suspend()  # should not raise


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
