# GTD Board Template

## Purpose

Use this template when the user asks for a fresh GTD-oriented Kanban board.
It is optimized for mixed card complexity: simple tasks can remain lightweight cards, while larger outcomes can grow into linked notes.

## Default list design

- `Inbox`: fast capture before triage
- `Next Actions`: concrete work that can be done now
- `Waiting`: blocked work waiting on others or external events
- `Scheduled`: date-driven work
- `Projects`: multi-step outcomes that need decomposition
- `Someday`: intentionally deferred work
- `Done`: recently completed work
- `Archive`: long-term historical storage

## Starter board

~~~~markdown
## Inbox

- [ ] Capture new tasks here before clarifying them

## Next Actions

- [ ] Example actionable task
  - priority: P2
  - due: 2026-05-02
  - tags: #example

## Waiting

- [ ] Example blocked task
  - priority: P2
  - tags: #follow-up

## Scheduled

- [ ] Example scheduled task
  - priority: P1
  - due: 2026-05-05
  - tags: #deadline

## Projects

- [ ] [[Example Project]]
  - priority: P1
  - due: 2026-05-10
  - tags: #project
  - [ ] Define scope
  - [ ] Break into next actions

## Someday

- [ ] Example deferred idea
  - priority: P3
  - tags: #idea

## Done

## Archive

%% kanban:settings
```json
{
  "kanban-plugin": "board"
}
```
%%
~~~~

## Triage rules

Apply these defaults when reorganizing incoming tasks:

1. Put unclear work into `Inbox`
2. Move clear, immediately doable work into `Next Actions`
3. Move blocked work into `Waiting`
4. Move date-sensitive work into `Scheduled`
5. Move larger outcomes into `Projects`
6. Move intentionally postponed ideas into `Someday`
7. Move finished work into `Done`
8. Move stale completed items into `Archive`

## Mixed-model guidance

Use a lightweight card when:

- the task is short
- the details fit comfortably on the card
- no ongoing notes are needed

Use a linked-note card when:

- the task is effectively a project
- the task needs notes, references, or attachments
- the task will be revisited across multiple work sessions

Recommended project-note topics:

- goal
- context
- decision log
- related links
- next milestones

## Priority convention

- `P1`: urgent or high leverage
- `P2`: normal priority
- `P3`: low priority or optional
