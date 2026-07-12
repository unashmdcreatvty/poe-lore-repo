from django.contrib import admin
from .models import Entry, Tag, EntryTag, Vote, Comment


class EntryTagInline(admin.TabularInline):
    model = EntryTag
    extra = 1
    readonly_fields = ('applied_by', 'created_at')


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ('source_name', 'source_type', 'game', 'status', 'submitted_by', 'created_at')
    list_filter = ('game', 'status', 'source_type')
    search_fields = ('text', 'source_name', 'context_note')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    inlines = [EntryTagInline]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'status')
    list_filter = ('category', 'status')
    search_fields = ('name',)
    ordering = ('category', 'name')


@admin.register(EntryTag)
class EntryTagAdmin(admin.ModelAdmin):
    list_display = ('tag', 'entry', 'applied_by', 'created_at')
    list_filter = ('tag__category', 'tag__status')
    search_fields = ('tag__name', 'entry__source_name')
    readonly_fields = ('created_at',)


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'vote_type', 'target_type', 'target_id', 'created_at')
    list_filter = ('vote_type', 'target_type')
    readonly_fields = ('created_at',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'entry', 'parent_comment', 'created_at')
    search_fields = ('text', 'user__display_name')
    readonly_fields = ('created_at',)
