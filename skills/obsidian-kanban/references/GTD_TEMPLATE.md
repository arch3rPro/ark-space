# GTD Board Template

## Purpose

Use this template when the user asks for a fresh GTD-oriented Kanban board.
It is optimized for mixed card complexity: simple tasks can remain lightweight cards, while larger outcomes can grow into linked notes.
It also aims to stay close to GTD rather than collapsing into a generic priority board.

## Default list design

- `Inbox`: fast capture before triage
- `Next Actions`: concrete work that can be done now
- `Waiting For`: blocked work waiting on others or external events
- `Calendar`: hard-date work or date-triggered reminders only
- `Projects`: multi-step outcomes that need decomposition and ongoing support material
- `Someday/Maybe`: intentionally deferred work
- `Done`: recently completed work kept briefly before archival
- `Archive`: long-term historical storage

## Starter board

~~~~markdown
---
kanban-plugin: board
---

## Inbox

- [ ] Capture new tasks here before clarifying them

## Next Actions

- [ ] Example actionable task @{2026-05-02} @@{09:00} #computer #work

- [ ] Call vendor about contract update #phone #work

## Waiting For

- [ ] Await revised contract from vendor #follow-up #work

## Calendar

- [ ] Submit tax declaration @{2026-05-05} @@{17:00} #deadline #finance

## Projects

- [ ] [[Example Project]] @{2026-05-10} @@{10:00} #project #work
  - [ ] Review project note
  - [ ] Ensure at least one next action exists

## Someday/Maybe

- [ ] Example deferred idea #idea

## Done

***

## Archive

%% kanban:settings
```
{
  "kanban-plugin": "board",
  "metadata-keys": [
    {
      "metadataKey": "priority",
      "label": "",
      "shouldHideLabel": true,
      "containsMarkdown": true
    }
  ]
}
```
%%
~~~~

## Triage rules

Apply these defaults when reorganizing incoming tasks:

1. Put unclear work into `Inbox`
2. Move clear, immediately doable work into `Next Actions`
3. Move blocked work into `Waiting For`
4. Move hard-date work into `Calendar`
5. Move larger outcomes into `Projects`
6. Move intentionally postponed ideas into `Someday/Maybe`
7. Move finished work into `Done`
8. Move stale completed items into `Archive`

## GTD rules

- `Calendar` is not a priority lane. Only place work there if it must happen on a date, or if the user should only see it on a date.
- Each item in `Projects` should have at least one concrete next action in `Next Actions`.
- `Waiting For` should only hold work blocked by someone else, an approval, or an external event.
- `Done` is a short-lived review lane, not a permanent trophy wall.
- Use tags to express context such as `#computer`, `#phone`, `#home`, `#office`, or `#errands`.
- Use inline Kanban date and time tokens like `@{2026-05-05}` and `@@{17:00}` instead of `due:` style list items.

## Mixed-model guidance

Use a lightweight card when:

- the task is short
- the details fit comfortably on the card
- no ongoing notes are needed

Use a linked-note card when:

- the task is effectively a project
- the task needs notes, references, or attachments
- the task will be revisited across multiple work sessions

Default expectation for GTD boards:

- lightweight cards fit `Inbox`, many `Next Actions`, and many `Waiting For` items
- linked-note cards fit most `Projects`

Recommended project-note topics:

- goal
- context
- desired outcome
- next visible actions
- decision log
- related links
- next milestones

## Optional priority convention

Priority is optional.
If the user already uses priority, keep it out of the title and display it through linked-note metadata instead of card-body text.

Recommended board setup:

```json
{
  "metadata-keys": [
    {
      "metadataKey": "priority",
      "label": "",
      "shouldHideLabel": true,
      "containsMarkdown": true
    }
  ]
}
```

Recommended linked-note frontmatter values:

- `priority: |` then `<span style="color:#dc2626;"><strong>Q1 重要且紧急</strong></span>`
- `priority: |` then `<span style="color:#ea580c;"><strong>Q2 重要不紧急</strong></span>`
- `priority: |` then `<span style="color:#2563eb;"><strong>Q3 紧急不重要</strong></span>`
- `priority: |` then `<span style="color:#6b7280;"><strong>Q4 不重要不紧急</strong></span>`

Do not require every card to have a priority.
If a task must stay lightweight, prefer leaving it without explicit priority rather than pushing styled priority text into the title or card body.
