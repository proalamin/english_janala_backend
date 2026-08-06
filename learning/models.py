from django.db import models


class Lesson(models.Model):
    title = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class Vocabulary(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.PROTECT, related_name='vocabulary_words')
    word = models.CharField(max_length=100)
    meaning = models.CharField(max_length=255)
    pronunciation = models.CharField(max_length=150, blank=True)
    example = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['lesson__title', 'word']
        constraints = [
            models.UniqueConstraint(fields=['lesson', 'word'], name='unique_word_within_lesson'),
        ]

    def __str__(self):
        return f'{self.word} - {self.lesson.title}'