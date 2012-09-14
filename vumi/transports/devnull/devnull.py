# -*- test-case-name: vumi.transports.devnull.tests.test_devnull -*-
import random
import uuid

from vumi import log

from vumi.transports.base import Transport
from vumi.message import TransportUserMessage

from twisted.internet.defer import inlineCallbacks


class DevNullTransport(Transport):
    """
    DevNullTransport for messages that need fake delivery to networks.
    Useful for testing.

    Configuration parameters:

    :param transport_type str:
        The transport type to emulate, defaults to sms.
    :param failure_rate float:
        How many messages should be treated as failures.
        Float value between 0.0 and 1.0.
    :param reply_rate float:
        For how many messages should we generate a reply?
        Float value between 0.0 and 1.0.
    :param reply_copy str:
        What copy should be sent as the reply, defaults to echo-ing the content
        of the outbound message.
    """

    def validate_config(self):
        self.transport_type = self.config.get('transport_type', 'sms')
        self.failure_rate = float(self.config['failure_rate'])
        self.reply_rate = float(self.config['reply_rate'])
        self.reply_copy = self.config.get('reply_copy')

    def setup_transport(self):
        pass

    def teardown_transport(self):
        pass

    @inlineCallbacks
    def handle_outbound_message(self, message):
        dr = ('failed' if random.random() < self.failure_rate
                else 'delivered')
        log.info('%(dr)s: %(from_addr)s -> %(to_addr)s: %(content)s' % {
            'dr': dr,
            'from_addr': message['from_addr'],
            'to_addr': message['to_addr'],
            'content': message['content'],
            })
        yield self.publish_ack(message['message_id'],
            sent_message_id=uuid.uuid4().hex)
        yield self.publish_delivery_report(message['message_id'], dr)
        if random.random() < self.reply_rate:
            yield self.publish_message(
                message_id=uuid.uuid4().hex,
                content=self.reply_copy or message['content'],
                to_addr=message['from_addr'],
                from_addr=message['to_addr'],
                provider='devnull',
                session_event=TransportUserMessage.SESSION_NONE,
                transport_type=self.transport_type,
                transport_metadata={})