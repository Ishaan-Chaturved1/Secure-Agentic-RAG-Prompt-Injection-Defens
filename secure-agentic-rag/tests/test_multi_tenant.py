"""
Comprehensive tests for Multi-User / Multi-Workspace RAG:
Authentication, Authorization, Document Ownership, and Pre-Retrieval Vector Isolation.
"""

import io
import os
import shutil
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.auth.security import hash_password, verify_password
from app.db.database import Database
from app.main import app
from app.rag.workspace_manager import WorkspaceRetrieverManager, get_workspace_retriever_manager


@pytest.fixture(scope="module")
def client():
    """Create test client with isolated database and storage."""
    temp_dir = tempfile.mkdtemp(prefix="rag_test_")
    db_path = Path(temp_dir) / "test_app.db"
    test_db = Database(db_path)

    # Override get_db dependency
    from app.auth.deps import get_db
    app.dependency_overrides[get_db] = lambda: test_db

    # Override global workspace manager
    ws_manager = WorkspaceRetrieverManager(Path(temp_dir))
    import app.rag.workspace_manager as wm_module
    import app.main as main_module
    import app.api.documents as doc_module
    import app.api.user_rag as user_rag_module

    wm_module._global_workspace_manager = ws_manager

    with TestClient(app) as test_client:
        yield test_client

    # Clean up overrides and temp directory
    app.dependency_overrides.clear()
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestPasswordHashing:
    """Security tests for password hashing."""

    def test_hash_not_plaintext(self):
        pw = "SuperSecretPassword123!"
        hashed = hash_password(pw)
        assert hashed != pw
        assert len(hashed) > 20
        assert not hashed.startswith(pw)

    def test_verify_password_correct(self):
        pw = "MySecurePassword2026"
        hashed = hash_password(pw)
        assert verify_password(pw, hashed) is True

    def test_verify_password_incorrect(self):
        pw = "MySecurePassword2026"
        hashed = hash_password(pw)
        assert verify_password("WrongPassword!", hashed) is False

    def test_salting_unique_hashes(self):
        pw = "IdenticalPassword"
        h1 = hash_password(pw)
        h2 = hash_password(pw)
        assert h1 != h2  # Different salts ensure different hashes


