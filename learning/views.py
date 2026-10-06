from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response

from .models import Lesson, Vocabulary
from .serializers import LessonSerializer, VocabularySerializer


class LessonListCreateAPIView(generics.ListCreateAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer


class LessonDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Lesson.objects.all()
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

    def get_queryset(self):
        queryset = Vocabulary.objects.select_related('lesson').all()
        difficulty = self.request.query_params.get('difficulty')
        part_of_speech = self.request.query_params.get('part_of_speech')
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        if part_of_speech:
            queryset = queryset.filter(part_of_speech=part_of_speech)
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
        queryset = Vocabulary.objects.select_related('lesson').all()
        if query:
            queryset = queryset.filter(Q(word__icontains=query) | Q(meaning__icontains=query))
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        return queryset.order_by('lesson__title', 'word')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'results': serializer.data,
        })
