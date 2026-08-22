# Aquarium

<img alt="Aquarium AI Fleet 엔지니어링 생태계" src="plugins/aquarium/assets/hero.png" width="100%">

**Vibe coding이 아니라, AI Fleet으로 하는 소프트웨어 엔지니어링.**

[English](README.md) · 한국어 · Codex 대신 Claude Code를 쓴다면 [Aquarium for Claude](https://github.com/irootkernel/aquarium-for-claude)를 보십시오.

[Root Kernel](https://home.rootkernel.xyz) 제작 · 지원: [cs@rootkernel.xyz](mailto:cs@rootkernel.xyz)

Aquarium은 AI Fleet으로 신뢰할 수 있는 소프트웨어를 만들기 위한 Codex 플러그인입니다. 전문화된 에이전트, 모델, 개발 도구를 하나의 워크플로로 연결하되 세 가지 규칙을 지킵니다. 모든 task는 추적되는 상태를 가지고, 완료는 검증된 증거를 요구하며, 영향이 큰 행동은 사용자의 승인을 기다립니다.

Aquarium은 vibe coding을 넘어 Agentic Engineering, Loop Engineering, Graph Engineering, 그리고 그다음의 practice를 향해 나아갑니다. 이들은 별개의 제품이나 고정된 성숙도 모델이 아닙니다. AI 작업이 더 전문화되고, 더 반복적이며, 더 긴밀히 연결되고, 더 책임 있는 형태로 발전하는 방향을 가리킵니다.

## 왜 Aquarium인가

AI 도구가 아무리 뛰어나도 하나씩 따로 쓰면 맥락, 승인, task 상태, 증거를 엔지니어가 직접 챙겨야 합니다. Aquarium은 이 도구들을 하나의 워크플로로 묶고 다음 규칙을 지킵니다.

- **작업에는 identity가 있습니다.** 수행 대상 task나 epic은 roadmap 안에서 ID와 lifecycle 상태를 가집니다. Commit은 `task-commit`을 거치며, 사용자가 확인한 lifecycle 변경을 건너뛰지 않고 함께 기록합니다.
- **수행은 단계와 gate로 나뉩니다.** `task-handler`는 task 하나를 plan부터 close까지 7단계로 진행합니다. Plan을 승인하기 전에는 아무것도 바꾸지 않습니다. 해당하는 모든 roadmap 요구사항은 현재 증거와 대응되어야 합니다. Closeout은 사용자의 명시적 승인을 기다립니다.
- **증거는 검증됩니다.** 명령의 exit code가 pass/fail을 결정합니다. Review finding은 roadmap, 코드, 테스트에 대해 로컬에서 검증하기 전까지 참고 의견(advisory)으로만 취급합니다.
- **Loop에는 한계가 있습니다.** Clean review가 나오면 loop는 즉시 끝납니다. Review와 remediation round는 정해진 예산 안에서만 돌고, cold validation은 새 gap이 더 발견되지 않으면 멈춥니다.
- **불변식과 테스트는 계약입니다.** Design Gate는 offline에서 객관적으로 검증 가능한 규칙입니다. Gate impact가 아직 pending인 task는 구현할 수 없고, release QA는 모든 active gate를 다시 실행합니다. 공통 테스트 계약은 prepare, unit, integration, E2E를 순서대로 실행하고, 전제 조건이 빠지면 건너뛰는 대신 실패하며, 새 프로젝트에는 waiver를 주지 않습니다.
- **권한은 사용자에게 있습니다.** 도구 설치, provider로의 source 전송, staging, commit, push, publication은 각각 따로 승인을 받습니다. 설계 문서와 setup 파일은 사용자가 승인한 exact diff로만 바뀝니다. 로컬 hook은 roadmap 저장소에서 직접 실행한 shell commit을 잡아 `task-commit` 경로로 안내합니다.
- **작업은 멈추고, 재개하고, 인계할 수 있습니다.** `task-handler`와 `epic-handler`는 plan-only 실행, 다른 에이전트로의 명시적 plan handoff, 기존 session 재개를 지원합니다. Plan만으로는 runtime state가 생기지 않습니다.

Codex는 Aquarium의 primary agent runtime입니다. Aquarium은 provider나 framework 중립성을 약속하는 대신 정해진 toolchain을 의도적으로 통합합니다. Codex, Orca, Podway, Sanho, Mulgae, Gaori, Ouroboros, Lora, Deslop 사이의 계약은 Aquarium이 소유하며, 각 계약은 도구를 언제 실행하고 무엇을 결정하게 하며 그 출력을 다음 단계의 증거로 어떻게 쓰는지를 정합니다.

## 설치

```bash
codex plugin marketplace add irootkernel/aquarium --ref main
codex plugin add aquarium@root-kernel
```

설치나 업그레이드 후 Codex를 재시작하고, `/hooks`에서 Aquarium의 roadmap commit guard를 명시적으로 신뢰하도록 설정합니다. 이 hook은 직접 실행한 shell commit을 잡아냅니다. 다만 완전한 강제 장치는 아니어서, 다른 도구가 간접적으로 만든 commit은 hook을 거치지 않을 수 있습니다.

Aquarium은 third-party skill이나 문서 source를 저장소에 내장(vendor)하지 않습니다. `$aquarium:dev-setup`이 지원 도구의 상태를 진단하고, 각각 별도 승인을 받아 정확한 upstream source에서 설치하거나 복구합니다. Upstream `$deslop` skill은 task 수행의 필수 요구사항입니다.

## 주요 워크플로

1. **Shape** — `$aquarium:new-project`는 목표를 승인된 PRD와 첫 roadmap으로 만듭니다. `$aquarium:new-feature`와 `$aquarium:refactor`는 epic 하나를 만들거나 수정합니다. `$aquarium:war-room`은 어려운 버그를 진단해 다음 작업 단위를 제안하거나 조사가 미완료임을 보고하며, 수정 코드는 쓰지 않습니다. `$aquarium:design-qa`는 Design Gate를 만들고, 바꾸고, 퇴역시킵니다.
2. **Deliver** — `$aquarium:task-handler`는 roadmap task 하나를 위의 단계로 수행합니다. `$aquarium:epic-handler`는 epic의 task를 순서대로 수행한 뒤 epic 전체를 hardening합니다. Commit은 별도로 `$aquarium:task-commit`을 거치며 사용자가 승인합니다.
3. **Validate** — `$aquarium:epic-validator`는 완료된 epic을 처음부터 다시 검증하고 확인된 gap을 해소합니다. `$aquarium:independent-review`는 별도의 Codex session에 요구사항과 코드의 read-only review를 맡기며, `$aquarium:orca-review`는 공개된 exact snapshot을 사용자가 고른 provider로 Orca에서 review합니다. Aquarium은 반환된 finding을 모두 로컬에서 확인합니다.
4. **Release** — `$aquarium:release-qa`는 버전을 내보내기 전에 release delta와 모든 active Design Gate를 격리된 scenario로 검증합니다.

기반 구성: `$aquarium:test-setup`은 저장소를 공통 테스트 계약에 등록합니다. `$aquarium:dev-setup`은 toolchain과 저장소의 에이전트 운영 지침을 진단하고 설정합니다. `$aquarium:dev-setup-bundle`은 manifest 하나로 여러 저장소에 같은 setup을 적용합니다.

## 생태계가 연결되는 방식

- [Podway](https://github.com/irootkernel/podway)는 Git 기반 workflow의 goal, transition, handoff를 기록하는 영속적인 local execution memory를 제공합니다. `task-handler`, `epic-handler`, `epic-validator`, `new-project`, `new-feature`, `refactor`, `war-room`, `design-qa`는 기본적으로 Podway를 사용하며, 첫 managed-session 변경 전에 선택 해제할 수 있습니다. Workflow는 Aquarium이 진행하고 Podway는 기록하며, 상세 lifecycle 작업은 해당 workflow나 standalone `use-podway` skill이 맡습니다.
- [Gaori](https://github.com/irootkernel/gaori)는 기존 check를 실행하고, raw log를 보존하며, 요약된 evidence를 돌려줍니다. Gaori 연동은 선택 사항이고, 명령의 exit code가 pass/fail의 기준입니다.
- [Mulgae](https://github.com/irootkernel/mulgae)는 완료된 task와 epic을 여러 provider로 review해 참고용 finding을 냅니다. Aquarium은 finding을 하나씩 로컬에서 검증하고 remediation 범위를 제한합니다.
- [Orca Review](plugins/aquarium/skills/orca-review/SKILL.md)는 별도로 설치된 Orca runtime에서 사용자가 명시적으로 선택한 AI CLI가 공개된 repository snapshot 하나를 review하도록 감독합니다. Aquarium은 provider 동의를 그 snapshot에 결합하고 결과를 독립적으로 판정합니다.
- [Sanho](https://github.com/irootkernel/sanho)는 Aquarium이 인계할 결과를 확정한 뒤, 프로젝트 문서를 canonical documentation repository와 동기화합니다.
- [Lora](https://github.com/tmdgusya/lora)는 decision context를 Git trailer에 남기고, [Cursor Team Kit](https://github.com/cursor/plugins/tree/main/cursor-team-kit)은 task refinement에 쓰는 upstream `deslop` cleanup skill을 제공합니다.
- [Ouroboros](https://github.com/Q00/ouroboros)는 명시적으로 호출한 다섯 가지 design workflow 안에서만 discovery, PM, Seed, QA를 제공합니다. 문서 적용, 승인, 저장소 authority는 Aquarium이 가집니다.

이 도구들은 작업 구체화부터 문서 동기화까지 하나의 통제된 경로를 이룹니다. Aquarium은 그 사이를 연결해, 도구 하나의 성공이 프로젝트 완료로 오인되지 않게 합니다.

## 운영 경계

- Workflow 호출은 해당 skill에 문서화된 효과만 허용합니다. 설치, 인증, source 전송, 테스트, staging, commit, push, publication, 파괴적인 lifecycle 작업은 각각 별도의 권한이 필요합니다.
- `release-qa` 호출은 QA 1회, private repository에 대한 기존 ambient authentication을 사용하는 구성된 Git remote와 hosting의 release metadata read-only 조회, 검증된 finding의 제한된 local 수정을 허용합니다. 수정 후에는 새 QA 전에 명시적 확인을 받기 위해 멈추며, source upload나 credential 처리는 하지 않습니다.
- Setup이나 진단 대상으로 선택한 Sanho, Mulgae, Gaori, Podway는 설치된 `use-*` skill과 비교하기 위해 official GitHub Releases metadata를 자동으로 조회하고 `raw.githubusercontent.com`에서 공개 skill 파일 4개를 임시 저장소로 내려받습니다. 선택하지 않은 도구와 그 밖의 network 작업은 포함되지 않으며, setup은 AI provider를 호출하지 않습니다.
- Aquarium은 중앙 project-state 파일을 만들지 않습니다. 전체 data 및 authority contract는 [PRIVACY.md](PRIVACY.md)와 [TERMS.md](TERMS.md)에 있습니다.

## 참고 문서

- [TESTING.md](TESTING.md)는 이 저장소의 test authority와 `aquarium-test-contract/v1` evidence mapping을 정의합니다.
- [Bundle manifest reference](plugins/aquarium/skills/dev-setup-bundle/references/manifest.md)는 여러 저장소를 한 번에 설정하는 manifest 형식을 정의합니다.
- 각 skill의 `SKILL.md`가 trigger, effect, approval boundary, failure behavior의 authority입니다.

## 검증

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
make test
```

이 gate는 Python 3.11 이상, Ruby 3.3 이상, 그리고 `requirements.txt`에 고정된 버전이 필요합니다. 이 저장소는 [MIT License](LICENSE)를 따릅니다.

## 업그레이드

- 이전 `aquarium` marketplace identity에서 오는 경우: `codex plugin remove aquarium@aquarium`과 `codex plugin marketplace remove aquarium`을 실행한 뒤 위의 설치 명령을 사용합니다.
- Legacy Root Kernel plugin에서 오는 경우: 진행 중인 legacy Podway session을 먼저 종료하거나 정리(disposition)하고, `codex plugin remove root-kernel@root-kernel-dev-skills`와 `codex plugin marketplace remove root-kernel-dev-skills`를 실행한 뒤 Aquarium을 설치하고, `$aquarium:dev-setup`으로 managed Procedure를 migration합니다.

## 감사의 말

Aquarium이 기반으로 삼는 upstream skill을 제공해 준 Lora, Ouroboros, Cursor Team Kit에 감사드립니다. Aquarium은 이들의 skill이나 문서 source를 저장소에 내장하지 않습니다. Ouroboros와 Cursor Team Kit은 MIT LICENSE 파일을 제공하고, Lora는 README에 MIT를 명시합니다.
