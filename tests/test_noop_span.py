# Copyright (c) 2015 Uber Technologies, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from __future__ import absolute_import
import mock
from opentracing import Format
from opentracing import SplitBinaryCarrier
from opentracing import SplitTextCarrier
from opentracing import Tracer
from opentracing.ext import tags


def test_span():
    tracer = Tracer()
    parent = tracer.start_span('parent')
    child = tracer.start_span('test', parent=parent)
    assert parent == child
    child.log_event('cache_hit', ['arg1', 'arg2'])

    with mock.patch.object(parent, 'finish') as finish:
        with mock.patch.object(parent, 'log_event') as log_event:
            try:
                with parent:
                    raise ValueError()
            except ValueError:
                pass
            assert finish.call_count == 1
            assert log_event.call_count == 1

    with mock.patch.object(parent, 'finish') as finish:
        with mock.patch.object(parent, 'log_event') as log_event:
            with parent:
                pass
            assert finish.call_count == 1
            assert log_event.call_count == 0

    parent.set_tag('x', 'y').set_tag('z', 1)  # test chaining
    parent.set_tag(tags.PEER_SERVICE, 'test-service')
    parent.set_tag(tags.PEER_HOST_IPV4, 127 << 24 + 1)
    parent.set_tag(tags.PEER_HOST_IPV6, '::')
    parent.set_tag(tags.PEER_HOSTNAME, 'uber.com')
    parent.set_tag(tags.PEER_PORT, 123)
    parent.finish()


def test_injector():
    tracer = Tracer()
    span = tracer.start_span()

    bin_carrier = SplitBinaryCarrier()
    tracer.injector(Format.SPLIT_BINARY).inject_span(
        span=span, carrier=bin_carrier)
    assert bin_carrier.tracer_state == bytearray()
    assert bin_carrier.trace_attributes == bytearray()

    text_carrier = SplitTextCarrier()
    tracer.injector(Format.SPLIT_TEXT).inject_span(
        span=span, carrier=text_carrier)
    assert text_carrier.tracer_state == {}
    assert text_carrier.trace_attributes == {}


def test_extractor():
    tracer = Tracer()
    noop_span = tracer._noop_span

    bin_carrier = SplitBinaryCarrier()
    span = tracer.extractor(Format.SPLIT_BINARY).join_trace(
        'op_name', carrier=bin_carrier)
    assert noop_span == span

    text_carrier = SplitTextCarrier()
    span = tracer.extractor(Format.SPLIT_TEXT).join_trace(
        'op_name', carrier=text_carrier)
    assert noop_span == span
