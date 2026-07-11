# pyrefly: ignore [missing-import]
from django.db import models
# pyrefly: ignore [missing-import]
from pgvector.django import VectorField, HnswIndex
import uuid

class RagStore(models.Model):

    class SourceType(models.TextChoices):
        PDF = "PDF"
        DOCX = "DOCX"
        TXT = "TXT"
        CSV = "CSV"
        URL = "URL"

    class StatusChoices(models.TextChoices):
        PENDING = "PENDING", "PENDING"
        PROCESSING = "PROCESSING", "PROCESSING"
        PROCESSED = "PROCESSED", "PROCESSED"
        FAILED = "FAILED", "FAILED"
    uuid = models.UUIDField(default=uuid.uuid4,editable=False,unique=True,)
    title = models.CharField(max_length=128, blank=True, null=True)
    type = models.CharField(max_length=50, choices=SourceType)
    status = models.CharField(max_length=50, choices=StatusChoices)
    text_content = models.TextField(
        blank=True,
        null=True
    )
    file_content = models.FileField(
        upload_to="rag/",
        blank=True,
        null=True
    )
    url_content = models.URLField(
        blank=True,
        null=True
    )
    created_at = models.DateField(auto_created=True, blank=True, null=True)

class RagChuks(models.Model):
    rag_store = models.ForeignKey(
        RagStore,
        on_delete=models.CASCADE,
        related_name="chunks",
    )
    chunk_index = models.IntegerField()
    content = models.TextField()
    embedding = VectorField(dimensions=1536)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            HnswIndex(
                name="rag_embedding_hnsw",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
        ]

