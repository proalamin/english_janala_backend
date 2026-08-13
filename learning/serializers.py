from rest_framework import serializers

from .models import Lesson, Vocabulary


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'description', 'created_at', 'updated_at']

    def validate_title(self, value):
        title = value.strip()
        if not title:
            raise serializers.ValidationError('Lesson title is required.')

        exists = Lesson.objects.filter(title__iexact=title)
        if self.instance:
            exists = exists.exclude(pk=self.instance.pk)
        if exists.exists():
            raise serializers.ValidationError('A lesson with this title already exists.')

        return title


class VocabularySerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)

    class Meta:
        model = Vocabulary
        fields = [
            'id',
            'lesson',
            'lesson_title',
            'word',
            'meaning',
            'pronunciation',
            'example',
            'created_at',
            'updated_at',
        ]

    def validate_word(self, value):
        word = value.strip()
        if not word:
            raise serializers.ValidationError('Word is required.')
        return word

    def validate_meaning(self, value):
        meaning = value.strip()
        if not meaning:
            raise serializers.ValidationError('Meaning is required.')
        return meaning

    def validate(self, attrs):
        lesson = attrs.get('lesson') or getattr(self.instance, 'lesson', None)
        word = attrs.get('word') or getattr(self.instance, 'word', None)

        if 'word' in attrs:
            attrs['word'] = attrs['word'].strip()
            word = attrs['word']
        if 'meaning' in attrs:
            attrs['meaning'] = attrs['meaning'].strip()
        if 'pronunciation' in attrs:
            attrs['pronunciation'] = attrs['pronunciation'].strip()
        if 'example' in attrs:
            attrs['example'] = attrs['example'].strip()

        if not lesson:
            raise serializers.ValidationError({'lesson': 'Lesson is required.'})

        if lesson and word:
            exists = Vocabulary.objects.filter(lesson=lesson, word__iexact=word)
            if self.instance:
                exists = exists.exclude(pk=self.instance.pk)
            if exists.exists():
                raise serializers.ValidationError({'word': 'This word already exists in the selected lesson.'})

        return attrs
