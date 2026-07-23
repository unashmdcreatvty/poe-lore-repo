from collections import defaultdict

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Entry, Vote, Tag, EntryTag, Comment
from .forms import EntryForm, CommentForm
from .confidence import get_confidence

User = get_user_model()


def home(request):
    entries = Entry.objects.order_by('-created_at')

    q = request.GET.get('q', '').strip()
    tag_ids = request.GET.getlist('tags')

    if q:
        search_vector = SearchVector('text', 'source_name', 'context_note')
        search_query = SearchQuery(q)
        entries = (
            entries
            .annotate(rank=SearchRank(search_vector, search_query))
            .filter(rank__gt=0)
            .order_by('-rank')
        )

    selected_tags = []
    if tag_ids:
        try:
            tag_ids_int = [int(t) for t in tag_ids if t]
            if tag_ids_int:
                selected_tags = list(Tag.objects.filter(pk__in=tag_ids_int))
                for tag in selected_tags:
                    entries = entries.filter(entry_tags__tag=tag)
                entries = entries.distinct()
        except ValueError:
            pass

    return render(request, 'home.html', {
        'entries': entries,
        'q': q,
        'selected_tags': selected_tags,
    })


def entry_detail(request, pk):
    entry = get_object_or_404(Entry, pk=pk)

    entry_tags = entry.entry_tags.select_related('tag').all()
    corroborated_tags = [et for et in entry_tags if et.tag.status == 'corroborated']
    uncorroborated_tags = [et for et in entry_tags if et.tag.status == 'uncorroborated']

    entry_votes = Vote.objects.filter(target_type='entry', target_id=pk)
    entry_upvotes = entry_votes.filter(vote_type='up').count()
    entry_downvotes = entry_votes.filter(vote_type='down').count()
    entry_score = entry_upvotes - entry_downvotes
    entry_confidence = get_confidence(entry_upvotes, entry_downvotes)

    note_score = None
    note_confidence = None
    if entry.context_note:
        note_votes = Vote.objects.filter(target_type='context_note', target_id=pk)
        note_upvotes = note_votes.filter(vote_type='up').count()
        note_downvotes = note_votes.filter(vote_type='down').count()
        note_score = note_upvotes - note_downvotes
        note_confidence = get_confidence(note_upvotes, note_downvotes)

    user_entry_vote = None
    user_note_vote = None
    if request.user.is_authenticated:
        user_votes = Vote.objects.filter(
            user=request.user,
            target_type__in=['entry', 'context_note'],
            target_id=pk,
        ).values('target_type', 'vote_type')
        for v in user_votes:
            if v['target_type'] == 'entry':
                user_entry_vote = v['vote_type']
            elif v['target_type'] == 'context_note':
                user_note_vote = v['vote_type']

    comments = (
        entry.comments
        .filter(parent_comment=None)
        .select_related('user')
        .prefetch_related('replies__user')
        .order_by('created_at')
    )

    return render(request, 'entry_detail.html', {
        'entry': entry,
        'corroborated_tags': corroborated_tags,
        'uncorroborated_tags': uncorroborated_tags,
        'entry_score': entry_score,
        'entry_confidence': entry_confidence,
        'user_entry_vote': user_entry_vote,
        'note_score': note_score,
        'note_confidence': note_confidence,
        'user_note_vote': user_note_vote,
        'comments': comments,
        'comment_form': CommentForm(),
    })


@login_required
def add_comment(request, pk):
    entry = get_object_or_404(Entry, pk=pk)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.entry = entry
            comment.user = request.user

            parent_id = request.POST.get('parent_comment')
            if parent_id:
                comment.parent_comment = get_object_or_404(Comment, pk=parent_id, entry=entry)

            comment.save()
    return redirect('lore:entry_detail', pk=pk)


@login_required
def submit_entry(request):
    if request.method == 'POST':
        form = EntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.submitted_by = request.user
            entry.save()

            for raw_name in form.cleaned_data.get('tags', '').split(','):
                name = raw_name.strip()
                if not name:
                    continue
                tag = Tag.objects.filter(name__iexact=name).first()
                if tag is None:
                    tag = Tag.objects.create(name=name, category='lore_topic')
                EntryTag.objects.get_or_create(
                    entry=entry,
                    tag=tag,
                    defaults={'applied_by': request.user},
                )

            return redirect('lore:entry_detail', pk=entry.pk)
    else:
        form = EntryForm()
    return render(request, 'submit_entry.html', {'form': form})


def tag_browser(request):
    tags = (
        Tag.objects
        .filter(status='corroborated')
        .annotate(entry_count=Count('entry_tags'))
        .order_by('name')
    )

    by_category = defaultdict(list)
    for tag in tags:
        by_category[tag.category].append(tag)

    category_labels = dict(Tag.CATEGORY_CHOICES)
    categories = [
        (category_labels[key], by_category[key])
        for key, _ in Tag.CATEGORY_CHOICES
        if key in by_category
    ]

    return render(request, 'tag_browser.html', {'categories': categories})


def tags_autocomplete(request):
    q = request.GET.get('q', '').strip()
    tags = Tag.objects.filter(name__icontains=q).order_by('name')[:20]
    category_labels = dict(Tag.CATEGORY_CHOICES)
    data = [
        {
            'id': tag.pk,
            'name': tag.name,
            'category': category_labels.get(tag.category, tag.category),
        }
        for tag in tags
    ]
    return JsonResponse({'tags': data})


def user_profile(request, pk):
    profile_user = get_object_or_404(User, pk=pk)
    entries = Entry.objects.filter(submitted_by=profile_user).order_by('-created_at')
    total_submitted = entries.count()

    entry_pks = list(entries.values_list('pk', flat=True))
    vote_rows = (
        Vote.objects
        .filter(target_type='entry', target_id__in=entry_pks)
        .values('target_id', 'vote_type')
        .annotate(count=Count('id'))
    )

    vote_map = defaultdict(lambda: {'up': 0, 'down': 0})
    for row in vote_rows:
        vote_map[row['target_id']][row['vote_type']] = row['count']

    high_confidence_count = sum(
        1 for pk in entry_pks
        if get_confidence(vote_map[pk]['up'], vote_map[pk]['down']) == 'green'
    )

    return render(request, 'user_profile.html', {
        'profile_user': profile_user,
        'entries': entries,
        'total_submitted': total_submitted,
        'high_confidence_count': high_confidence_count,
    })


@login_required
def cast_vote(request):
    if request.method != 'POST':
        return redirect('lore:home')

    next_url = request.POST.get('next') or '/'
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = '/'

    target_type = request.POST.get('target_type')
    vote_type = request.POST.get('vote_type')

    if target_type not in {'entry', 'entry_tag', 'context_note'}:
        return redirect(next_url)
    if vote_type not in {'up', 'down'}:
        return redirect(next_url)

    try:
        target_id = int(request.POST.get('target_id', ''))
    except ValueError:
        return redirect(next_url)

    existing = Vote.objects.filter(
        user=request.user,
        target_type=target_type,
        target_id=target_id,
    ).first()

    if existing is None:
        Vote.objects.create(
            user=request.user,
            target_type=target_type,
            target_id=target_id,
            vote_type=vote_type,
        )
    elif existing.vote_type == vote_type:
        existing.delete()
    else:
        existing.vote_type = vote_type
        existing.save()

    return redirect(next_url)
