"""Actual TCP controls for byte preservation, intervention and bounded cleanup."""
import socket
import threading
import time
import unittest
from impairment import Relay, MAX_FRAME, PROFILES


class ImpairmentChecks(unittest.TestCase):
    def transfer(self, profile, payload, fragments=False):
        listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen(1);listener.settimeout(3)
        errors=[];received=[]
        def echo():
            try:
                peer,_=listener.accept();peer.settimeout(3)
                with peer:
                    value=b''
                    while True:
                        chunk=peer.recv(32768)
                        if not chunk:break
                        value+=chunk
                    received.append(value)
                    peer.sendall(value);peer.shutdown(socket.SHUT_WR)
            except Exception as error:errors.append(error)
        thread=threading.Thread(target=echo);thread.start()
        try:
            with Relay(listener.getsockname()[1],profile,lifetime=4) as relay:
                with socket.create_connection(('127.0.0.1',relay.port),timeout=3) as client:
                    if fragments:
                        for part in (payload[:3],payload[3:17],payload[17:]):client.sendall(part);time.sleep(.005)
                    else:client.sendall(payload)
                    client.shutdown(socket.SHUT_WR);actual=b''
                    while True:
                        chunk=client.recv(32768)
                        if not chunk:break
                        actual+=chunk
                thread.join(timeout=3)
                deadline=time.monotonic()+1
                while not relay.stats['closed'] and time.monotonic()<deadline:time.sleep(.005)
            self.assertFalse(errors,str(errors));self.assertEqual(received,[payload]);self.assertEqual(actual,payload)
            for direction in relay.stats['directions'].values():
                self.assertEqual(direction['frames_received'],payload.count(b'\n'))
                self.assertEqual(direction['frames_forwarded'],payload.count(b'\n'))
                self.assertEqual(direction['bytes_received'],len(payload));self.assertEqual(direction['bytes_forwarded'],len(payload))
            self.assertFalse(relay.thread.is_alive())
            return relay.stats
        finally:
            listener.close();thread.join(timeout=3)
            self.assertFalse(thread.is_alive(),'Owned fixture thread must stop')

    def test_zero_relay_preserves_fragmented_bytes_fifo_and_half_close(self):
        self.transfer('relay_zero',b'{"a":1}\n{"b":"two"}\n{"c":3}\n',True)

    def test_delay_is_applied_in_both_actual_directions(self):
        stats=self.transfer('delay_60',b'{"kind":"fixture"}\n')
        for direction in stats['directions'].values():self.assertGreaterEqual(direction['min_residence_ms'],59.9)

    def test_downstream_batch_groups_real_frames_without_loss(self):
        stats=self.transfer('batch_400',b'one\ntwo\nthree\n')
        self.assertGreaterEqual(stats['directions']['down']['max_frames_per_send_turn'],3)

    def test_schedule_preserves_fifo_even_if_a_later_due_is_earlier(self):
        relay=Relay(12000,'delay_60')
        self.assertEqual(relay.due(1,'up',2,0),2)
        batch=Relay(12000,'batch_400')
        self.assertAlmostEqual(batch.due(.41,'down',0,0),.8)
        self.assertAlmostEqual(batch.due(.41,'up',0,0),.41)

    def test_oversize_stream_fails_closed_without_unbounded_buffer(self):
        listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen(1);listener.settimeout(2);peer=None
        relay=Relay(listener.getsockname()[1],lifetime=3)
        try:
            with self.assertRaisesRegex(ValueError,'Unterminated relay frame'):
                with relay:
                    with socket.create_connection(('127.0.0.1',relay.port),timeout=2) as client:
                        client.sendall(b'x'*MAX_FRAME);peer,_=listener.accept()
                        deadline=time.monotonic()+2
                        while not relay.stats['closed'] and time.monotonic()<deadline:time.sleep(.01)
            self.assertFalse(relay.thread.is_alive())
        finally:
            if peer:peer.close()
            listener.close()

    def bad_stream(self, payload, expected):
        listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen(1);listener.settimeout(2);peer=None
        relay=Relay(listener.getsockname()[1],lifetime=3)
        try:
            with self.assertRaisesRegex(ValueError,expected):
                with relay:
                    with socket.create_connection(('127.0.0.1',relay.port),timeout=2) as client:
                        client.sendall(payload);client.shutdown(socket.SHUT_WR);peer,_=listener.accept()
                        deadline=time.monotonic()+2
                        while not relay.stats['closed'] and time.monotonic()<deadline:time.sleep(.005)
            self.assertFalse(relay.thread.is_alive())
        finally:
            if peer:peer.close()
            listener.close()

    def test_truncated_frame_fails_instead_of_silently_dropping_bytes(self):
        self.bad_stream(b'partial','EOF inside a newline frame')

    def test_excess_frames_fail_closed_at_queue_bound(self):
        self.bad_stream(b'a\n'*129,'Scheduled queue limit')

    def test_disabled_delay_mutant_is_detected_by_real_observation(self):
        original=PROFILES['delay_60']['delay_ms']
        try:
            PROFILES['delay_60']['delay_ms']=0
            stats=self.transfer('delay_60',b'one\n')
            with self.assertRaises(AssertionError):
                self.assertTrue(all(d['min_residence_ms']>=59.9 for d in stats['directions'].values()))
        finally:PROFILES['delay_60']['delay_ms']=original

    def test_unused_relay_stops_promptly(self):
        before=time.monotonic()
        with Relay(12000,lifetime=2) as relay:pass
        self.assertFalse(relay.thread.is_alive());self.assertLess(time.monotonic()-before,1)

    def test_invalid_configuration_never_binds(self):
        for port in (True,80,65536,'1234'):
            with self.assertRaises(ValueError):Relay(port)
        with self.assertRaises(ValueError):Relay(12000,'arbitrary')
        for lifetime in (True,0,float('nan'),121):
            with self.assertRaises(ValueError):Relay(12000,lifetime=lifetime)


if __name__=='__main__':unittest.main()
