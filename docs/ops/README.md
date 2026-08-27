# Aquarium Operations

This directory owns maintainer and operator guidance for configuring, diagnosing, recovering, and safely updating Aquarium's real development and local runtime environments. It does not replace the user-facing installation and upgrade guidance in the root README, implementation-changing guidance in `docs/implementation-tips/`, or executable authority in skills, Procedures, the Makefile, and repository instructions.

## Current Operational Surface

Aquarium is a local Codex plugin rather than an independently hosted service. Its current operational surface is the installed plugin, paired local tool integrations, managed Procedure files, and disposable workflow runtime state. The root [README](../../README.md) owns supported installation and upgrade commands. [Implementation tips](../implementation-tips/README.md) own how maintainers change and release those components. Add focused runbooks here when repository evidence establishes a recurring environment operation or recovery case.

The [development-channel runbook](development-channel.md) covers diagnosis, approved enrollment, exact builds, isolated Codex configuration, login, and bounded recovery on Apple Silicon macOS.

## Runbook Requirements

Every runbook must state:

- the target, supported environment, symptom or intended outcome, and owner;
- prerequisites, required authority, expected impact, and safe read-only diagnosis;
- the bounded procedure and its success checks;
- rollback or failure recovery, escalation conditions, and the escalation owner.

Never record credentials, tokens, private keys, live secret values, or copied secret-bearing output. Use descriptive placeholders and reference the owning secret-management authority. A runbook documents an operation but never grants approval to perform installation, authentication, network, production, destructive, publication, or third-party control-plane effects.
