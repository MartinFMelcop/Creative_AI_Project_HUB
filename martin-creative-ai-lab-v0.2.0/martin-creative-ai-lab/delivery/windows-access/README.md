# Windows access probe — unchanged authored-scene recipient

This asks whether the [existing Windows recipient](../authored-scene-windows/README.md)
can start and expose its actual C# owner under an explicitly observed non-elevated
Windows token context. Prior recipient execution used an administrative token; it
cannot answer this access question. This probe adds no scene, gameplay owner, resource,
package release or save migration.

The [predeclared protocol](../../evidence/windows-access/protocol.json) is preparation,
not an execution result. Initially, this access assessment is **unexecuted**. A later
record must identify the actual Windows job, executable inputs, token context and
outcome before any access claim is made. Build/Operations remains incomplete under
its retained licensed Unity Editor/module and production Windows acceptance.

## Fixed baseline and actual context

Use the complete, unchanged `authored-scene-demo-win-x64.zip`:

- SHA256: `0500d70a6a6c7071f12423fd529c0922830c09d34a312ae46c4f1e562c5aaffb`.
- Bytes: 35,820,510; official private .NET10.0.12 win-x64 runtime and complete notices.
- The same ten managed application files and 22 archived sources remain bound to the
  existing Linux delivery and compiled journal identity.

Extract and inspect the trusted package before probing. Keep probe outputs, mutable
saves and any compiled probe helper outside the maintained tree and immutable package.
Do not change the package, regenerate either recipient, or edit its source to collect
this baseline.

The probe first uses an already-existing linked limited token if Windows actually
provides one. Otherwise it attempts a restricted primary token derived from the current
account: `CreateRestrictedToken(DISABLE_MAX_PRIVILEGE)`, Administrators SID deny-only,
and medium integrity. The selected branch and actual resulting child context must be
recorded; these contexts are not interchangeable. If the token cannot be created or
its resulting identity cannot be observed, the access result is inconclusive.

This retains the same underlying account/profile and filesystem environment. It is
not a fresh ordinary-user account, a different person's Windows desktop, a physical
device assessment or proof for Windows10/11. A process merely launched by a wrapper
named “restricted” is insufficient evidence: inspect the actual child token and bind
that observation to the package launch.

No accounts, URL reservations, execution policies, privileges or machine security
settings are changed to make the application succeed. No elevation or policy bypass
is part of this method. A policy refusal remains a refusal or an inconclusive result,
with its actual stage retained; it must not be converted into a gameplay result.

## Execute the bounded assessment

Build the separate probe helper with the pinned SDK10.0.401. Record exact helper,
script, archive and relevant inherited input hashes before execution and verify them
afterwards. Compilation is preparation; only an actual Windows process can answer
the access question. The helper is an instrument, not part of the recipient package.

From an appropriate Windows instrument environment, using absolute paths:

```powershell
pwsh -NoProfile -File delivery/windows-access/probe.ps1 -Bundle 'C:\external\AuthoredSceneWindows' -Launcher 'C:\external\TokenProbe.dll' -Output 'C:\external\new-access-result' -Shell 'C:\Program Files\PowerShell\7\pwsh.exe'
```

Use a new output directory. The package still invokes its own private runtime. Keep
all owned process trees bounded and stop them after the probe. The instrument records
actual exit status, stdout/stderr, observed state and the selected token context.
Do not infer successful launch from a created process, file, printed intention or
published workflow. Do not infer an application refusal from a timeout or failure to
construct the instrument's process/token.

## Decision boundary

A real successful launch and observation of `/state` support only the stated package,
Windows host and observed token context. A real nonzero application exit supports an
actual refusal at the recorded stage. It does not, by itself, prove that HTTP.sys
permissions caused it. Preserve the exact diagnostic and separate token/instrument,
package integrity, policy, filesystem, occupied-port and network possibilities.

A timeout, missing result, unavailable token context or failed helper is inconclusive
for application access. Retain it without counting it as successful refusal or gameplay.
No fallback grants, invented return or silent save reset can make an access test pass.

Only an observed consequential dependency can justify a later transport adaptation.
Such a change needs its own acceptance, actual consumer execution and preservation of
the existing scene/journal owner; it must not be preselected as the winner. If this
baseline already works, do not implement a replacement merely to satisfy the hypothesis.
The existing archives, protected sources, notices and prior consumers remain intact.

Read SCI-013/014/076/077 for the materially applied rival-hypothesis, construct,
method-selection and repeated-observation limits. Specialist review and automated
controls are not independent human comprehension, approval, usability or enjoyment.
