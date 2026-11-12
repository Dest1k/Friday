"""Explicit SYNTHETIC Python classes/bridge stand-ins; imports no UNO/Office."""
import gc
import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "candidate"))
import conversion_probe as p
import request_args_compat_v2 as compat
import callback_observer_v2 as observer
import readonly_diagnostic as adapter

SENTINEL = "SYNTHETIC_VALUE_MUST_NEVER_BE_SERIALIZED"
CALLS = []


def original(self, name, value):
    CALLS.append((type(self), name))
    if name == "args":
        raise AttributeError(SENTINEL)
    return object.__setattr__(self, name, value)


def generated(name, base=Exception, setter=original):
    # Initialization doesn't perform any synthetic UNO assignment.
    return type(name, (base,), {"__pyunostruct__": name,
                                "__setattr__": setter, "__init__": lambda self: None})


CLASSES = {name: generated(name) for name in compat.REQUEST_NAMES}


def fixture():
    uno = types.ModuleType("synthetic_uno")
    uno._uno_struct__setattr__ = original
    uno.getClass = CLASSES.__getitem__
    return uno, compat.install_request_args_compat(uno)


class Request:
    def __init__(self, action):
        self.action = action
        self.calls = 0

    def getRequest(self):
        self.calls += 1
        return self.action()


