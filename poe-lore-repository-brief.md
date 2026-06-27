# PoE Lore Repository — Project Brief

## Purpose

A community-driven online repository for Path of Exile 1 and Path of Exile 2 flavour text, NPC dialogue, environmental lore, and item descriptions. The core problem: PoE's lore is scattered across thousands of items, NPC conversations, environmental objects, and mechanical interactions, with no single comprehensive source. Dialogue is class-specific and often patch-specific. The endgame is shared across characters per league, meaning a single player cannot see all unique dialogue variations. Critical lore connections depend on cross-referencing text fragments that most players never encounter together.

The repository allows users to submit text they encounter in-game, tag it with relevant metadata, and collaboratively verify accuracy through a confidence voting system. It also provides a theorycrafting layer through comments.

## Core Design Principles

1. **Anyone can contribute, but accuracy is earned through consensus.** Any user can submit entries and suggest tags, but visibility and trust are tied to community corroboration, not individual authority.
2. **The site owner (Alex) is the sole arbiter of taxonomy and system design.** Tag categories, site structure, and feature decisions are not democratic. Users can suggest changes via comments; Alex decides.
3. **No formal inter-entry linking system.** This was considered and deliberately excluded. The tag and search system handles the vast majority of cross-referencing needs. Direct "this replaced that" links were considered too error-prone and too difficult to visually manage with unverified suggestions. This decision may be revisited in the future.
4. **Simplicity over completeness.** The MVP should do a few things well. Features can be added iteratively based on what the community actually needs.

## Tech Stack

- **Backend framework:** Django (Python)
  - Rationale: Alex has introductory Python experience. Django is opinionated and structured, which suits systematic thinking. Django's built-in admin panel provides an immediate moderation dashboard without custom development. Django's ORM lets Alex interact with the database through Python rather than raw SQL.
- **Database:** PostgreSQL
  - Rationale: Free, powerful, handles full-text search natively (important for searching across dialogue content), and handles tag-based filtering efficiently.
- **Authentication:** Discord OAuth
  - Rationale: The PoE community lives on Discord. Low friction for users, no need to manage passwords.
- **Hosting:** Railway or Render
  - Rationale: Simple deployment for Django apps. Free tier or under $10/month at low traffic. Scales if needed.
- **Frontend:** Django templates initially
  - Rationale: Simpler than a separate frontend framework. Can be upgraded to React or similar later without changing the backend.

## Data Model

### Entry

The atomic unit of content. One entry = one discrete piece of text from the game.

Fields:
- `id` — unique identifier (auto-generated)
- `text` — the actual dialogue, flavour text, or lore content (required)
- `source_name` — who or what says/displays it (NPC name, item name, environmental object name) (required)
- `source_type` — enum: `dialogue`, `flavour_text`, `environmental`, `quest_text`, `lore_object`, `skill_gem_description`, `other`
- `game` — enum: `poe1`, `poe2`
- `patch_added` — the game patch version in which this text was first confirmed (e.g., "0.5.0")
- `patch_removed` — the game patch version in which this text was removed or replaced, if applicable (nullable)
- `status` — enum: `current`, `replaced`, `removed`, `datamined`
  - `current` — confirmed present in the live game as of the latest known patch
  - `replaced` — was in the game but has been changed to different text
  - `removed` — was in the game but has been deleted entirely
  - `datamined` — found in game files but not yet confirmed in-game; auto-greylisted by default
- `context_note` — free-text field where the submitter describes the conditions under which they encountered this text (e.g., "Saw this on my Mercenary after completing the Shambrin quest but before entering Deshar"). This field has its own confidence voting.
- `submitted_by` — reference to the User who submitted it
- `created_at` — timestamp
- `updated_at` — timestamp

### Tag

A label that can be applied to entries for categorization and search.

Fields:
- `id` — unique identifier
- `name` — the tag text (e.g., "Hinekora", "Act 4", "Precursors", "Order of the Djinn")
- `category` — enum: `character`, `faction`, `mechanic`, `act`, `location`, `lore_topic`, `game_system`, `class`
  - Tag categories are controlled exclusively by the site admin. Users cannot create new categories.
- `status` — enum: `corroborated`, `uncorroborated`
  - Tags are created as `uncorroborated` and promoted to `corroborated` once they pass a confirmation threshold

### EntryTag

