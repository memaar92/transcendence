from django.urls import path
from .views import live_chat, RelationshipStatusView

urlpatterns = [
    path('live_chat/', live_chat, name='live_chat'),
    path('users/relationships/<int:user_id_1>/<int:user_id_2>/', RelationshipStatusView.as_view(), name='relationship_status'),
]