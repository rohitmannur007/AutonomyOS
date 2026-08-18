"""
Execution Simulator.

No real infrastructure is touched. Each supported action has fixed metadata
(whether it is reversible, and the message shown on simulated success) so
the rest of the system — risk engine, autonomy engine, UI — can reason about
it consistently and deterministically.
"""

from dataclasses import dataclass


@dataclass
class ActionMeta:
    label: str
    reversible: bool
    success_message: str


ACTIONS = {
    "RESET_AUTH_SESSION": ActionMeta(
        label="Reset authentication session",
        reversible=True,
        success_message="Authentication session reset successfully. The user can sign in normally.",
    ),
    "RESET_PASSWORD": ActionMeta(
        label="Reset password",
        reversible=True,
        success_message="Temporary password issued and emailed to the verified recovery address.",
    ),
    "UNLOCK_ACCOUNT": ActionMeta(
        label="Unlock account",
        reversible=True,
        success_message="Account lockout cleared. The user can sign in immediately.",
    ),
    "ASSIGN_M365_LICENSE": ActionMeta(
        label="Assign Microsoft 365 license",
        reversible=True,
        success_message="License assigned successfully and provisioned to the account.",
    ),
    "GRANT_ADMIN_PERMISSION": ActionMeta(
        label="Grant administrator permission",
        reversible=True,
        success_message="Elevated administrative role granted and logged to the security audit trail.",
    ),
    "INSTALL_SOFTWARE": ActionMeta(
        label="Install software",
        reversible=True,
        success_message="Software package pushed to the device and installed successfully.",
    ),
    "DISABLE_USER": ActionMeta(
        label="Disable user account",
        reversible=True,
        success_message="User account disabled and sessions revoked across all devices.",
    ),
    "UPDATE_FIREWALL_RULE": ActionMeta(
        label="Update firewall rule",
        reversible=False,
        success_message="Firewall rule updated and change logged to the network audit trail.",
    ),
}


def get_action_meta(action: str) -> ActionMeta:
    return ACTIONS.get(
        action,
        ActionMeta(label=action, reversible=True, success_message="Action completed successfully."),
    )


def simulate_execution(action: str) -> dict:
    """Deterministically 'execute' an action. Always succeeds in this
    simulator — there is no real backend system to fail against — but the
    shape mirrors a real integration's response so the UI/execution path is
    realistic."""
    meta = get_action_meta(action)
    return {
        "status": "SUCCESS",
        "message": meta.success_message,
    }
