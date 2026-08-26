# Operations Documentation

Use this reference when auditing, creating, or adopting the canonical `ops` role.

## Boundary

Operations documentation helps maintainers and operators configure, deploy, observe, diagnose, recover, and safely update real development or service environments. Examples include Docker image updates, cloud configuration, service restarts, health checks, backup and recovery, migration execution, and first-aid for recurring failures.

Keep code-changing, test-authoring, and release-engineering guidance in `implementation-tips`. Keep required system behavior in `specs`, current runtime topology in `architecture`, and accepted structural rationale in architecture decision records. Public end-user troubleshooting stays with the public documentation owner unless it requires operator authority or environment access.

## Runbook Contract

Each runbook states:

- the target system, supported environment, symptom or intended outcome, and owner;
- prerequisites, required access, expected impact, and any separate approval boundary;
- safe read-only diagnosis before mutation;
- the bounded resolution or update procedure;
- success checks and observable postconditions;
- rollback, failure recovery, escalation conditions, and the escalation owner.

Never record credentials, tokens, private keys, live secret values, or copied secret-bearing output. Use descriptive placeholders and reference the owning secret-management authority. Name destructive, production, network, publication, and third-party control-plane effects explicitly; documentation never grants authority to perform them.

Prefer durable CLI, API, or repository-owned commands over volatile console click paths. When a cloud or provider console is the actual authority, identify the product surface and the assumptions that may drift without claiming a stale screen sequence is current forever.

## Empty Operations Surface

Every delivery scope has an operations index. When the scope has no independently operated environment, the index records that fact, identifies any other owning scope, and contains no invented procedures. Add a runbook only when repository evidence establishes its target and owner.
