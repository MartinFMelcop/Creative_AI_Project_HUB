# Recipient delivery — The coil and the shutters

This packages the [existing authored scene](../../north-star/authored-scene/README.md)
for a recipient without a checkout, SDK or Node installation. It does not add a new
scene or replace its unchanged `RequestExpedition` owner. The beneficiary is someone
who wants to inspect actual choices instead of assembling development tools first.

## Obtain and run

[Download the complete Linux x64 ZIP](dist/authored-scene-demo-linux-x64.zip) and
[its SHA256 checksum](dist/SHA256SUMS). [Actual execution and provenance](../../evidence/recipient-delivery/RUN.json)
identify the delivered artifact; CI success and source availability are separate facts.
Extract the archive into a fresh directory; paths with spaces are supported:

```sh
sha256sum -c SHA256SUMS
mkdir 'North Star demo'
unzip authored-scene-demo-linux-x64.zip -d 'North Star demo'
cd 'North Star demo/AuthoredSceneDemo'
./run-demo.sh
```

Open the loopback URL printed by the host in your graphical browser. No SDK, Node,
account or network connection is required after acquisition. The bundled official
.NET runtime still requires compatible Linux x64 native libraries; `sha256sum` is
required for the launch-time payload check. Actual execution coverage is one Debian13
Linux x64 environment, not general Linux compatibility, physical-device coverage or
Windows validation. Consult the linked execution record for the actual tested package.

The default port is 8768 and lifetime 300 seconds. `./run-demo.sh 8769 600` selects a
port 1024–65535 and lifetime 1–600 seconds. Stop with Ctrl+C or wait for host expiry.
An occupied port fails; choose another port explicitly. The launcher checks payload
hashes before executing its private runtime; changed or missing runtime, web content
or notices must prevent launch. This is an integrity check within a trusted package,
not a signature or a way to make an untrusted archive safe.

## What to observe

Edda's unfinished shutters, Rill's consent and actual departure/return, finite light,
refusal, guided travel and the actual Crossing encounters share one owner. A guided
handoff can succeed while local work remains unfinished. Promise, redraw and elapsed
time never fabricate completion. Inspect the visible threat and current state before
choosing; there is no universal free solution supplied by delivery tooling.

The session is ephemeral. Refresh observes the host; it is not a save. New day
explicitly replaces the session. Process exit/expiry loses it. Following an uncertain
response, reconnect observes actual state without replaying intent. This trusted-local
loopback observer has no authentication, shared-world or production-security claim.

## Reproduce and inspect

[package.py](package.py) builds from a verified copied source closure and includes only
the installed private runtime files matching [the official runtime lock](runtime-lock.json).
The lock was derived from the SHA512-verified SDK archive; supplying `--sdk-archive`
checks that archive again. [check.py](check.py) independently validates and extracts
the archive. [verify.py](verify.py) builds twice and executes the actual relocated
recipient package through [Chromium](browser.mjs):

```sh
python3 delivery/authored-scene/verify.py --dotnet /absolute/path/to/dotnet --output /tmp/recipient-delivery-new
```

The SDK must match 10.0.401, with its included .NET10.0.12 runtime. Verification uses
the existing locked Node24.19.0/Playwright/Chromium instrument; these tools are not
required by the recipient package. Use a fresh output directory. Keep outputs outside maintained
sources. The source-development fallback remains the scene's existing build/run
commands; no prebuilt artifact availability is inferred from those commands.

The archive root is `AuthoredSceneDemo/`: `app/`, original `web/`, private `runtime/`,
`source/`, `BUILDINFO.json`, `payload.sha256`, `run-demo.sh` and `README.txt`.
Build metadata binds actual inputs; the copied forward source closure supports
inspection and recovery without pretending to be a complete HUB source distribution.
Payload identity is distinct from behavior, runtime archive identity and author approval.

The runtime retains its own `LICENSE.txt` and `ThirdPartyNotices.txt`. Martin Melcop
Neto directs and owns the project's creative authority; this scene and staging are
original experimental agent-authored work under that direction, not approved cast/world
canon. Preserve source provenance and rights. No blanket commercial clearance or
license for all HUB code, fiction and media is granted by this package.

This remains an actual Linux/.NET/browser observer. Unity/C# is selected for production,
Windows-first and Steam-intended. Editor activation/modules, Windows-player execution,
Steam delivery, independent author/player assessment and commercial clearance remain
separate unresolved obligations. Delivery does not establish comprehension, fairness,
accessibility, enjoyment or human approval. Existing gameplay controls and historical
negatives remain in their original evidence; this package is a distinct recipient-runtime
beneficiary, not another count of the same scene implementation.

## Update and retirement conditions

This is one current local demonstration, not a second permanent Linux product line.
When its actual forward source, bundle instructions, runtime lock or launcher changes,
rebuild and compare the delivered payload; do not silently ship an outdated package.
CI also rebuilds from separate staging roots and compares every delivered file against
the committed artifact. Two builds in one environment must reproduce ZIP bytes;
cross-environment acceptance compares exact payload identities, separating compression
implementation from source/binary identity. Keep the actual downloadable ZIP SHA distinct.

The copied source closure was rebuilt from the extracted archive and reproduced all
ten delivered application files byte-for-byte with the pinned SDK. Recovery requires
that development SDK; running the delivered demonstration does not.

The copied sources and notices provide a recovery path for this bounded demonstration;
unique Godot players, saves, original media and notices have not been replaced or retired.
The package may be superseded after another real delivery supplies its recipient/runtime/
source-recovery behavior and rights. Actual Unity/Windows delivery remains the production
acceptance; no question or integrity gate was relaxed to call Build/Operations complete.