class Controls(unittest.TestCase):
    def setUp(self):
        CALLS.clear()
        gc.collect()
        self.uno, self.token = fixture()

    def tearDown(self):
        # Tests that intentionally drifted one setter restore THEIR OWN fixtures.
        self.uno._uno_struct__setattr__ = original
        for cls, old, replacement in self.token:
            cls.__setattr__ = replacement
        compat.restore_request_args_compat(self.token)

    def probe(self, action):
        req = Request(action)
        event = {}
        probe = p.OneShotConversionProbe(self.uno, self.token)
        return probe, req, event

    def test_cached_unknown_error_is_same_object_and_original_once(self):
        cls = generated("com.sun.star.synthetic.CachedFailure")
        obj = cls()
        failure = SystemError(SENTINEL)
        def action():
            try:
                obj.args = (SENTINEL,)
            except AttributeError as cause:
                raise failure from cause
        probe, req, event = self.probe(action)
        with self.assertRaises(SystemError) as caught:
            probe.get_request(req, event)
        self.assertIs(caught.exception, failure)
        self.assertEqual(CALLS, [(cls, "args")])
        self.assertEqual(req.calls, 1)
        self.assertTrue(event["restored"])
        self.assertIs(cls.__dict__["__setattr__"], original)
        self.assertIs(self.uno._uno_struct__setattr__, original)
        self.assertNotIn(SENTINEL, json.dumps(event))
        row = event["setter_events"][0]
        self.assertEqual(row["generated_exception_class_during_conversion"], cls.__pyunostruct__)
        self.assertEqual(event["get_request_error"]["chain"][1]["exception_class"], "builtins.AttributeError")

    def test_accepted_five_setters_untouched(self):
        cls = CLASSES[compat.REQUEST_NAMES[0]]
        replacement = cls.__dict__["__setattr__"]
        obj = cls()
        def action():
            self.assertIs(cls.__dict__["__setattr__"], replacement)
            obj.args = (SENTINEL,)
            return obj
        probe, req, event = self.probe(action)
        self.assertIs(probe.get_request(req, event), obj)
        self.assertEqual(obj.args, (SENTINEL,))
        self.assertEqual(CALLS, [])
        self.assertEqual(event["setter_events"], [])
        self.assertIs(cls.__dict__["__setattr__"], replacement)
        self.assertTrue(event["restored"])

    def test_cold_base_and_struct_cached_without_setter_call_restored(self):
        made = []
        def action():
            base = generated("com.sun.star.synthetic.ColdBase", setter=self.uno._uno_struct__setattr__)
            sub = generated("com.sun.star.synthetic.ColdChild", base, self.uno._uno_struct__setattr__)
            struct = generated("com.sun.star.synthetic.ColdStruct", object, self.uno._uno_struct__setattr__)
            made.extend([base, sub, struct])
            return None
        probe, req, event = self.probe(action)
        probe.get_request(req, event)
        self.assertTrue(all(c.__dict__["__setattr__"] is original for c in made))
        self.assertTrue(event["restored"])
        self.assertEqual(event["setter_events"], [])

    def test_cold_exception_error_detected(self):
        made = []
        def action():
            cls = generated("com.sun.star.synthetic.ColdFailure", setter=self.uno._uno_struct__setattr__)
            made.append(cls)
            cls().args = (SENTINEL,)
        probe, req, event = self.probe(action)
        with self.assertRaises(AttributeError):
            probe.get_request(req, event)
        self.assertEqual(len(event["setter_events"]), 1)
        self.assertIs(made[0].__dict__["__setattr__"], original)

    def test_nonargs_setter_exactly_once(self):
        cls = generated("com.sun.star.synthetic.NonArgs")
        obj = cls()
        probe, req, event = self.probe(lambda: setattr(obj, "field", SENTINEL))
        probe.get_request(req, event)
        self.assertEqual(CALLS, [(cls, "field")])
        self.assertEqual(obj.field, SENTINEL)
        self.assertEqual(event["setter_events"], [])

    def test_foreign_cached_setter_refuses_before_method(self):
        foreign = lambda *args: None
        cls = generated("com.sun.star.synthetic.Foreign", setter=foreign)
        probe, req, event = self.probe(lambda: None)
        try:
            with self.assertRaises(p.ProbeRefused):
                probe.get_request(req, event)
            self.assertEqual(req.calls, 0)
            self.assertIs(cls.__dict__["__setattr__"], foreign)
            self.assertIs(self.uno._uno_struct__setattr__, original)
        finally:
            cls.__setattr__ = original

    def test_global_drift_not_overwritten(self):
        foreign = lambda *args: None
        probe, req, event = self.probe(lambda: setattr(self.uno, "_uno_struct__setattr__", foreign))
        with self.assertRaises(p.ProbeRefused):
            probe.get_request(req, event)
        self.assertIs(self.uno._uno_struct__setattr__, foreign)
        self.assertFalse(event["restored"])
        self.assertIn("HELPER_RESTORE_CAS_DRIFT", event["cleanup_failures"])

    def test_class_drift_not_overwritten_primary_error_retained(self):
        cls = generated("com.sun.star.synthetic.ClassDrift")
        foreign = lambda *args: None
        error = SystemError(SENTINEL)
        def action():
            cls.__setattr__ = foreign
            raise error
        probe, req, event = self.probe(action)
        try:
            with self.assertRaises(SystemError) as caught:
                probe.get_request(req, event)
            self.assertIs(caught.exception, error)
            self.assertIs(cls.__dict__["__setattr__"], foreign)
            self.assertFalse(event["restored"])
        finally:
            cls.__setattr__ = original

    def test_once_and_reentrancy_refused_no_second_getrequest(self):
        event = {}
        probe = p.OneShotConversionProbe(self.uno, self.token)
        req = Request(lambda: probe.get_request(Request(lambda: None), {}))
        with self.assertRaises(p.ProbeRefused):
            probe.get_request(req, event)
        with self.assertRaises(p.ProbeRefused):
            probe.get_request(req, {})
        self.assertEqual(req.calls, 1)
        self.assertTrue(event["restored"])

    def test_token_drift_refuses_without_call(self):
        probe, req, event = self.probe(lambda: None)
        self.token[0][0].__setattr__ = original
        with self.assertRaises(p.ProbeRefused):
            probe.get_request(req, event)
        self.assertEqual(req.calls, 0)
        self.assertIs(self.uno._uno_struct__setattr__, original)

    def test_pre_scan_bound_refuses_without_mutation(self):
        scan = p.generated_classes
        p.generated_classes = lambda: (_ for _ in ()).throw(p.ProbeRefused("SYNTHETIC_BOUND"))
        probe, req, event = self.probe(lambda: None)
        try:
            with self.assertRaises(p.ProbeRefused):
                probe.get_request(req, event)
            self.assertEqual(req.calls, 0)
            self.assertIs(self.uno._uno_struct__setattr__, original)
        finally:
            p.generated_classes = scan

    def test_postscan_failure_restores_known_and_fails_closed(self):
        scan = p.generated_classes
        calls = [0]
        def controlled(**kwargs):
            calls[0] += 1
            if calls[0] == 2:
                raise RuntimeError(SENTINEL)
            return scan(**kwargs)
        p.generated_classes = controlled
        probe, req, event = self.probe(lambda: None)
        try:
            with self.assertRaises(p.ProbeRefused):
                probe.get_request(req, event)
            self.assertIn("POSTSCAN_FAILED", event["cleanup_failures"])
            self.assertFalse(event["restored"])
            self.assertIs(self.uno._uno_struct__setattr__, original)
        finally:
            p.generated_classes = scan

    def test_metadata_failure_preserves_original_setter_and_method_error(self):
        cls = generated("com.sun.star.synthetic.MetadataFailure")
        error = AttributeError(SENTINEL)
        def action():
            try:
                cls().args = (SENTINEL,)
            except AttributeError:
                raise error
        original_metadata = p.exception_metadata
        p.exception_metadata = lambda error: (_ for _ in ()).throw(RuntimeError(SENTINEL))
        probe, req, event = self.probe(action)
        try:
            with self.assertRaises(AttributeError) as caught:
                probe.get_request(req, event)
            self.assertIs(caught.exception, error)
            self.assertEqual(CALLS, [(cls, "args")])
            self.assertTrue(event["metadata_incomplete"])
            self.assertTrue(event["restored"])
        finally:
            p.exception_metadata = original_metadata

    def test_exception_metadata_never_formats_or_gets_values(self):
        class Poison(Exception):
            def __str__(self):raise AssertionError("STR_FORBIDDEN")
            def __repr__(self):raise AssertionError("REPR_FORBIDDEN")
            @property
            def Message(self):raise AssertionError("MESSAGE_FORBIDDEN")
            @property
            def args(self):raise AssertionError("ARGS_FORBIDDEN")
        error = Poison(SENTINEL)
        error.__cause__ = error
        metadata = p.exception_metadata(error)
        self.assertNotIn(SENTINEL, json.dumps(metadata))
        self.assertTrue(metadata["chain_truncated_or_cycle"])

    def test_event_overflow_bounded_and_not_acceptance(self):
        cls = generated("com.sun.star.synthetic.Overflow")
        def action():
            for unused in range(20):
                try:cls().args = (SENTINEL,)
                except AttributeError:pass
        probe, req, event = self.probe(action)
        probe.get_request(req, event)
        self.assertEqual(len(event["setter_events"]), 16)
        self.assertTrue(event["setter_events_overflow"])
        self.assertEqual(event["purpose"], "DIAGNOSTIC_NOT_ACCEPTANCE")
        self.assertNotIn(SENTINEL, json.dumps(event))

    def test_adapter_one_load_strict_properties_close_and_no_acceptance(self):
        class UnoHelper:Base = type("SyntheticBase", (), {})
        class Interaction:pass
        class Prop:pass
        class Doc:
            def close(self, unused):self.closed = True
            def store(self):raise AssertionError("STORE_FORBIDDEN")
        class Desktop:
            calls = 0
            def loadComponentFromURL(inner, url, target, flags, props):
                inner.calls += 1
                inner.props = {v.Name:v.Value for v in props}
                return doc
        doc = Doc();desktop = Desktop()
        result = adapter.observe_one_readonly(uno=self.uno, unohelper=UnoHelper,
                    desktop=desktop, property_value=Prop, interaction_handler_type=Interaction,
                    password_request_type=CLASSES[compat.REQUEST_NAMES[0]],
                    ms_password_request_type=CLASSES[compat.REQUEST_NAMES[1]],
                    error_code_request_type=CLASSES[compat.REQUEST_NAMES[4]], compat_token=self.token,
                    selected_file_url="file:///inputs/native-outputs/retained-source.ott",
                    correct_password=SENTINEL, semantic_check=lambda d: d is doc)
        self.assertEqual(desktop.calls, 1)
        self.assertEqual({k:desktop.props[k] for k in ("Hidden","ReadOnly","AsTemplate","MacroExecutionMode","UpdateDocMode")},
                         {"Hidden":True,"ReadOnly":True,"AsTemplate":False,"MacroExecutionMode":0,"UpdateDocMode":0})
        self.assertTrue(doc.closed)
        self.assertTrue(result["semantic_match"])
        self.assertFalse(result["acceptance_granted"])
        self.assertFalse(result["original_strict_all_pass"])
        self.assertNotIn(SENTINEL, json.dumps(result))

    def test_adapter_path_refused_before_any_load(self):
        with self.assertRaises(ValueError):
            adapter.observe_one_readonly(uno=None, unohelper=None, desktop=None,
                property_value=None, interaction_handler_type=None,password_request_type=None,
                ms_password_request_type=None,error_code_request_type=None,compat_token=None,
                selected_file_url="file:///inputs/../OUTSIDE",correct_password=SENTINEL,semantic_check=None)

    def test_existing_handler_still_reraises_and_refusal_is_not_password_pass(self):
        class UnoHelper:Base=type("SyntheticBase", (), {})
        class Interaction:pass
        handler = observer.make_abort_handler(self.uno, UnoHelper, Interaction,
                   CLASSES[compat.REQUEST_NAMES[0]],CLASSES[compat.REQUEST_NAMES[1]],
                   CLASSES[compat.REQUEST_NAMES[4]],request_probe=p.OneShotConversionProbe(self.uno,self.token))
        failure = SystemError(SENTINEL)
        req = Request(lambda: (_ for _ in ()).throw(failure))
        with self.assertRaises(SystemError) as caught:handler.handle(req)
        self.assertIs(caught.exception,failure)
        self.assertEqual(req.calls,1)
        self.assertEqual(handler.events[0]["phase"],"callback_exception_reraised")
        self.assertFalse(observer.observed_password_refusal_sequence(handler.events,"odt"))
        self.assertNotIn(SENTINEL,json.dumps(handler.events))

    def test_existing_typed_ms_password_abort_positive_unchanged(self):
        class UnoHelper:Base=type("SyntheticBase", (), {})
        class Interaction:pass
        class Abort:
            selected=False
            def select(self):self.selected=True
        class Continuation:
            def queryInterface(self, requested):return abort
        abort=Abort()
        self.uno.getTypeByName=lambda name:name
        payload=CLASSES[compat.REQUEST_NAMES[1]]()
        req=Request(lambda:payload)
        req.getContinuations=lambda:(Continuation(),)
        handler=observer.make_abort_handler(self.uno,UnoHelper,Interaction,
            CLASSES[compat.REQUEST_NAMES[0]],CLASSES[compat.REQUEST_NAMES[1]],CLASSES[compat.REQUEST_NAMES[4]],
            request_probe=p.OneShotConversionProbe(self.uno,self.token))
        handler.handle(req)
        self.assertTrue(abort.selected)
        self.assertTrue(observer.observed_password_refusal_sequence(handler.events,"docx"))
        self.assertFalse(observer.observed_password_refusal_sequence(handler.events,"odt"))
        self.assertEqual(req.calls,1)

    def test_generic_systemerror_without_args_event_stays_unknown(self):
        failure=SystemError(SENTINEL)
        probe,req,event=self.probe(lambda:(_ for _ in ()).throw(failure))
        with self.assertRaises(SystemError) as caught:probe.get_request(req,event)
        self.assertIs(caught.exception,failure)
        self.assertEqual(event["setter_events"],[])
        self.assertEqual(event["origin"],"RETURN_OR_ERROR_CONVERSION_UNKNOWN")
        self.assertTrue(event["restored"])


class FixedResult(unittest.TestResult):
    def __init__(self):super().__init__();self.records=[]
    def addSuccess(self,test):super().addSuccess(test);self.records.append({"test":test._testMethodName,"status":"PASS"})
    def addFailure(self,test,err):self.failures.append((test,"FIXED_METADATA_ONLY"));self.records.append({"test":test._testMethodName,"status":"FAIL","exception_class":err[0].__name__})
    def addError(self,test,err):self.errors.append((test,"FIXED_METADATA_ONLY"));self.records.append({"test":test._testMethodName,"status":"ERROR","exception_class":err[0].__name__})


if __name__ == "__main__":
    result=FixedResult();unittest.defaultTestLoader.loadTestsFromTestCase(Controls).run(result)
    print(json.dumps({"scope":"SYNTHETIC_PYTHON_ONLY_NO_UNO_OR_OFFICE","testsRun":result.testsRun,"records":result.records,"all_pass":result.wasSuccessful()},indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