class TestAuthenticationFlow:
    """Tests for registration, login, and token enforcement."""

    def test_register_user_success(self, client):
        resp = client.post(
            "/auth/register",
            json={
                "username": "alice",
                "email": "alice@example.com",
                "password": "PasswordAlice123!",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["user"]["username"] == "alice"
        assert data["user"]["email"] == "alice@example.com"
        assert "password_hash" not in data["user"]
        assert "token" in data
        assert len(data["workspaces"]) >= 1
        assert data["active_workspace_id"] == data["workspaces"][0]["id"]

    def test_register_duplicate_username_fails(self, client):
        resp = client.post(
            "/auth/register",
            json={
                "username": "alice",
                "email": "alice_alt@example.com",
                "password": "PasswordAlice123!",
            },
        )
        assert resp.status_code == 400
        assert "already registered" in resp.json()["detail"].lower()

    def test_login_success(self, client):
        resp = client.post(
            "/auth/login",
            json={
                "username_or_email": "alice",
                "password": "PasswordAlice123!",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert data["user"]["username"] == "alice"

    def test_login_invalid_password_fails(self, client):
        resp = client.post(
            "/auth/login",
            json={
                "username_or_email": "alice",
                "password": "WrongPassword!",
            },
        )
        assert resp.status_code == 401
        assert "Invalid credentials" in resp.json()["detail"]

    def test_login_nonexistent_user_fails(self, client):
        resp = client.post(
            "/auth/login",
            json={
                "username_or_email": "nonexistent_user",
                "password": "AnyPassword123!",
            },
        )
        assert resp.status_code == 401

    def test_get_current_user_me(self, client):
        # Register Bob
        reg = client.post(
            "/auth/register",
            json={
                "username": "bob",
                "email": "bob@example.com",
                "password": "PasswordBob123!",
            },
        )
        token = reg.json()["token"]

        # Call /auth/me with valid bearer token
        me_resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_resp.status_code == 200
        assert me_resp.json()["user"]["username"] == "bob"

    def test_unauthorized_endpoints(self, client):
        # Calling protected endpoints without token must return 401
        assert client.get("/documents").status_code == 401
        assert client.get("/auth/me").status_code == 401
        assert client.post("/query", json={"query": "test"}).status_code == 401
        assert client.post("/user/query", json={"query": "test"}).status_code == 401


class TestMultiTenantIsolation:
    """
    Critical security test:
    Verify tenant isolation between User A (Workspace A) and User B (Workspace B).
    """

    @pytest.fixture(autouse=True)
    def setup_tenants(self, client):
        import uuid
        uid = uuid.uuid4().hex[:6]
        # Register User A
        reg_a = client.post(
            "/auth/register",
            json={
                "username": f"user_a_{uid}",
                "email": f"user_a_{uid}@enterprise.com",
                "password": "SecurePasswordA123!",
            },
        )
        self.token_a = reg_a.json()["token"]
        self.ws_a = reg_a.json()["active_workspace_id"]
        self.headers_a = {"Authorization": f"Bearer {self.token_a}"}

        # Register User B
        reg_b = client.post(
            "/auth/register",
            json={
                "username": f"user_b_{uid}",
                "email": f"user_b_{uid}@enterprise.com",
                "password": "SecurePasswordB123!",
            },
        )
        self.token_b = reg_b.json()["token"]
        self.ws_b = reg_b.json()["active_workspace_id"]
        self.headers_b = {"Authorization": f"Bearer {self.token_b}"}

    def test_isolated_document_upload_and_listing(self, client):
        # Upload doc_A to Workspace A
        doc_a_content = (
            "User A Private Travel Policy:\n"
            "Employees traveling on transatlantic flights over 5 hours are eligible for Business Class seating."
        )
        res_a = client.post(
            "/documents/upload",
            headers=self.headers_a,
            data={"workspace_id": self.ws_a},
            files={"file": ("travel_policy_a.txt", io.BytesIO(doc_a_content.encode("utf-8")), "text/plain")},
        )
        assert res_a.status_code == 201
        doc_a_id = res_a.json()["id"]

        # Upload doc_B to Workspace B
        doc_b_content = (
            "User B Confidential Financial Earnings:\n"
            "Q3 Secret Financial Report: Gross net profit surpassed 45 million dollars with 80% operating margin."
        )
        res_b = client.post(
            "/documents/upload",
            headers=self.headers_b,
            data={"workspace_id": self.ws_b},
            files={"file": ("financials_b.txt", io.BytesIO(doc_b_content.encode("utf-8")), "text/plain")},
        )
        assert res_b.status_code == 201
        doc_b_id = res_b.json()["id"]

        # User A lists documents: must ONLY see travel_policy_a.txt
        list_a = client.get("/documents", headers=self.headers_a)
        assert list_a.status_code == 200
        docs_a = list_a.json()
        doc_a_filenames = [d["original_filename"] for d in docs_a]
        assert "travel_policy_a.txt" in doc_a_filenames
        assert "financials_b.txt" not in doc_a_filenames

        # User B lists documents: must ONLY see financials_b.txt
        list_b = client.get("/documents", headers=self.headers_b)
        assert list_b.status_code == 200
        docs_b = list_b.json()
        doc_b_filenames = [d["original_filename"] for d in docs_b]
        assert "financials_b.txt" in doc_b_filenames
        assert "travel_policy_a.txt" not in doc_b_filenames

        # Test direct access attempt: User A attempts GET /documents/{doc_b_id} -> must be DENIED (403)
        get_denied = client.get(f"/documents/{doc_b_id}", headers=self.headers_a)
        assert get_denied.status_code == 403

        # Test direct delete attempt: User A attempts DELETE /documents/{doc_b_id} -> must be DENIED (403)
        del_denied = client.delete(f"/documents/{doc_b_id}", headers=self.headers_a)
        assert del_denied.status_code == 403

        # Test workspace manipulation attempt: User A uploads file claiming workspace_id=ws_b -> must be DENIED (403)
        spoof_upload = client.post(
            "/documents/upload",
            headers=self.headers_a,
            data={"workspace_id": self.ws_b},
            files={"file": ("spoof.txt", io.BytesIO(b"Spoofed document"), "text/plain")},
        )
        assert spoof_upload.status_code == 403

        # Test workspace manipulation in query: User A attempts to query workspace B -> must be DENIED (403)
        spoof_query = client.post(
            "/query",
            headers=self.headers_a,
            json={"query": "financial profit", "workspace_id": self.ws_b},
        )
        assert spoof_query.status_code == 403

    def test_semantic_retrieval_cross_tenant_isolation(self, client):
        """
        Verify that semantic search / vector retrieval NEVER leaks another tenant's documents.
        """
        # Upload doc_A to Workspace A
        doc_a = "Executive Travel Guideline: Employees must submit flight expense receipts within 14 business days."
        client.post(
            "/documents/upload",
            headers=self.headers_a,
            data={"workspace_id": self.ws_a},
            files={"file": ("travel_rules.txt", io.BytesIO(doc_a.encode("utf-8")), "text/plain")},
        )

        # Upload doc_B to Workspace B
        doc_b = "Confidential API Key Vault: Project Titan secret master access key is TITAN_VAULT_KEY_9999."
        client.post(
            "/documents/upload",
            headers=self.headers_b,
            data={"workspace_id": self.ws_b},
            files={"file": ("vault_secrets.txt", io.BytesIO(doc_b.encode("utf-8")), "text/plain")},
        )

        # 1. User A asks specifically for User B's secret
        query_a = client.post(
            "/query",
            headers=self.headers_a,
            json={"query": "What is the Project Titan secret master access key?", "mode": "hardened"},
        )
        assert query_a.status_code == 200
        res_a = query_a.json()

        # User A's retrieval must NOT contain User B's document or secret!
        for doc_text in res_a["retrieved_documents"]:
            assert "TITAN_VAULT_KEY" not in doc_text
            assert "Project Titan" not in doc_text
        assert "TITAN_VAULT_KEY_9999" not in res_a["answer"]

        # 2. User B asks for the Project Titan secret
        query_b = client.post(
            "/query",
            headers=self.headers_b,
            json={"query": "What is the Project Titan secret master access key?", "mode": "hardened"},
        )
        assert query_b.status_code == 200
        res_b = query_b.json()
        # User B's retrieved documents should contain their own document
        assert any("TITAN_VAULT_KEY" in doc_text for doc_text in res_b["retrieved_documents"])

        # 3. User B asks about travel rules
        query_b_travel = client.post(
            "/query",
            headers=self.headers_b,
            json={"query": "When must travel receipts be submitted?", "mode": "hardened"},
        )
        assert query_b_travel.status_code == 200
        res_b_travel = query_b_travel.json()
        # User B must NOT retrieve User A's travel guidelines
        for doc_text in res_b_travel["retrieved_documents"]:
            assert "Executive Travel Guideline" not in doc_text
            assert "14 business days" not in doc_text

    def test_document_deletion_removes_from_retriever(self, client):
        # User A uploads a temporary policy
        temp_doc = "UniqueCodeOmega: The secret alpha launch code is 12345."
        res = client.post(
            "/documents/upload",
            headers=self.headers_a,
            data={"workspace_id": self.ws_a},
            files={"file": ("launch.txt", io.BytesIO(temp_doc.encode("utf-8")), "text/plain")},
        )
        doc_id = res.json()["id"]

        # Query verifies it is retrieved
        q1 = client.post(
            "/query",
            headers=self.headers_a,
            json={"query": "launch code", "mode": "hardened"},
        )
        assert any("UniqueCodeOmega" in d for d in q1.json()["retrieved_documents"])

        # User A deletes the document
        del_res = client.delete(f"/documents/{doc_id}", headers=self.headers_a)
        assert del_res.status_code == 200

        # Query after deletion verifies it is NO LONGER retrieved
        q2 = client.post(
            "/query",
            headers=self.headers_a,
            json={"query": "launch code", "mode": "hardened"},
        )
        assert not any("UniqueCodeOmega" in d for d in q2.json()["retrieved_documents"])
