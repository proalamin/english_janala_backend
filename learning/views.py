from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import Lesson, Segment, Vocabulary
from .serializers import LessonSerializer, SegmentSerializer, VocabularySerializer


class VocabularyPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 500


class SegmentListCreateAPIView(generics.ListCreateAPIView):
    queryset = Segment.objects.all()
    serializer_class = SegmentSerializer


class SegmentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Segment.objects.all()
    serializer_class = SegmentSerializer

    def destroy(self, request, *args, **kwargs):
        segment = self.get_object()
        try:
            segment.delete()
        except ProtectedError:
            return Response(
                {
                    'detail': 'This segment has bundles. Delete or move those bundles first.'
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class SegmentLessonsListAPIView(generics.ListCreateAPIView):
    serializer_class = LessonSerializer

    def get_queryset(self):
        segment_id = self.kwargs['segment_id']
        get_object_or_404(Segment, pk=segment_id)
        return Lesson.objects.filter(segment_id=segment_id).order_by('serial')

    def perform_create(self, serializer):
        segment = get_object_or_404(Segment, pk=self.kwargs['segment_id'])
        serializer.save(segment=segment)


class SegmentVocabularyCreateAPIView(generics.CreateAPIView):
    """Admin adds a word to a segment; the open (non-full) bundle is picked automatically,
    or a new bundle is created when every existing bundle is full."""
    serializer_class = VocabularySerializer

    def create(self, request, *args, **kwargs):
        segment = get_object_or_404(Segment, pk=self.kwargs['segment_id'])
        word = (request.data.get('word') or '').strip()

        if word and Vocabulary.objects.filter(lesson__segment=segment, word__iexact=word).exists():
            return Response(
                {'word': ['This word already exists in this segment.']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bundle = segment.get_open_bundle()
        data = request.data.copy()
        data['lesson'] = bundle.id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class LessonListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = LessonSerializer

    def get_queryset(self):
        queryset = Lesson.objects.select_related('segment').all()
        segment_id = self.request.query_params.get('segment')
        if segment_id:
            queryset = queryset.filter(segment_id=segment_id)
        return queryset


class LessonDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Lesson.objects.select_related('segment').all()
    serializer_class = LessonSerializer

    def destroy(self, request, *args, **kwargs):
        lesson = self.get_object()
        try:
            lesson.delete()
        except ProtectedError:
            return Response(
                {
                    'detail': 'This lesson has vocabulary records. Delete or move those vocabulary records first.'
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class VocabularyListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = VocabularySerializer
    pagination_class = VocabularyPagination

    def get_queryset(self):
        queryset = Vocabulary.objects.select_related('lesson', 'lesson__segment').all()
        difficulty = self.request.query_params.get('difficulty')
        part_of_speech = self.request.query_params.get('part_of_speech')
        segment_id = self.request.query_params.get('segment')
        lesson_id = self.request.query_params.get('lesson')
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        if part_of_speech:
            queryset = queryset.filter(part_of_speech=part_of_speech)
        if segment_id:
            queryset = queryset.filter(lesson__segment_id=segment_id)
        if lesson_id:
            queryset = queryset.filter(lesson_id=lesson_id)
        return queryset


class VocabularyDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Vocabulary.objects.select_related('lesson').all()
    serializer_class = VocabularySerializer


class LessonVocabularyListAPIView(generics.ListAPIView):
    serializer_class = VocabularySerializer

    def get_queryset(self):
        lesson_id = self.kwargs['lesson_id']
        get_object_or_404(Lesson, pk=lesson_id)
        return Vocabulary.objects.select_related('lesson').filter(lesson_id=lesson_id)


class VocabularySearchAPIView(generics.ListAPIView):
    serializer_class = VocabularySerializer

    def get_queryset(self):
        query = self.request.query_params.get('q', '').strip()
        difficulty = self.request.query_params.get('difficulty')
        part_of_speech = self.request.query_params.get('part_of_speech')
        segment_id = self.request.query_params.get('segment')
        queryset = Vocabulary.objects.select_related('lesson', 'lesson__segment').all()
        if query:
            queryset = queryset.filter(Q(word__icontains=query) | Q(meaning__icontains=query))
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        if part_of_speech:
            queryset = queryset.filter(part_of_speech=part_of_speech)
        if segment_id:
            queryset = queryset.filter(lesson__segment_id=segment_id)
        return queryset.order_by('lesson__title', 'word')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'results': serializer.data,
        })
