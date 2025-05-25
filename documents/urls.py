from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet

router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')

urlpatterns = router.urls

from django.urls import path
from .views import DocumentQAView

urlpatterns += [
    path('documents/<int:pk>/ask/', DocumentQAView.as_view(), name='document_qa'),
]