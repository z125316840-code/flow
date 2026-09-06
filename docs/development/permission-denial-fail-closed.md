# Permission Denial Must End an Agent Run

## Goal

Flow agents are visible virtual colleagues. Visibility does not grant authority: every
tool runs with the current Frappe/ERPNext user's identity and permissions. If any tool
reports that the user lacks permission, the current agent run must end immediately.

The agent must not retry, switch tools, alter filters, use code/SQL/raw APIs, assume an
administrator identity, or otherwise look for an alternate path to the same data or
action.

## Runtime contract

This rule is a platform invariant, not wording that every agent author must remember to
paste into an individual prompt.

1. Flow prepends a highest-priority permission boundary to every runtime agent prompt.
2. It also injects the boundary when continuing an older transcript, so sessions created
   before this change receive the same policy.
3. The tool runner distinguishes permission exceptions from ordinary tool errors.
4. A permission exception produces a structured `permission_denied` tool result and a
   deterministic user-facing terminal message. The model is not called again.
5. If one model response contains multiple tool calls, calls after the denied call are
   recorded as skipped and are not executed.
6. The same behavior applies to synchronous runs, streamed runs, and confirmed tool calls
   resumed after a pause.
7. Built-in batch write/action tools must re-raise permission exceptions instead of
   hiding them inside ordinary per-record failure lists.
8. DocType discovery must distinguish "nothing matched" from "matches exist but none are
   readable". The latter is a permission denial, not an empty search result that the model
   may work around by broadening its query.

Ordinary validation, missing-record, integration, and business-rule failures remain tool
errors that the model may explain or recover from. A user choosing **Deny** at a confirmation
prompt remains a separate terminal outcome.

## User-visible response

The terminal response must say that the current Frappe/ERPNext user lacks the required
permission, that the task stopped, and that no alternate route was attempted. It may suggest
requesting access or handing the work to an authorized user. Raw exception text remains in
the auditable tool result but is not echoed into the natural-language response.

For compatibility, a permission-stopped run remains a terminal completed Flow Run. The
tool transcript carries `status: permission_denied`; this change does not add a new database
status or require a schema migration.

## Files in scope

- `flow/lib/agent.py`: global prompt policy, permission result type, fail-closed control
  flow, streaming/resume parity, and skipped-call transcript completion.
- `flow/flow/doctype/flow_agent/flow_agent.py`: include the effective policy in saved run
  snapshots for auditability.
- `flow/flow/doctype/flow_run/flow_run.py`: keep historical sessions without a stored
  system row aligned when the policy is injected ephemerally.
- `flow/tools/builtins.py`: propagate permission exceptions from batch operations.
- `flow/translations/zh.csv`: provide the deterministic terminal response in Chinese.
- `flow/tests/test_ai_agent.py`: runtime, multi-call, streaming, old-transcript, and resume
  regression tests.
- `flow/tests/test_ai_builtins.py`: built-in permission propagation tests.
- `flow/flow/doctype/flow_run/test_flow_run.py`: historical-session persistence regression.

## Acceptance tests

Run these in order:

1. Compile the changed Python files with Python 3.14 and a cache directory under `/tmp`.
2. Run the focused agent unit tests.
3. Run the focused built-in integration tests in a Frappe Bench/site environment.
4. Run the repository's configured pre-commit checks.
5. Review the final diff and verify the original dirty checkout is unchanged.
6. Commit the branch and push it to the user's GitHub fork.

The critical assertions are:

- a generic tool exception still returns to the model for possible recovery;
- a built-in or Frappe permission exception stops after one model turn;
- permission-filtered DocType discovery stops instead of making an installed module look absent;
- later calls in the same response never execute after permission denial;
- streaming emits terminal tool events and `Done` without another model request;
- approval-resume stops if the approved tool raises a permission exception;
- a historical message list receives the permission policy before the next model call.

## Out of scope

- Granting, mirroring, or bypassing ERPNext roles and User Permissions.
- Hiding agents based on business-document permissions.
- Treating prompt text as the security boundary; Frappe remains the authorization source.
- Adding per-user permission checks to custom Python tools that intentionally bypass
  Frappe. Such tools remain a configuration/code-review concern and should not be exposed
  to agents.
