#!/bin/sh
set -eu
fail() { printf '%s\n' "Cannot start demo: $*" >&2; exit 1; }
[ "$#" -le 2 ] || fail 'usage: ./run-demo.sh [PORT [SECONDS]]'
port=${1-8768}
seconds=${2-300}
case "$port" in ''|*[!0-9]*) fail 'PORT must be an integer from 1024 to 65535';; esac
case "$seconds" in ''|*[!0-9]*) fail 'SECONDS must be an integer from 1 to 600';; esac
# Reject oversized or zero-prefixed representations before shell integer arithmetic.
[ "${#port}" -le 5 ] || fail 'PORT must be from 1024 to 65535'
[ "${#seconds}" -le 3 ] || fail 'SECONDS must be from 1 to 600'
case "$port" in 0*) fail 'PORT must not have leading zeroes';; esac
case "$seconds" in 0*) fail 'SECONDS must not have leading zeroes';; esac
[ "$port" -ge 1024 ] && [ "$port" -le 65535 ] || fail 'PORT must be from 1024 to 65535'
[ "$seconds" -ge 1 ] && [ "$seconds" -le 600 ] || fail 'SECONDS must be from 1 to 600'
bundle_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P) || fail 'cannot locate extracted bundle'
cd "$bundle_dir"
command -v sha256sum >/dev/null 2>&1 || fail 'sha256sum is required to check the extracted payload'
[ -f payload.sha256 ] || fail 'payload.sha256 is missing'
sha256sum -c --status payload.sha256 || fail 'payload is missing or changed; extract a fresh trusted package'
[ -x runtime/dotnet ] || fail 'bundled runtime is not executable'
[ -f runtime/LICENSE.txt ] && [ -f runtime/ThirdPartyNotices.txt ] || fail 'runtime notices are missing'
[ -f app/NorthStar.AuthoredScene.dll ] && [ -f web/index.html ] || fail 'application or web content is missing'
# Saves are separate mutable user data, never part of the verified package payload.
scene_save_dir=${NORTH_STAR_SAVE_DIR-"$bundle_dir/../NorthStarSaves"}
case "$scene_save_dir" in /*) ;; *) fail 'NORTH_STAR_SAVE_DIR must be an absolute directory path';; esac
[ ! -L "$scene_save_dir" ] || fail 'save directory must not be a symbolic link'
if [ ! -e "$scene_save_dir" ]; then
  command -v mkdir >/dev/null 2>&1 || fail 'mkdir is required to create the local save directory'
  mkdir -p -- "$scene_save_dir" || fail 'cannot create selected local save directory'
fi
[ -d "$scene_save_dir" ] && [ ! -L "$scene_save_dir" ] || fail 'selected save path must be a regular directory'
scene_save="$scene_save_dir/scene.json"
[ ! -L "$scene_save" ] || fail 'local save must not be a symbolic link'
if [ -e "$scene_save" ]; then
  [ -f "$scene_save" ] || fail 'local save must be a regular file'
  scene_mode=--resume
else
  scene_mode=--new
fi
DOTNET_ROOT="$bundle_dir/runtime"
DOTNET_ROOT_X64="$DOTNET_ROOT"
DOTNET_MULTILEVEL_LOOKUP=0
DOTNET_ROLL_FORWARD=Disable
DOTNET_EnableDiagnostics=0
DOTNET_CLI_TELEMETRY_OPTOUT=1
export DOTNET_ROOT DOTNET_ROOT_X64 DOTNET_MULTILEVEL_LOOKUP DOTNET_ROLL_FORWARD DOTNET_EnableDiagnostics DOTNET_CLI_TELEMETRY_OPTOUT
exec "$bundle_dir/runtime/dotnet" "$bundle_dir/app/NorthStar.AuthoredScene.dll" --serve "$port" "$bundle_dir/web" --seconds "$seconds" "$scene_mode" "$scene_save"
