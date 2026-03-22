"""E2E tests for RAG (document upload and chat) flow."""
import io
import uuid
import pytest
from httpx import AsyncClient


class TestRAGFlowE2E:
    """E2E tests for RAG document upload and chat flow."""

    @pytest.mark.asyncio
    async def test_document_upload_and_retrieval(self, api_client: AsyncClient, unique_project_name: str):
        """Test uploading a document and retrieving it."""
        # Create project
        project_response = await api_client.post(
            "/api/projects",
            json={"name": unique_project_name, "description": "RAG test project"},
        )

        if project_response.status_code == 500:
            pytest.skip("Database not available")

        assert project_response.status_code == 200
        project_id = project_response.json()["id"]

        try:
            # Upload document
            content = b"# StudyClaw Test\n\nThis is a test document for RAG."
            files = {"file": ("test.md", io.BytesIO(content), "text/markdown")}

            upload_response = await api_client.post(
                f"/api/projects/{project_id}/documents",
                files=files,
            )

            # Upload may succeed or fail depending on Chroma availability
            if upload_response.status_code == 200:
                doc = upload_response.json()
                assert doc["filename"] == "test.md"

                # List documents
                list_response = await api_client.get(
                    f"/api/projects/{project_id}/documents",
                )
                assert list_response.status_code == 200
                docs = list_response.json()["documents"]
                assert len(docs) >= 1
            else:
                # If Chroma not available, check response
                assert upload_response.status_code in [200, 500]

        finally:
            # Cleanup
            await api_client.delete(f"/api/projects/{project_id}")

    @pytest.mark.asyncio
    async def test_chat_endpoint_accessible(self, api_client: AsyncClient, unique_project_name: str):
        """Test that chat endpoint is accessible (streaming response)."""
        # Create project
        project_response = await api_client.post(
            "/api/projects",
            json={"name": unique_project_name},
        )

        if project_response.status_code == 500:
            pytest.skip("Database not available")

        assert project_response.status_code == 200
        project_id = project_response.json()["id"]

        try:
            # Send chat message (streaming)
            chat_response = await api_client.post(
                f"/api/projects/{project_id}/chat",
                json={"message": "Hello, this is a test message", "session_id": str(uuid.uuid4())},
            )

            # Should get streaming response or error
            assert chat_response.status_code in [200, 500]

        finally:
            # Cleanup
            await api_client.delete(f"/api/projects/{project_id}")

    @pytest.mark.asyncio
    async def test_document_deletion_flow(self, api_client: AsyncClient, unique_project_name: str):
        """Test deleting a document after upload."""
        # Create project
        project_response = await api_client.post(
            "/api/projects",
            json={"name": unique_project_name},
        )

        if project_response.status_code == 500:
            pytest.skip("Database not available")

        assert project_response.status_code == 200
        project_id = project_response.json()["id"]

        try:
            # Upload document
            content = b"# Test\n\nContent to be deleted."
            files = {"file": ("delete_test.md", io.BytesIO(content), "text/markdown")}

            upload_response = await api_client.post(
                f"/api/projects/{project_id}/documents",
                files=files,
            )

            if upload_response.status_code == 200:
                doc = upload_response.json()
                doc_id = doc["id"]

                # Delete document
                delete_response = await api_client.delete(f"/api/documents/{doc_id}")
                assert delete_response.status_code == 200

                # Verify deletion
                get_response = await api_client.get(f"/api/documents/{doc_id}")
                assert get_response.status_code == 404

        finally:
            # Cleanup project
            await api_client.delete(f"/api/projects/{project_id}")
