from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework import permissions
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import Lesson, Segment, Vocabulary, WordProgress
from .serializers import LessonSerializer, SegmentSerializer, VocabularySerializer


class VocabularyPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 500


class MarkWordsKnownAPIView(generics.GenericAPIView):
    """Logged-in users call this after correctly matching words (e.g. in
    Match Words with Meanings) so progress is saved to their account."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        vocabulary_ids = request.data.get('vocabulary_ids')
        if not isinstance(vocabulary_ids, list) or not vocabulary_ids:
            return Response({'detail': 'vocabulary_ids must be a non-empty list.'}, status=status.HTTP_400_BAD_REQUEST)

        valid_ids = set(
            Vocabulary.objects.filter(id__in=vocabulary_ids).values_list('id', flat=True)
        )
        created = 0
        for vocab_id in valid_ids:
            _, was_created = WordProgress.objects.get_or_create(user=request.user, vocabulary_id=vocab_id)
            if was_created:
                created += 1

        return Response({'marked': created, 'already_known': len(valid_ids) - created}, status=status.HTTP_200_OK)


class ProgressSummaryAPIView(generics.GenericAPIView):
    """Everything a student dashboard needs in one call: overall totals,
    per-segment progress, bundles currently in progress / completed, and
    the most recently learned words."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        total_words = Vocabulary.objects.count()
        total_known = WordProgress.objects.filter(user=user).count()

        segments = Segment.objects.all()
        segment_data = SegmentSerializer(segments, many=True, context={'request': request}).data

        lessons = Lesson.objects.select_related('segment').all()
        lesson_data = LessonSerializer(lessons, many=True, context={'request': request}).data

        in_progress_bundles = [
            item for item in lesson_data
            if item['vocabulary_count'] > 0 and 0 < (item['known_count'] or 0) < item['vocabulary_count']
        ]
        completed_bundles = [
            item for item in lesson_data
            if item['vocabulary_count'] > 0 and item['known_count'] == item['vocabulary_count']
        ]

        recent_entries = (
            WordProgress.objects.filter(user=user)
            .select_related('vocabulary', 'vocabulary__lesson')
            .order_by('-learned_at')[:8]
        )
        recent_words = [
            {
                'id': entry.vocabulary.id,
                'word': entry.vocabulary.word,
                'meaning': entry.vocabulary.meaning,
                'lesson_title': entry.vocabulary.lesson.title,
                'learned_at': entry.learned_at,
            }
            for entry in recent_entries
        ]

        return Response({
            'total_known': total_known,
            'total_words': total_words,
            'progress_percent': round((total_known / total_words) * 100) if total_words else 0,
            'segments': segment_data,
            'in_progress_bundles': in_progress_bundles,
            'completed_bundles': completed_bundles,
            'recent_words': recent_words,
        })


class IsAdminOrReadOnly(permissions.BasePermission):
    """Anyone can read (GET/HEAD/OPTIONS); only staff/admin accounts can write."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


def filter_locked_bundles(queryset, request, lesson_field='lesson'):
    """Anonymous visitors only see words from free-preview bundles."""
    if request.user and request.user.is_authenticated:
        return queryset
    return queryset.filter(**{f'{lesson_field}__is_free': True})


class SegmentListCreateAPIView(generics.ListCreateAPIView):
    queryset = Segment.objects.all()
    serializer_class = SegmentSerializer
    permission_classes = [IsAdminOrReadOnly]


class SegmentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Segment.objects.all()
    serializer_class = SegmentSerializer
    permission_classes = [IsAdminOrReadOnly]

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
    permission_classes = [IsAdminOrReadOnly]

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
    permission_classes = [permissions.IsAdminUser]

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
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = Lesson.objects.select_related('segment').all()
        segment_id = self.request.query_params.get('segment')
        if segment_id:
            queryset = queryset.filter(segment_id=segment_id)
        return queryset


class LessonDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Lesson.objects.select_related('segment').all()
    serializer_class = LessonSerializer
    permission_classes = [IsAdminOrReadOnly]

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
    permission_classes = [IsAdminOrReadOnly]

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
        return filter_locked_bundles(queryset, self.request)


class VocabularyDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Vocabulary.objects.select_related('lesson').all()
    serializer_class = VocabularySerializer
    permission_classes = [IsAdminOrReadOnly]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.lesson.is_free and not (request.user and request.user.is_authenticated):
            raise PermissionDenied('Please log in to access this bundle.')
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class LessonVocabularyListAPIView(generics.ListAPIView):
    serializer_class = VocabularySerializer

    def get_queryset(self):
        lesson_id = self.kwargs['lesson_id']
        lesson = get_object_or_404(Lesson, pk=lesson_id)
        request = self.request
        if not lesson.is_free and not (request.user and request.user.is_authenticated):
            raise PermissionDenied('Please log in to access this bundle.')
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
        queryset = filter_locked_bundles(queryset, self.request)
        return queryset.order_by('lesson__title', 'word')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'results': serializer.data,
        })
