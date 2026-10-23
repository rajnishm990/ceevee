import boto3
import pytest
from moto import mock_aws

from app.core.config import settings
from app.services import storage_service
from app.services.storage_service import StorageService

BUCKET = "test-bucket"


@pytest.fixture()
def s3_backend(monkeypatch):
    for key in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"):
        monkeypatch.setenv(key, "testing")
    monkeypatch.setattr(settings, "STORAGE_BACKEND", "s3")
    monkeypatch.setattr(settings, "S3_BUCKET_NAME", BUCKET)
    monkeypatch.setattr(settings, "S3_REGION", "us-east-1")
    monkeypatch.setattr(settings, "S3_ENDPOINT_URL", "")
    monkeypatch.setattr(settings, "AWS_ACCESS_KEY_ID", "")
    storage_service._s3_client.cache_clear()
    with mock_aws():
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket=BUCKET)
        yield client
    storage_service._s3_client.cache_clear()


def _keys(client):
    return [o["Key"] for o in client.list_objects_v2(Bucket=BUCKET).get("Contents", [])]


async def test_s3_roundtrip_stores_ciphertext_only(s3_backend):
    key = await StorageService.save_file("abc", b"%PDF-1.4 hello")
    assert key == "resumes/abc.enc"
    stored = s3_backend.get_object(Bucket=BUCKET, Key=key)["Body"].read()
    assert not stored.startswith(b"%PDF-")
    assert await StorageService.get_file(key) == b"%PDF-1.4 hello"


async def test_s3_delete_is_idempotent(s3_backend):
    key = await StorageService.save_file("gone", b"%PDF-x")
    await StorageService.delete_file(key)
    await StorageService.delete_file(key)
    assert _keys(s3_backend) == []


async def test_full_flow_on_s3(client, headers, section, upload, s3_backend):
    version = await upload(section["id"])
    sid = next(iter(version["content"]))
    await client.patch(f"/api/v1/versions/{version['id']}", json={"updated_content": {sid: "On S3"}}, headers=headers)
    assert len(_keys(s3_backend)) == 2
    public = await client.get(f"/api/v1/public/{section['shareable_slug']}")
    assert public.status_code == 200 and b"%PDF-" in public.content
    await client.delete(f"/api/v1/versions/{version['id']}", headers=headers)
    assert _keys(s3_backend) == []
