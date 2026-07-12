from django.db import models
from django.conf import settings


class Entry(models.Model):
    SOURCE_TYPE_CHOICES = [
        ('dialogue', 'Dialogue'),
        ('flavour_text', 'Flavour Text'),
        ('environmental', 'Environmental'),
        ('quest_text', 'Quest Text'),
        ('lore_object', 'Lore Object'),
        ('skill_gem_description', 'Skill Gem Description'),
        ('other', 'Other'),
    ]

    GAME_CHOICES = [
        ('poe1', 'Path of Exile 1'),
        ('poe2', 'Path of Exile 2'),
    ]

    STATUS_CHOICES = [
        ('current', 'Current'),
        ('replaced', 'Replaced'),
        ('removed', 'Removed'),
        ('datamined', 'Datamined'),
    ]

    text = models.TextField()
    source_name = models.CharField(max_length=200)
    source_type = models.CharField(max_length=30, choices=SOURCE_TYPE_CHOICES)
    game = models.CharField(max_length=10, choices=GAME_CHOICES)
    patch_added = models.CharField(max_length=20, blank=True)
    patch_removed = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='current')
    context_note = models.TextField(blank=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='submitted_entries',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'entries'

    def __str__(self):
        return f"{self.source_name}: {self.text[:60]}"


class Tag(models.Model):
    CATEGORY_CHOICES = [
        ('character', 'Character'),
        ('faction', 'Faction'),
        ('mechanic', 'Mechanic'),
        ('act', 'Act'),
        ('location', 'Location'),
        ('lore_topic', 'Lore Topic'),
        ('game_system', 'Game System'),
        ('class', 'Class'),
    ]

    STATUS_CHOICES = [
        ('corroborated', 'Corroborated'),
        ('uncorroborated', 'Uncorroborated'),
    ]

    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uncorroborated')

    def __str__(self):
        return f"{self.name} ({self.category})"


class EntryTag(models.Model):
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name='entry_tags')
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='entry_tags')
    applied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='applied_tags',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('entry', 'tag')

    def __str__(self):
        return f"{self.tag.name} on {self.entry}"


class Vote(models.Model):
    VOTE_TYPE_CHOICES = [
        ('up', 'Upvote'),
        ('down', 'Downvote'),
    ]

    TARGET_TYPE_CHOICES = [
        ('entry', 'Entry'),
        ('entry_tag', 'Entry Tag'),
        ('context_note', 'Context Note'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='votes',
    )
    vote_type = models.CharField(max_length=4, choices=VOTE_TYPE_CHOICES)
    target_type = models.CharField(max_length=20, choices=TARGET_TYPE_CHOICES)
    target_id = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'target_type', 'target_id')

    def __str__(self):
        return f"{self.user} {self.vote_type}voted {self.target_type} #{self.target_id}"


class Comment(models.Model):
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    text = models.TextField()
    parent_comment = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user} on {self.entry}"