The join between an Entry and a Tag. Each application of a tag to an entry is separately voteable.

Fields:
- `id` — unique identifier
- `entry` — reference to Entry
- `tag` — reference to Tag
- `applied_by` — reference to the User who applied this tag
- `created_at` — timestamp

This record has its own confidence score derived from votes. A tag application that the community disputes (many downvotes) can be visually demoted or hidden.

### Vote

A single upvote or downvote on a voteable entity.

Fields:
- `id` — unique identifier
- `user` — reference to User (one vote per user per target)
- `vote_type` — enum: `up`, `down`
- `target_type` — enum: `entry`, `entry_tag`, `context_note`
  - Indicates what is being voted on: the entry's accuracy, whether a tag belongs on the entry, or whether the context note is accurate
- `target_id` — the id of the thing being voted on
- `created_at` — timestamp

### User

Fields:
- `id` — unique identifier
- `discord_id` — from OAuth
- `display_name` — from Discord
- `joined_at` — when they first logged in
- `reputation_score` — calculated from history (entries submitted that reached high confidence, votes that aligned with eventual consensus, etc.). Not displayed prominently but used for implicit trust weighting.

### Comment

For theorycrafting and discussion on individual entries.

Fields:
- `id` — unique identifier
- `entry` — reference to Entry
- `user` — reference to User
- `text` — comment content
- `parent_comment` — self-reference for threading (nullable)
- `created_at` — timestamp

## Confidence System

### How It Works

Every voteable element (entry text accuracy, tag applications, context notes) accumulates upvotes and downvotes independently. The net score and the ratio determine a confidence level displayed as a colored indicator.

### Confidence Levels

| Color | Label | Meaning | Rough Criteria |
|-------|-------|---------|----------------|
| Grey | Unconfirmed | Brand new, zero votes | No votes yet |
| Orange | Low Confidence | Some engagement but insufficient corroboration | Fewer than N total votes, slightly positive net |
| Yellow | Moderate Confidence | Reasonable corroboration | N+ total votes, clearly positive net |
| Green | High Confidence | Strong community agreement | High total votes, overwhelmingly positive net |
| Purple | Debated | Significant engagement but no consensus | Many votes on both sides, net score near zero |

Exact thresholds (what N is, what ratios trigger each level) should be calibrated after launch based on actual usage patterns. Start with conservative values and adjust.

### Display

The confidence indicator is compact: `+ [score] -` with the score number colored according to confidence level. Hovering/tapping the score shows a tooltip explaining what the color means.

### Implicit Reputation

Users whose submissions consistently reach High Confidence accumulate implicit reputation. This could eventually be used to give their votes slightly more weight, but this is a future consideration, not an MVP feature. The reputation score is not prominently displayed to users — it's a backend value used for system tuning.

## Tag System

### Two-Tier Visibility

When tags are displayed on an entry:
- **Corroborated tags** appear in the main tag list, styled normally
- **Uncorroborated tags** appear in a separate section below, headed "Needs Corroboration" or similar, visually distinct (lighter, smaller, or different background)

### Tag Creation

Any logged-in user can apply a tag to an entry. If the tag doesn't exist yet, it is created as `uncorroborated`. Once enough users have independently applied the same tag to entries (or upvoted its application), it becomes `corroborated`.

### Tag Categories

Categories are admin-controlled. The initial set:
- `character` — named individuals (Hinekora, Sin, Ahkeli, Doryani, Kaom, etc.)
- `faction` — groups and organizations (Order of the Djinn, Precursors, Vaal, Eternal Empire, Karui, Maraketh, Azmeri, Lightless, Twilight Order, etc.)
- `mechanic` — game mechanics that provide lore (Delve, Heist, Expedition, Breach, Delirium, Ritual, Lake of Kalandra, Sanctum, etc.)
- `act` — game progression (Act 1, Act 2, ..., Endgame)
- `location` — specific in-game areas (Temple of Kopec, Highgate, Utzaal, etc.)
- `lore_topic` — thematic/cosmological topics (Divinity, Corruption, Edicts, Mother Soul, Well of Souls, Unlight, etc.)
- `game_system` — source type filtering (Item Flavour Text, NPC Dialogue, Environmental Lore, Quest Text, Support Gem Flavour, etc.)
- `class` — player class whose dialogue this is (Warrior, Mercenary, Huntress, Witch, Sorceress, Druid, etc.)

