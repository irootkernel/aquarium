#!/bin/sh
# Guest entrypoint for Aquarium's Haepari VM suites.
# It refuses to run outside the managed runner's Job/lease context and never
# submits another Job, runs the host wrapper, or operates UTM.
set -eu

refuse() {
	printf '%s\n' 'This entrypoint requires the managed runner Job/lease context.' >&2
	exit 2
}

test -n "${HAEPARI_PARENT_CONTEXT:-}" || refuse
job=$(printf '%s' "$HAEPARI_PARENT_CONTEXT" | /usr/bin/plutil -extract 0.job_id raw -o - -) || refuse
lease=$(printf '%s' "$HAEPARI_PARENT_CONTEXT" | /usr/bin/plutil -extract 0.lease_generation raw -o - -) || refuse
nonce=$(printf '%s' "$HAEPARI_PARENT_CONTEXT" | /usr/bin/plutil -extract 0.nonce raw -o - -) || refuse
case "$job" in '' | *[!a-zA-Z0-9._-]*) refuse ;; esac
case "$lease" in '' | *[!0-9]*) refuse ;; esac
test "$lease" -gt 0 || refuse
case "$nonce" in '' | *[!0-9a-f]*) refuse ;; esac
test "${#nonce}" -eq 64 || refuse

test -n "${AQUARIUM_GUEST_PYTHON:-}" || refuse
AQUARIUM_VM_JOB_ID="$job"
AQUARIUM_VM_LEASE_GENERATION="$lease"
export AQUARIUM_VM_JOB_ID AQUARIUM_VM_LEASE_GENERATION
exec "$AQUARIUM_GUEST_PYTHON" -B "$(dirname "$0")/guest_main.py" "$@"
