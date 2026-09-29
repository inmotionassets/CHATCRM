import threading
from types import SimpleNamespace

from fastapi import HTTPException

from backend.app.routers import leads


def caller(username: str):
    return SimpleNamespace(username=username, name=username.title(), role="Acquisition")


def test_atomic_claim_allows_only_one_caller(tmp_path, monkeypatch):
    monkeypatch.setattr(leads, "DATABASE_PATH", tmp_path / "claims.db")
    monkeypatch.setattr(leads, "USE_POSTGRES", False)
    leads.save_lead(leads.Lead(id="lead-1", address="100 Main St", name="Seller"))
    barrier = threading.Barrier(2)
    outcomes = []

    def attempt(username):
        barrier.wait()
        try:
            saved = leads.claim_lead_for_user("lead-1", caller(username))
            outcomes.append(("ok", saved.assignedToUserId))
        except HTTPException as exc:
            outcomes.append((exc.status_code, exc.detail))

    threads = [threading.Thread(target=attempt, args=(name,)) for name in ("caller-a", "caller-b")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    successes = [outcome for outcome in outcomes if outcome[0] == "ok"]
    conflicts = [outcome for outcome in outcomes if outcome[0] == 409]
    assert len(successes) == 1
    assert len(conflicts) == 1
    assert leads.get_saved_lead("lead-1").assignedToUserId == successes[0][1]


def test_admin_assignment_can_reassign_and_unassign(tmp_path, monkeypatch):
    monkeypatch.setattr(leads, "DATABASE_PATH", tmp_path / "assignments.db")
    monkeypatch.setattr(leads, "USE_POSTGRES", False)
    admin = SimpleNamespace(username="admin", name="Admin", role="Admin")
    leads.save_lead(leads.Lead(id="lead-2", address="200 Main St", name="Seller"))
    assigned = leads.assign_lead_as_admin(
        "lead-2", leads.LeadAssignmentRequest(userId="caller-a", userName="Caller A"), admin
    )
    assert assigned.assignedToUserId == "caller-a"
    assert assigned.assignedToName == "Caller A"
    unassigned = leads.assign_lead_as_admin("lead-2", leads.LeadAssignmentRequest(), admin)
    assert unassigned.assignedToUserId == ""
    assert unassigned.assignedToName == ""
