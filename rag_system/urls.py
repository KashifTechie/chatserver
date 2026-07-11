from django.urls import path
from rag_system.views import RagStoringAPIView

urlpatterns = [
    path("/store-vector", RagStoringAPIView.as_view(), name="store-vector")
]