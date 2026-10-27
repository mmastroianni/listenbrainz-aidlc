# Accessibility Checklist

Target: basic keyboard use (rough-mockups Q7, requirement FR6.3), with cheap WCAG AA practices applied where they cost little. Covers the screens in `mockups.md` and `ideation/rough-mockups/wireframes.md`, the flow in `ideation/rough-mockups/user-flow.md`, story US2.4 in `inception/user-stories/stories.md`, requirements FR6.1 to FR6.6 in `inception/requirements-analysis/requirements.md`, and is verified by the pre-merge tests described in `inception/practices-discovery/team-practices.md`.

## Keyboard (required)

- [ ] The search box is focused on page load (AC2.4.2).
- [ ] Down and Up move through suggestions, Enter picks, Escape closes (AC2.4.3).
- [ ] Tab reaches every result name, every link and "Show more" in visual order (AC2.4.4).
- [ ] Every focusable element shows the focus ring (`3px solid #93d3e1`).
- [ ] No keyboard trap: Tab always leaves the suggestions list.
- [ ] After "Show more", focus moves to the first new row.

## Screen readers (good practice)

- [ ] The search box has the visible label "Artist" and the combobox/listbox roles.
- [ ] Each similarity bar has text "similarity 0.87" (Q1).
- [ ] Each icon link has a label such as "Anthony Braxton on YouTube".
- [ ] Status messages (no match, not enough data, error) are in a polite live region.
- [ ] Headings: one `h1` (page), one `h2` (results).
- [ ] The page language is declared.

## Visual

- [ ] Text contrast meets 4.5:1 (`--ink` and `--muted` on white both do).
- [ ] The similarity value is never shown by colour alone.
- [ ] Long names wrap and are not cut mid-word (AC2.4.5).
- [ ] The layout works at 375 px wide with no sideways scroll (AC2.4.1) and at 200% zoom.
- [ ] Touch targets for icon links are at least 44 by 44 px on phones.

## Verification

Keyboard items are covered by API and page tests where possible and by a manual keyboard pass before tagging v0.1.0.
