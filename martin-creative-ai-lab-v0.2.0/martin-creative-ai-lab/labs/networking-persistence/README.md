# Networking & Persistence Lab — joint expedition recovery

Owner origin: P11; cross-origin invariants: P05 Cinderwatch and P01 Eclipse Fair.
This bounded method studies local single-owner command ownership and recovery of the
actual North Star C# expedition. It does not claim an MMO service or completed
networking/persistence domain.

## Selection and independent analyses

Engineering, Scientific and Creative analyses compared durable joint recovery,
NPC/narrative continuity and evaluation methods against actual product state and
sources. The current expedition already has earned identity, equipped actions,
finite materials, encounter resources and rewards; process exit previously discarded
all of them. Recovery therefore adds a consequential production dependency rather
than another terminal preparation layer. NPC/quest sources need separate state and
authored-consequence assays; source journals and empty reputation effects cannot
stand in for a working world. Evaluation requires a concrete candidate/decision,
not a generic label attached to routine tests.

Creative review preferred authored narrative continuity as the next experience gain;
Engineering and Science selected recovery as a concrete prerequisite because current
process exit erased existing investment. Creation accepted that boundary and required
explicit new/resume, readable state and refusal without silent reset. This preserves
agency already implemented; it is not new authored narrative agency. CRE-005 supports
remembered consequence and CRE-013 remains a safe-replacement hypothesis.

SCI-017 influenced the method: distinguish implementation, environment and injected
failure; compare the same accepted command prefix across restarts; preserve negative
results. Process repetitions are software observations, not participants or player
validation. A historical CI remote-consumer failure is diagnosed separately; it does
not establish a persistence defect or the cause of any other failure.

## Inspected sources and scope

`run.py` binds and assays the actual sources:

- `projects/cinderwatch/Core/Journal.cs`: bounded versioned accepted-command replay,
  rejection of illegal replay and unknown fields, temporary-file replacement/cleanup.
- `projects/eclipse-fair/Cli/Journal.cs`: temporary-file replacement and cleanup.
- `projects/realtime-integration-lab/rooms-store.cjs`: content-bound uncertain retries.
- `projects/realtime-integration-lab/rooms-actions.cjs`: transaction rollback,
  request identity/content conflict checks, commit before receipt and stored receipts.
- `projects/realtime-integration-lab/rooms-backup.cjs`: explicit flush and recovery
  refusal to overwrite existing data.

These are inspected **invariant sources**, not executed origin runtimes in this
instrument. Cinder's file-store source does not contain an explicit file flush;
replay and temporary replacement alone cannot establish power-loss durability.
P11 SQLite transactions and its backup format are not silently imported as a C#
provider, authentication model, save schema or permission to overwrite player data.
No source fiction, credentials or personal workspaces enter the new experiment.

## Actual method and reproduction

The instrument builds the actual RecoveryChecks host with the existing SDK pin,
executes native controls, then executes the actual Recovery consumer's multi-process
demonstration. The destination verifies whole gameplay observations, not only a
summary count/hash. Recovery must preserve committed identity/slots, inventory and
request receipts, earned XP/allocation, encounter stage and resource state.
Duplicate retry must neither refund a failed rig nor mint another reward/output;
changing content under a committed request identity must refuse safely.

```bash
python3 -m unittest discover -s labs/networking-persistence -p 'test_*.py'
python3 labs/networking-persistence/run.py --dotnet dotnet \
  --output /tmp/persistent-expedition.json \
  --compare evidence/persistent-expedition/results.json
```

The SDK must match `north-star/csharp/global.json`. Build, native and demonstration
processes have bounded timeouts. Outputs are forbidden throughout the maintained
workspace; scratch saves live in temporary directories. Source/instrument/consumer
fingerprints must remain identical before and after execution. Exact comparison
binds both identities and complete observations. The consumer's README and retained
execution own exact CLI commands, outcomes and local file semantics.

Controls include real process restart during an encounter, durable duplicate and
content-conflict handling, failure before replacement versus after commit/before
receipt, corrupt/unsupported saves, second-writer refusal, OS lease release after an owner
process is killed, and failed-rig conservation.
Injected child termination is not a simulated machine power cut. Meaningful failures
and attempted environment repairs remain separate from successful execution.

## Validity and next frontier

Integrate only the demonstrated replay, request ownership and local process/file
recovery contracts into the real consumer. Preserve origin save formats and existing
applications; this is not a migration of historical SQLite databases or all P11
networking. Recovery evidence does not establish hostile-save authentication,
authoritative accounts, remote replication, multi-host concurrency or exactly-once
network delivery.

Actual execution here is pinned .NET on Linux. It does not establish Windows rename,
locking or filesystem behavior, Unity Editor/API compatibility, Steam Cloud,
commercial distribution, power-loss durability or human comprehension. Checksums and
rules identity bind supported content/corruption boundaries; they are not signatures
or anti-cheat. Keep the selected Unity/C#, Windows-first, Steam-intended direction.

Next: compare the remaining incomplete laboratories and concrete production needs;
execute Windows/platform recovery and supported Unity integration when available.
Do not repeat this same command-prefix study as another substantive unit or assume
that a functioning local journal completes the networking domain.
