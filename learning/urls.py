from django.urls import path

from .views import (
    LessonDetailAPIView,
    LessonListCreateAPIView,
    LessonVocabularyListAPIView,
    VocabularyDetailAPIView,
    VocabularyListCreateAPIView,
    VocabularySearchAPIView,
)


urlpatterns = [
    path('lessons/', LessonListCreateAPIView.as_view(), name='lesson-list-create'),
    path('lessons/<int:pk>/', LessonDetailAPIView.as_view(), name='lesson-detail'),
    path('lessons/<int:lesson_id>/vocabulary/', LessonVocabularyListAPIView.as_view(), name='lesson-vocabulary'),
    path('vocabulary/', VocabularyListCreateAPIView.as_view(), name='vocabulary-list-create'),
    path('vocabulary/<int:pk>/', VocabularyDetailAPIView.as_view(), name='vocabulary-detail'),
    path('vocabulary/search/', VocabularySearchAPIView.as_view(), name='vocabulary-search'),
]