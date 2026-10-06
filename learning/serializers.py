from django.db.models import Max

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
    serial = serializers.ReadOnlyField()

    class Meta:
        model = Lesson
        fields = [
            'id',
            'segment',
            'segment_name',
            'serial',
            'title',
            'description',
            'vocabulary_count',
            'is_full',
            'capacity',
            'created_at',
            'updated_at',
        ]
        extra_kwargs = {
            'title': {'required': False, 'allow_blank': True},
            'segment': {'required': False},
        }

    def get_capacity(self, obj):
        return BUNDLE_CAPACITY

    def validate_title(self, value):
        title = value.strip() if value else ''
        if title:
            exists = Lesson.objects.filter(title__iexact=title)
            if self.instance:
                exists = exists.exclude(pk=self.instance.pk)
            if exists.exists():
                raise serializers.ValidationError('A bundle with this title already exists.')
        return title

    def create(self, validated_data):
        segment = validated_data.get('segment')
        if not segment:
            raise serializers.ValidationError({'segment': 'Segment is required.'})
        next_serial = (segment.bundles.aggregate(Max('serial'))['serial__max'] or 0) + 1
        if not validated_data.get('title'):
            validated_data['title'] = f'{segment.name} - Bundle {next_serial}'
        validated_data['serial'] = next_serial
        return super().create(validated_data)


class VocabularySerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    segment_name = serializers.CharField(source='lesson.segment.name', read_only=True)
    bundle_serial = serializers.IntegerField(source='lesson.serial', read_only=True)

    class Meta:
        model = Vocabulary
        fields = [
            'id',
            'lesson',
            'lesson_title',
            'segment_name',
            'bundle_serial',
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

    def validate_synonyms(self, value):
        return self._clean_word_meaning_list(value, 'synonyms')

    def validate_antonyms(self, value):
        return self._clean_word_meaning_list(value, 'antonyms')

    def _clean_word_meaning_list(self, value, field_name):
        if value in (None, ''):
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError(f'{field_name} must be a list of {{word, meaning}} entries.')

        cleaned = []
        for entry in value:
            if not isinstance(entry, dict):
                raise serializers.ValidationError(f'Each {field_name} entry must be an object with word and meaning.')
            word = (entry.get('word') or '').strip()
            meaning = (entry.get('meaning') or '').strip()
            if not word:
                continue
            cleaned.append({'word': word, 'meaning': meaning})
        return cleaned

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
