from django.urls import path
from .views import HuggingFaceAi

urlpatterns = [ 
    path("/huggingface", HuggingFaceAi.as_view(), name="huggingface-ai"),
]