Alex reserves the right to add, rename, merge, or restructure categories at any time.

## Spoiler Greylisting

### How It Works

Each user maintains a personal greylist of tags. Any entry that has a greylisted tag appears as a collapsed bar rather than fully rendered.

### Collapsed Bar Display

The collapsed bar shows the tags that triggered the greylist match, so the user can make an informed decision: "This entry is tagged: [Act 5] [Cedrus] [Twilight Order] — Click to reveal"

The user sees *which* tags matched their greylist without seeing the entry content. They can click to reveal if they decide they don't care about that particular spoiler.

### Datamined Content Default

Entries with status `datamined` are auto-greylisted for all users by default. Users can opt in to seeing datamined content via a setting. When datamined content is confirmed in a live patch, its status changes to `current` and the auto-greylist is removed.

## Version Tracking

### Tracking Changes Across Patches

When game text changes between patches, the original entry's status is updated to `replaced` and its `patch_removed` is set. A new entry is created with the current text and `patch_added` set to the new patch version.

Both entries share the same tags (plus any new ones relevant to the change). They are *not* explicitly linked to each other — the shared tags and version metadata let users find them through search.

### Search and Sort

When searching by tags, results include a "Patch Version" column that users can sort by. Current entries appear at the top by default. Users can switch to sorting by patch version to see the full history of text changes for a given tag combination.

### Status Display

Each entry visually indicates its status:
- `current` — no special indicator (default state)
- `replaced` — subtle indicator (e.g., strikethrough styling or a "Replaced in [patch]" badge)
- `removed` — similar indicator (e.g., "Removed in [patch]" badge)
- `datamined` — distinct indicator (e.g., "Datamined — Unconfirmed" badge)

## Search System

### Tag-Based Filtering

Users can construct boolean queries using tags:
- Include: "Show entries tagged with [Hinekora] AND [Karui]"
- Exclude: "But NOT tagged [Act 5]"

The UI should make this accessible without requiring users to type boolean syntax — a tag selector with include/exclude toggles is more user-friendly.

### Full-Text Search

Users can also search within entry text content directly. PostgreSQL's built-in full-text search handles this. Full-text search can be combined with tag filters.

### Sort Options

- **Default:** Current entries first, then by confidence score
- **By patch version:** Useful for tracking changes over time
- **By submission date:** Most recent submissions first
- **By confidence:** Highest confidence first

## Pages (MVP)

1. **Home / Search** — the primary interface. Tag selector with include/exclude, free-text search bar, results list with sort controls.
2. **Entry Detail** — full text of a single entry with all its metadata, tags (both tiers), confidence indicator, context note with its own confidence, and threaded comments.
3. **Submit Entry** — form for adding new dialogue/text. Fields for the text, source, source type, game, current patch version, and an optional context note. User must be logged in.
4. **Tag Browser** — browse all corroborated tags by category, see how many entries each tag has, click to search.
5. **User Profile** — a user's submission history and their aggregate stats (entries submitted, how many reached high confidence, etc.)
6. **Admin Dashboard** — Django's built-in admin panel, customized to show pending uncorroborated tags, recently flagged entries, submission volume, and moderation queue.

## Future Considerations (Not MVP)

These are features discussed and deemed either not yet necessary or deliberately deferred:

- **Formal inter-entry linking** — "This entry replaced that entry" direct links. Deliberately excluded due to verification complexity and visual clutter concerns. May be revisited if the community strongly needs it.
- **Formal trigger modeling** — Machine-readable conditions (quest state, class, etc.) that determine when a line appears. Excluded because GGG's trigger logic is too opaque. Community context notes serve this purpose informally.
- **Admin-curated condition summaries** — Alex manually writing a canonical "this line appears when..." summary on entries with high-confidence context notes. Possible future addition once the community has generated enough data to make this reliable.
- **API access** — Letting other tools (wiki bots, community apps) query the repository programmatically.
- **Bulk import** — Ingesting datamined text dumps from poe2db or similar sources.
- **Image/screenshot attachments** — Letting users attach screenshots as evidence alongside their text submissions.
- **Localization** — Supporting non-English game text.

## Project Name

Not yet decided. Candidates could be anything that resonates thematically with PoE's lore around mirrors, reflections, memory, and preservation — but this is Alex's call.
