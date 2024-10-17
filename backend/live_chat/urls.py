from django.urls import path
from .views import RelationshipStatusView

urlpatterns = [
    path('users/relationships/<int:user_id_1>/<int:user_id_2>/', RelationshipStatusView.as_view(), name='relationship_status'),
]