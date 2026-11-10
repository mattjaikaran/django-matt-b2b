# Specs

A spec is a scoped unit of work an unattended agent can finish without a
design decision. The spec file is the source of truth; a GitHub issue is the
request it answers.

One file per spec: `tasks/specs/S-<AREA>-<NN>-<slug>.md`, where the ID is
`S-<AREA>-<NN>` and matches the file name prefix. Use an uppercase area code:
`API`, `AUTH`, `ORG`, `INFRA`, `DOCS`, `TEST`.

## Format

Start with a header table. agent-run reads only the table, up to the first
`## ` heading, so keep every row and spell the keys as below.

|Key|Rule|
| --- | --- |
|`Spec ID`|`S-<AREA>-<NN>`; matches the file name prefix.|
|`Issue`|Issue number(s) the spec closes.|
|`Size`|`S` or `M`. An `L` issue is split before a spec is written.|
|`Status`|`READY`, `BLOCKED-DEPS`, `BLOCKED-PLANNER`, `BLOCKED-HUMAN` or `MERGED`.|
|`Branch`|`agent/<Spec ID>`.|
|`Depends on`|Spec IDs that merge first, or `none`.|
|`Files owned`|Every path, directory or glob the diff may change.|
|`Migrations`|App and purpose, or `none`; listed here because a migration may sit outside `Files owned`.|
|`Verification`|Commands that prove the change, e.g. `make lint`, `make test-fast`, `make docs-check`.|
|`Human needed`|`none`, or the decision a human makes first.|

Then the body:

- `## Context` - the current behavior, with code quoted as `path:start-end`.
- `## Change` - exact files and symbols, and the shape of the result.
- `## Acceptance` - observable outcomes, not steps.

## Template

```markdown
|Key|Value|
| --- | --- |
|Spec ID|S-API-01|
|Issue|12|
|Size|S|
|Status|READY|
|Branch|agent/S-API-01|
|Depends on|none|
|Files owned|apps/organizations/controllers/, apps/organizations/schemas/, tests/test_organizations.py|
|Migrations|none|
|Verification|make lint, make test-fast|
|Human needed|none|

## Context

`OrganizationController.list_organizations` returns every membership
(`apps/organizations/controllers/organization_controller.py:27-58`).

## Change

Filter inactive memberships and add a `status` query parameter.

## Acceptance

- `GET /api/organizations?status=active` returns only active memberships.
- `make test-fast` passes.
```

## Gate

agent-run fails the run when:

- a changed file is outside `Files owned`;
- a migration is added that `Migrations` does not list;
- a `Verification` command fails.

A spec gap - a needed path or a missing decision - stops the run. Report it;
never widen the spec.

## Status lifecycle

```
draft -> READY -> claimed (agent/<ID> branch and PR) -> MERGED
              -> BLOCKED-DEPS (a dependency is not merged)
              -> BLOCKED-PLANNER (a spec gap needs the planner)
              -> BLOCKED-HUMAN (a decision is missing)
```

`claimed` is not a header value; it is the `agent/<ID>` branch. Merging the PR
lands the code and sets `Status` to `MERGED` in the same commit.
