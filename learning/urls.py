from django.urls import path

from .views import (
    LessonDetailAPIView,
    LessonListCreateAPIView,
    LessonVocabularyListAPIView,
    MarkWordsKnownAPIView,
    ProgressSummaryAPIView,
    SegmentDetailAPIView,
    SegmentListCreateAPIView,
    SegmentLessonsListAPIView,
    SegmentVocabularyCreateAPIView,
    VocabularyDetailAPIView,
    VocabularyListCreateAPIView,
    VocabularySearchAPIView,
)


urlpatterns = [
    path('progress/words/', MarkWordsKnownAPIView.as_view(), name='mark-words-known'),
    path('progress/summary/', ProgressSummaryAPIView.as_view(), name='progress-summary'),
    path('segments/', SegmentListCreateAPIView.as_view(), name='segment-list-create'),
    path('segments/<int:pk>/', SegmentDetailAPIView.as_view(), name='segment-detail'),
    path('segments/<int:segment_id>/lessons/', SegmentLessonsListAPIView.as_view(), name='segment-lessons'),
    path('segments/<int:segment_id>/vocabulary/', SegmentVocabularyCreateAPIView.as_view(), name='segment-vocabulary-create'),
    path('lessons/', LessonListCreateAPIView.as_view(), name='lesson-list-create'),
    path('lessons/<int:pk>/', LessonDetailAPIView.as_view(), name='lesson-detail'),
    path('lessons/<int:lesson_id>/vocabulary/', LessonVocabularyListAPIView.as_view(), name='lesson-vocabulary'),
    path('vocabulary/', VocabularyListCreateAPIView.as_view(), name='vocabulary-list-create'),
    path('vocabulary/<int:pk>/', VocabularyDetailAPIView.as_view(), name='vocabulary-detail'),
    path('vocabulary/search/', VocabularySearchAPIView.as_view(), name='vocabulary-search'),
]