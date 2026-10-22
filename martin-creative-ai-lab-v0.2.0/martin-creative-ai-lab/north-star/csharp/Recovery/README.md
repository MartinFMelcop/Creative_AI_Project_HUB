# Recoverable North Star expedition

An original **local recovery consumer** preserves the actual Loadout/Forge/Crossing
journey: identity and slots, earned XP/allocations, finite materials, consumed rigs,
encounter health/resolve/position and next action. It adds continuity to existing
behavior; it does not add another preparation system or a production account service.

## Build, create and continue

From `north-star/csharp`, use the exact SDK10.0.401 pin:

```bash
dotnet build RecoveryChecks/NorthStar.RecoveryChecks.csproj -c Release
dotnet Recovery/bin/Release/net10.0/NorthStar.Recovery.dll new /tmp/north-star-run.json
dotnet Recovery/bin/Release/net10.0/NorthStar.Recovery.dll play /tmp/north-star-run.json
# Close with quit or EOF, then run play again on the SAME existing path.
dotnet Recovery/bin/Release/net10.0/NorthStar.Recovery.dll show /tmp/north-star-run.json
dotnet RecoveryChecks/bin/Release/net10.0/NorthStar.RecoveryChecks.dll native /tmp/recovery-native.json
dotnet Recovery/bin/Release/net10.0/NorthStar.Recovery.dll --demo /tmp/recovery-journeys.json
```

`new` explicitly creates and persists a fresh run and **refuses every existing path**.
`play` and `show` require a valid existing journal. Missing, corrupt, unsupported or
incompatible runs refuse recovery; they never silently start over or overwrite the
old bytes. Preserve an incompatible file for explicit migration or inspection.

During play, accepted commands save before the receipt. `quit`/EOF releases the local
owner; the next process restores the exact next turn. Current state, actual next
threat and distance/deadline appear before input. Available commands are:

```text
craft trail
craft plate
enter trail
enter plate
enter unprepared
walk
wait
slot 1
focus 2
vitality 2
loadout anchor trailborn brace dash - -
quit
```

Existing rules remain: finite4fiber+2binder; each rig costs2fiber+1binder and entry
consumes it even on failure. Slots and earned-level requirements, outfit/style
independence, active preparation locks and reward ownership are unchanged. Reloading
is continuity, not a refund, respec, heal or reward reset. Original experimental class/
background names and numbers are not approved canon. See [Loadout](../Loadout/README.md)
for complete action costs and rules.

## Atomic ownership and receipts

[Journal.cs](Journal.cs) holds an exclusive `.lock` FileStream across load, replay and
replacement. Cooperating .NET processes opening the same canonical regular path are
excluded; process death releases the OS-held lease. The lock file remains after close
so deletion/recreation cannot accidentally split cooperative ownership. Save/lease
symlinks and directories are rejected. Parent directories and filesystem owners are
trusted: hard-link aliases, hostile mutations, remote filesystems and multiple hosts
are not an authorization or distributed-lock boundary.

Submit and Dispose serialize within a live owner. Disposed sessions cannot mutate
a run after their lease has transferred; readonly snapshots remain historical observations.
A typed command is normalized, validated and applied to a candidate reconstructed
from accepted history. Only an accepted candidate can produce a new complete journal.
A unique same-directory temporary file is written and `Flush(true)` executes before
replacement. Only after replacement returns does the live consumer publish candidate
state and return its receipt. A write exception blocks the current owner: close and
reopen the validated durable file before issuing more commands. Failed/rejected
commands reserve no request ID and never modify the saved journal.

A successful request ID owns its normalized command content. Retrying it after restart
returns `Accepted:true, Duplicate:true` without reapplying its effect. Substituting
content returns a conflict. Receipt `OriginalRevision` identifies the first accepted
command; `CurrentRevision` and `State` describe the current run, including later
accepted commands. A duplicate receipt therefore does not masquerade as an old snapshot.

Developer protocol:

```bash
dotnet Recovery/bin/Release/net10.0/NorthStar.Recovery.dll submit /tmp/north-star-run.json craft_1 '{"op":"craft","recipe":"trail_rig"}'
```

Supported exact command shapes: `craft/recipe`, `begin/rig`, `allocate/axis/points`,
`replace/class_id/background_id/slots`, `slot/slot` (zero-based), and `walk` or `wait`.
Unknown/duplicate/missing fields, invalid JSON/types and unsupported commands refuse.
The journal accepts at most4,096 entries/2MiB. Sequence, request identity uniqueness,
per-prefix actual state hashes, schema1, rules identity and canonical checksum are
validated before recovered state is exposed. Replay uses the actual existing consumer,
not trusted serialized HP, XP, inventory or completion fields.

Rules identity fingerprints embedded copies of the actual Domain sources and Crossing/
Forge/Loadout gameplay owners. This is portable source-byte identity, not a machine-
specific DLL hash or a promise that all future protocol changes are compatible. Schema
and explicit migration remain necessary. Checksums detect accidental corruption;
trusted local users can rewrite/recompute a valid journal. No tamper resistance,
authentication or account ownership is claimed.

## Actual executed controls and limits

The demo launches real child processes for each accepted operation, interruption and
reopen. It preserves the complete mid-encounter snapshot; retries and content conflicts
cannot duplicate resources. The connected journey resumes through earned Focus/Dash
and completes at HP11/resolve5, position4, XP25/level3 with two rigs consumed. A failed
rig remains spent after restart. Existing-new and corrupt-file refusal, competing
writer exclusion and actual owner-process death/reopen are exercised.

Three controlled child exits use code79 at `before_write`, `before_replace` and
`after_replace` (before receipt). Fresh processes must recover complete old prefixes
at the first two boundaries and the complete new prefix at the last. Retrying after
acknowledgement loss yields a duplicate, without another craft. The unlocked temporary
file left by a killed pre-replacement writer is never treated as an accepted run.

The native suite has82 controls, including recomputed-checksum semantic corruption,
future schema/rules refusal, duplicate request/sequence, malformed fields, limits,
whole-state rejection, blocked uncertain writes and symlink refusal. The demonstration
was also executed through the Linux apphost; child host selection supports both
`dotnet DLL` and apphost invocation. `DOTNET_ROOT` must identify an installed runtime
when the SDK is outside the system installation.

P11's commit-before-receipt/idempotency and P05/P01's full replay validation inform
this adaptation. Their SQLite, modern game fiction and full applications are not
imported. No existing gameplay source is modified. This .NET10 file/process host is
not offered as a Unity runtime assembly; the existing domain remains C#8/netstandard2.1.
The [Persistence laboratory](../../../labs/networking-persistence/README.md) owns the
bounded method, identities and evidence.

Actual Linux process interruption is not power loss. File flush plus rename does not
establish directory-fsync, arbitrary-filesystem durability, Windows behavior or Steam
cloud conflict policy. No Unity Editor, Windows player, Steam, networking/account
security, shared-world scale, player preference or independent human validation ran.
