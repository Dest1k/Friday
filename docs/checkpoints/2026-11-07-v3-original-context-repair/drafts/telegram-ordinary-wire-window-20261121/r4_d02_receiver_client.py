"""Owned R4 client for the gateway's ordinary D02 receiver control."""

import math
import os
import re
import time
from uuid import uuid4


VERB = 'ordinary-d02-receiver'
SCHEMA = 'frw.gateway.d02-owned-receiver-control.v1'
OPTIONS_SCHEMA = 'frw.Root.D02.receiver-options.v1'
ARM_SECONDS = 25.0
READBACK_SECONDS = 1.5
RECEIPT_FIELDS = {
    'state', 'claim_sha256', 'generation', 'first_offset', 'armed_monotonic', 'expires_monotonic',
}
# The reviewed R4 child checks before GET preflight, after durable send intent,
# and immediately before wire. Each check needs a new positive readback.
CONSUMER_CONFIRMATIONS = 3


def _monotonic_number(value):
    return type(value) in (int, float) and math.isfinite(value)


class ReceiverWindow:
    """Use the reviewed driver's exact identity, options and installed helpers.

    The driver supplies gateway.control_socket.query_gateway_control and
    agent.deadline.run_bounded_sync from its pinned installed sources.
    """

    def __init__(self, actor, *, workdir, home, gateway, boot_id, receiver_options, role,
                 query_gateway_control, run_bounded_sync):
        actor.need(role in ('parent', 'consumer'), 'R4_RECEIVER_CONTROL_ROLE_REQUIRED')
        actor.need(type(gateway) is dict and set(gateway) == {'pid', 'start_time'}
                   and all(type(n) is int and n > 0 for n in gateway.values())
                   and type(boot_id) is str
                   and re.fullmatch('[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', boot_id) is not None,
                   'R4_RECEIVER_CONTROL_GATEWAY_PIN_REQUIRED')
        actor.need(actor.reference_shape(receiver_options), 'R4_RECEIVER_CONTROL_OPTIONS_PIN_REQUIRED')
        self.actor = actor
        self.work = actor.canonical_path(str(workdir))
        self.work_identity = actor.protected_directory(self.work)[:5]
        self.home = actor.canonical_path(str(home))
        self.gateway = dict(gateway)
        self.boot_id = boot_id
        self.options = dict(receiver_options)
        self.role = role
        self.query = query_gateway_control
        self.bounded = run_bounded_sync
        self.consumer_confirmations = 0

    def _named_document(self, ref, filename):
        actor = self.actor
        actor.need(ref == actor.fileref(self.work / filename), 'R4_RECEIVER_CONTROL_PROOF_CHANGED')
        value = actor.doc(ref)
        actor.need(type(value) is dict, 'R4_RECEIVER_CONTROL_PROOF_REQUIRED')
        return value

    def _intent(self, intent_ref):
        intent = self._named_document(intent_ref, 'receiver-arm-intent.json')
        claim = self._named_document(intent['claim'], 'claim.json')
        self.actor.need(intent['no_retry'] is True and claim['no_retry'] is True
                        and all(intent[key] == claim[key] for key in
                                ('parent', 'binding', 'run_id', 'scenario_sha256')),
                        'R4_RECEIVER_CONTROL_CLAIM_CHANGED')
        return intent

    def _owner(self, intent, arm_ref=None):
        actor = self.actor
        owner = actor.kernel(os.getpid())
        parent = intent['parent']
        actor.need(owner['boot_id'] == parent['boot_id'] == self.boot_id, 'R4_RECEIVER_CONTROL_BOOT_CHANGED')
        clock_path = self.work / 'clock.json'
        if self.role == 'parent':
            actor.need(owner == parent and not os.path.lexists(clock_path), 'R4_RECEIVER_CONTROL_PARENT_CHANGED')
            return None, math.inf

        clock_ref = actor.fileref(clock_path)
        clock = actor.doc(clock_ref)
        invocation = actor.doc(actor.fileref(self.work / 'consumer-invocation.json'))
        start, end = clock['started_monotonic'], clock['deadline_monotonic']
        actor.need(parent == actor.kernel(os.getppid())
                   and clock['schema'] == 'frw.Root.F07.finite-operation-clock.v1'
                   and clock['status'] == 'ROOT_BOUND_FUTURE_OPERATION'
                   and clock['old_effects_clocks_preserved'] is True
                   and clock['receiver_arm'] == arm_ref
                   and all(_monotonic_number(value) for value in (start, end))
                   and 0 <= start <= time.monotonic() < end
                   and invocation['schema'] == 'frw.Root.F07.one-ordinary-consumer-invocation.v1'
                   and invocation['clock'] == clock_ref and invocation['consumer'] == owner
                   and invocation['driver_binding'] == intent['binding'] and invocation['no_retry'] is True
                   and clock['run_id'] == invocation['run_id'] == intent['run_id']
                   and clock['scenario_sha256'] == intent['scenario_sha256'],
                   'R4_RECEIVER_CONTROL_CONSUMER_CHANGED')
        return clock_ref, end

    def _identity_current(self):
        actor = self.actor
        actor.need(actor.protected_directory(self.work)[:5] == self.work_identity,
                   'R4_RECEIVER_CONTROL_WORKDIR_CHANGED')
        actor.need(actor.kernel(self.gateway['pid']) == dict(self.gateway, boot_id=self.boot_id),
                   'R4_RECEIVER_CONTROL_GATEWAY_CHANGED')

    def _request(self, action, filename, intent_ref, proof, deadline):
        actor = self.actor
        self._identity_current()
        options = actor.doc(self.options)
        actor.need(type(options) is dict
                   and set(options) == {'schema', 'principal', 'profile', 'rights', 'observer_expires_monotonic'}
                   and options['schema'] == OPTIONS_SCHEMA,
                   'R4_RECEIVER_CONTROL_OPTIONS_REQUIRED')
        created = time.monotonic()
        expires = min(deadline, created + (ARM_SECONDS if action == 'arm' else READBACK_SECONDS))
        actor.need(created < expires, 'R4_RECEIVER_CONTROL_REQUEST_EXPIRED')
        query_id = uuid4().hex
        request = actor.new(self.work / filename, actor.encoded(dict(
            schema=SCHEMA, operator='Root', action=action, query_id=query_id, boot_id=self.boot_id,
            gateway=self.gateway, created_monotonic=created, expires_monotonic=expires,
            arm_intent=intent_ref, receiver_options=self.options, proof=proof,
        )))
        params = {'root_request': {key: request[key] for key in ('path', 'sha256')}}

        def query_once():
            remaining = expires - time.monotonic()
            if remaining > 0:
                return self.query(self.home, VERB, params=params, timeout=remaining)
            return None

        remaining = expires - time.monotonic()
        actor.need(remaining > 0, 'R4_RECEIVER_CONTROL_REQUEST_EXPIRED')
        outcome = self.bounded(query_once, remaining, label='r4-d02-receiver-control')
        actor.need(outcome.timed_out is False, 'R4_RECEIVER_CONTROL_RESPONSE_UNKNOWN')
        response = outcome.value
        self._identity_current()
        actor.need(time.monotonic() < expires and type(response) is dict,
                   'R4_RECEIVER_CONTROL_RESPONSE_UNKNOWN')
        actor.need(response.get('accepted') is True and response.get('action') == action
                   and response.get('query_id') == query_id
                   and response.get('state') == ('CUTOFF_BOUND' if action == 'cutoff' else 'ARMED'),
                   'R4_RECEIVER_CONTROL_RESPONSE_NOT_CONFIRMED')
        return response, created

    def _receipt(self, value, claim_sha256, *, earliest=0):
        now = time.monotonic()
        self.actor.need(type(value) is dict and set(value) == RECEIPT_FIELDS
                        and value['state'] == 'ARMED' and value['claim_sha256'] == claim_sha256
                        and type(value['generation']) is int and value['generation'] > 0
                        and type(value['first_offset']) is int and 0 <= value['first_offset'] < 2**63
                        and all(_monotonic_number(value[key]) for key in ('armed_monotonic', 'expires_monotonic'))
                        and earliest <= value['armed_monotonic'] <= now < value['expires_monotonic']
                        <= value['armed_monotonic'] + 600,
                        'R4_RECEIVER_CONTROL_RECEIPT_NOT_CONFIRMED')
        return value

    def _arm_record(self, arm_ref):
        record = self._named_document(arm_ref, 'receiver-arm.json')
        intent = self._intent(record['intent'])
        self.actor.need(record['no_retry'] is True and all(record[key] == intent[key] for key in
                        ('claim', 'parent', 'run_id', 'scenario_sha256')), 'R4_RECEIVER_CONTROL_ARM_CHANGED')
        receipt = self._receipt(record['receipt'], intent['claim']['sha256'])
        return record['intent'], intent, receipt

    def arm(self, intent_ref):
        self.actor.need(self.role == 'parent', 'R4_RECEIVER_CONTROL_PARENT_REQUIRED')
        intent = self._intent(intent_ref)
        self._owner(intent)
        response, created = self._request('arm', 'receiver-control-arm.json', intent_ref, None, math.inf)
        return self._receipt(response.get('receipt'), intent['claim']['sha256'], earliest=created)

    def confirm(self, arm_ref):
        try:
            actor = self.actor
            intent_ref, intent, expected = self._arm_record(arm_ref)
            _, deadline = self._owner(intent, arm_ref)
            index = self.consumer_confirmations
            if self.role == 'parent':
                name = 'receiver-control-confirm-parent.json'
            else:
                actor.need(index < CONSUMER_CONFIRMATIONS, 'R4_RECEIVER_CONTROL_CONFIRMATIONS_EXHAUSTED')
                name = f'receiver-control-confirm-consumer-{index + 1}.json'
            response, _ = self._request('confirm', name, intent_ref, arm_ref,
                                         min(deadline, expected['expires_monotonic']))
            actual = self._receipt(response.get('receipt'), intent['claim']['sha256'])
            actor.need(actor.encoded(actual) == actor.encoded(expected),
                       'R4_RECEIVER_CONTROL_ARM_RECEIPT_CHANGED')
            if self.role == 'consumer':
                self.consumer_confirmations += 1
            return True
        except Exception:
            return False

    def bind_cutoff(self, arm_ref, proof_ref):
        try:
            actor = self.actor
            actor.need(self.role == 'consumer' and self.consumer_confirmations == CONSUMER_CONFIRMATIONS,
                       'R4_RECEIVER_CONTROL_OWNED_WIRE_READBACK_REQUIRED')
            intent_ref, intent, receipt = self._arm_record(arm_ref)
            clock_ref, deadline = self._owner(intent, arm_ref)
            proof = self._named_document(proof_ref, 'receiver-cutoff-intent.json')
            cutoff = proof['receiver_monotonic_cutoff']
            actor.need(proof['arm'] == arm_ref and proof['clock'] == clock_ref and proof['no_retry'] is True
                       and all(proof[key] == intent[key] for key in ('run_id', 'scenario_sha256'))
                       and _monotonic_number(cutoff), 'R4_RECEIVER_CONTROL_CUTOFF_PROOF_CHANGED')
            self._request('cutoff', 'receiver-control-cutoff.json', intent_ref, proof_ref,
                          min(deadline, receipt['expires_monotonic'], cutoff))
            return True
        except Exception:
            return False
