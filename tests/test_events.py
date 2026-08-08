from agent.events import RunEventBroadcaster


def test_broadcaster_delivers_published_events_to_subscriber():
    broadcaster = RunEventBroadcaster()
    q = broadcaster.subscribe("run-1")
    broadcaster.publish("run-1", {"node": "research"})
    assert q.get(timeout=1) == {"node": "research"}


def test_broadcaster_close_sends_sentinel():
    broadcaster = RunEventBroadcaster()
    q = broadcaster.subscribe("run-1")
    broadcaster.close("run-1")
    assert q.get(timeout=1) is None


def test_publish_to_unknown_run_id_is_a_no_op():
    broadcaster = RunEventBroadcaster()
    broadcaster.publish("unknown-run", {"node": "research"})  # must not raise
