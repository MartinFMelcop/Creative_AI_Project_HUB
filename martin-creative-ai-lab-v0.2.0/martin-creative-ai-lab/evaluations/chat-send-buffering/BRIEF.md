# EVAL-001 — Repair chat send buffering

You are given a local Node/Express/Socket.IO text chat. Its client can lose a
form submission even while it reports a connection. Repair `public/client.js`.
All other supplied files must remain unchanged. Dependencies are locked; do not
upgrade them or add a framework. Explain your correction separately from this
workspace. Do not consult a reference solution or evaluator-owned checks.

## Run and reproduce

Requires Node 22+, npm, and a browser. From this exported workspace:

```bash
npm ci
npm start
```

Open `http://127.0.0.1:3000` in two local tabs. Accepted text should appear once
in each tab, including the sender. Messages are ephemeral; there is no identity,
history recovery, or persistence. Stop the server when finished.

To investigate the defect, force the sender to use HTTP polling, disable its
WebSocket upgrade, and reconnect. Start an ordinary outgoing packet, then submit
the form while the polling transport is temporarily busy. The form message must
wait for that live write instead of disappearing. Also inspect what happens if
heartbeat expiry is detected before the UI's connected flag changes.

## Required behavior

- A connected send survives an in-flight polling write and appears once in each
  connected browser, in event order. Use the existing broadcast rendering path.
- A stale connected flag must not retain a failed attempt for automatic replay
  after reconnection. Offline submissions keep their draft and send nothing.
- Preserve validation: strings only; 1–500 UTF-16 units before trimming;
  whitespace-only or oversized text rejected. Display text literally.
- Preserve rejection feedback, uncertain-delivery feedback on acknowledgement
  timeout, and a newer draft typed before an earlier acknowledgement arrives.
- Keep only the latest 200 displayed messages. Rejoining and new participants
  receive future messages only. Do not introduce persistence or automatic retry.

Submission is this workspace with only `public/client.js` changed. The evaluator
will check browser behavior and regressions separately; no numeric model score
is implied by an artifact passing. Do not place outputs or explanations here.

Origin: P11 working starter 0.1.0, commit `66041e7fdd7687ee21099f95129dff41933c74dd`.
This is a public practice task. Exported files exclude answers and checks, but
public repository history is discoverable; this task cannot prove secrecy or
independent model performance.
