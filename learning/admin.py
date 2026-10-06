from django.contrib import admin

from .models import Lesson, Segment, Vocabulary


@admin.register(Segment)
class SegmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'segment', 'vocabulary_count', 'created_at', 'updated_at')
    list_filter = ('segment',)
    search_fields = ('title', 'description')
    ordering = ('title',)


@admin.register(Vocabulary)
class VocabularyAdmin(admin.ModelAdmin):
    list_display = ('id', 'word', 'meaning', 'lesson', 'part_of_speech', 'difficulty', 'created_at', 'updated_at')
    list_filter = ('lesson', 'difficulty', 'part_of_speech')
    search_fields = ('word', 'meaning', 'pronunciation', 'example', 'synonyms', 'antonyms', 'lesson__title')
    ordering = ('lesson__title', 'word')
