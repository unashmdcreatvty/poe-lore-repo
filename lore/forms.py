from django import forms
from .models import Entry


class EntryForm(forms.ModelForm):
    tags = forms.CharField(
        required=False,
        label='Tags',
        help_text='Tag names separated by commas. New tags are created as uncorroborated and categorised by an admin.',
        widget=forms.TextInput(attrs={'placeholder': 'e.g. Hinekora, Karui, Act 4'}),
    )

    class Meta:
        model = Entry
        fields = ['text', 'source_name', 'source_type', 'game', 'patch_added', 'context_note']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 6}),
            'context_note': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'patch_added': 'Patch version',
        }
        help_texts = {
            'patch_added': 'The patch in which this text was first confirmed (e.g. 0.5.0). Leave blank if unknown.',
            'context_note': 'Describe the conditions under which you encountered this text — character class, quest state, etc.',
        }
