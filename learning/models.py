from django.core.exceptions import ValidationError
from django.db import models

BUNDLE_CAPACITY = 20


class Segment(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def clean(self):
        if not self.name or not self.name.strip():
            raise ValidationError({'name': 'Segment name is required.'})
        self.name = self.name.strip()
        self.description = self.description.strip() if self.description else ''

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Lesson(models.Model):
    segment = models.ForeignKey(Segment, on_delete=models.PROTECT, related_name='bundles')
    title = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']

    def clean(self):
        if not self.title or not self.title.strip():
            raise ValidationError({'title': 'Lesson title is required.'})
        self.title = self.title.strip()
        self.description = self.description.strip() if self.description else ''

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def vocabulary_count(self):
        return self.vocabulary_words.count()

    @property
    def is_full(self):
        return self.vocabulary_count >= BUNDLE_CAPACITY

    def __str__(self):
        return self.title


class Vocabulary(models.Model):
    class Difficulty(models.TextChoices):
        EASY = 'easy', 'Easy'
        MEDIUM = 'medium', 'Medium'
        HARD = 'hard', 'Hard'

    class PartOfSpeech(models.TextChoices):
        NOUN = 'noun', 'Noun'
        VERB = 'verb', 'Verb'
        ADJECTIVE = 'adjective', 'Adjective'
        ADVERB = 'adverb', 'Adverb'
        PRONOUN = 'pronoun', 'Pronoun'
        PREPOSITION = 'preposition', 'Preposition'
        CONJUNCTION = 'conjunction', 'Conjunction'
        INTERJECTION = 'interjection', 'Interjection'

    lesson = models.ForeignKey(Lesson, on_delete=models.PROTECT, related_name='vocabulary_words')
    word = models.CharField(max_length=100)
    meaning = models.CharField(max_length=255)
    pronunciation = models.CharField(max_length=150, blank=True)
    example = models.TextField(blank=True)
    part_of_speech = models.CharField(max_length=20, choices=PartOfSpeech.choices, blank=True)
    difficulty = models.CharField(max_length=10, choices=Difficulty.choices, default=Difficulty.MEDIUM)
    synonyms = models.CharField(max_length=255, blank=True, help_text='Comma-separated synonyms.')
    antonyms = models.CharField(max_length=255, blank=True, help_text='Comma-separated antonyms.')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['lesson__title', 'word']
        constraints = [
            models.UniqueConstraint(fields=['lesson', 'word'], name='unique_word_within_lesson'),
        ]

    def __str__(self):
        return f'{self.word} - {self.lesson.title}'