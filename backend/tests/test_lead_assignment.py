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



def test_google_voice_open_is_not_a_call_attempt():
    assert "call_started" not in leads.CALL_COUNT_ACTIVITY_TYPES
    assert "voice_opened" not in leads.CALL_COUNT_ACTIVITY_TYPES
    assert "call_result" in leads.CALL_COUNT_ACTIVITY_TYPES


def test_result_requires_claim_and_follow_up_details(tmp_path, monkeypatch):
    monkeypatch.setattr(leads, "DATABASE_PATH", tmp_path / "results.db")
    monkeypatch.setattr(leads, "USE_POSTGRES", False)
    worker = caller("caller-a")
    leads.save_lead(leads.Lead(id="lead-3", address="300 Main St", name="Seller"))

    try:
        leads.save_lead_result(
            "lead-3",
            leads.LeadResultRequest(contactStatus="did-not-answer", phoneNumber="2145551212"),
            worker,
        )
        assert False, "unclaimed lead result should fail"
    except HTTPException as exc:
        assert exc.status_code == 409

    leads.claim_lead_for_user("lead-3", worker)
    for request in (
        leads.LeadResultRequest(contactStatus="follow-up", notes="Call back"),
        leads.LeadResultRequest(contactStatus="follow-up", followUpDate="2026-10-01"),
    ):
        try:
            leads.save_lead_result("lead-3", request, worker)
            assert False, "incomplete follow-up should fail"
        except HTTPException as exc:
            assert exc.status_code == 422


def test_saved_result_records_attempted_phone_and_counts_once(tmp_path, monkeypatch):
    monkeypatch.setattr(leads, "DATABASE_PATH", tmp_path / "attempts.db")
    monkeypatch.setattr(leads, "USE_POSTGRES", False)
    worker = caller("caller-a")
    leads.save_lead(leads.Lead(id="lead-4", address="400 Main St", name="Seller"))
    leads.claim_lead_for_user("lead-4", worker)

    saved = leads.save_lead_result(
        "lead-4",
        leads.LeadResultRequest(
            contactStatus="did-not-answer",
            notes="No answer on first number.",
            phoneNumber="2145551212",
        ),
        worker,
    )
    activity = leads.list_lead_activities("lead-4")[0]
    assert saved.contactStatus == "did-not-answer"
    assert activity.actionType == "call_result"
    assert activity.callOutcome == "Did Not Answer"
    assert "2145551212" in activity.notes



def test_other_caller_cannot_log_power_dialer_action(tmp_path, monkeypatch):
    monkeypatch.setattr(leads, "DATABASE_PATH", tmp_path / "ownership.db")
    monkeypatch.setattr(leads, "USE_POSTGRES", False)
    caller_a = caller("caller-a")
    caller_b = caller("caller-b")
    leads.save_lead(leads.Lead(id="lead-5", address="500 Main St", name="Seller"))
    leads.claim_lead_for_user("lead-5", caller_a)

    try:
        leads.create_lead_activity(
            "lead-5",
            leads.LeadActivityCreate(actionType="voice_opened", phoneNumber="2145551212"),
            caller_b,
        )
        assert False, "another caller must not log dialer activity"
    except HTTPException as exc:
        assert exc.status_code == 409
        assert "Caller-A" in exc.detail
