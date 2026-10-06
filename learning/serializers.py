from rest_framework import serializers

from .models import BUNDLE_CAPACITY, Lesson, Segment, Vocabulary


class SegmentSerializer(serializers.ModelSerializer):
    bundle_count = serializers.SerializerMethodField()

    class Meta:
        model = Segment
        fields = ['id', 'name', 'description', 'bundle_count', 'created_at', 'updated_at']

    def get_bundle_count(self, obj):
        return obj.bundles.count()

    def validate_name(self, value):
        name = value.strip()
        if not name:
            raise serializers.ValidationError('Segment name is required.')

        exists = Segment.objects.filter(name__iexact=name)
        if self.instance:
            exists = exists.exclude(pk=self.instance.pk)
        if exists.exists():
            raise serializers.ValidationError('A segment with this name already exists.')

        return name


class LessonSerializer(serializers.ModelSerializer):
    segment_name = serializers.CharField(source='segment.name', read_only=True)
    vocabulary_count = serializers.ReadOnlyField()
    is_full = serializers.ReadOnlyField()
    capacity = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            'id',
            'segment',
            'segment_name',
            'title',
            'description',
            'vocabulary_count',
            'is_full',
            'capacity',
            'created_at',
            'updated_at',
        ]

    def get_capacity(self, obj):
        return BUNDLE_CAPACITY

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
    segment_name = serializers.CharField(source='lesson.segment.name', read_only=True)

    class Meta:
        model = Vocabulary
        fields = [
            'id',
            'lesson',
            'lesson_title',
            'segment_name',
            'word',
            'meaning',
            'pronunciation',
            'example',
            'part_of_speech',
            'difficulty',
            'synonyms',
            'antonyms',
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
        if 'synonyms' in attrs:
            attrs['synonyms'] = attrs['synonyms'].strip()
        if 'antonyms' in attrs:
            attrs['antonyms'] = attrs['antonyms'].strip()

        if not lesson:
            raise serializers.ValidationError({'lesson': 'Lesson is required.'})

        if lesson:
            current_lesson = getattr(self.instance, 'lesson', None)
            if lesson != current_lesson and lesson.vocabulary_count >= BUNDLE_CAPACITY:
                raise serializers.ValidationError({
                    'lesson': f'This bundle already has {BUNDLE_CAPACITY} words (max). Please choose or create another bundle.',
                })

        if lesson and word:
            exists = Vocabulary.objects.filter(lesson=lesson, word__iexact=word)
            if self.instance:
                exists = exists.exclude(pk=self.instance.pk)
            if exists.exists():
                raise serializers.ValidationError({'word': 'This word already exists in the selected lesson.'})

        return attrs
