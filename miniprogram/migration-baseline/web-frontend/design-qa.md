# Design QA

## Source visual truth

- Homepage annotation: `C:\Users\37227\AppData\Local\Temp\codex-clipboard-581c050c-fbba-4766-84cd-f9a0a64a1345.png`
- Editor reference: `C:\Users\37227\AppData\Local\Temp\codex-clipboard-eaa69f3b-c127-4e47-9089-86f7cd34b864.png`
- Pattern chart reference: `D:\vscodePro\pindou\PRD1.0_media\image2.png`
- Mirrored pattern chart reference: `D:\vscodePro\pindou\PRD1.0_media\image3.png`
- Making-assistant reference: `D:\vscodePro\pindou\PRD1.0_media\image4.jpg`

## Implementation under test

- Routes: `/`, `/editor/demo`, `/make/girl`
- Core implementation: `src/pages/HomePage.tsx`, `src/pages/EditorPage.tsx`, `src/pages/MakePage.tsx`, `src/components/CoordinateBoard.tsx`, `src/components/BeadGrid.tsx`, `src/advanced.css`
- Desktop captures:
  - `C:\Users\37227\.codex\visualizations\2026\07\19\019f78ad-05b4-7191-9773-0214089eb7a8\home-revised-2048.png`
  - `C:\Users\37227\.codex\visualizations\2026\07\19\019f78ad-05b4-7191-9773-0214089eb7a8\editor-revised-v2-2048.png`
  - `C:\Users\37227\.codex\visualizations\2026\07\19\019f78ad-05b4-7191-9773-0214089eb7a8\editor-mirror-revised-v2-2048.png`
  - `C:\Users\37227\.codex\visualizations\2026\07\19\019f78ad-05b4-7191-9773-0214089eb7a8\make-revised-v2-1672.png`
- Mobile captures:
  - `C:\Users\37227\.codex\visualizations\2026\07\19\019f78ad-05b4-7191-9773-0214089eb7a8\editor-revised-390.png`
  - `C:\Users\37227\.codex\visualizations\2026\07\19\019f78ad-05b4-7191-9773-0214089eb7a8\make-revised-390.png`

## Viewports and states

- Desktop homepage/editor: 2048 × 1128.
- Desktop making view: 1672 × 1012.
- Mobile editor/making view: 390 × 844.
- Exercised states: selected cell, selection tab, normal/mirrored editor, A18 color highlight, making-assistant guide, export tab.

## Comparison evidence

- Homepage full-view comparison: `C:\Users\37227\.codex\visualizations\2026\07\19\019f78ad-05b4-7191-9773-0214089eb7a8\qa-home-comparison.jpg`
- Editor full-view comparison: `C:\Users\37227\.codex\visualizations\2026\07\19\019f78ad-05b4-7191-9773-0214089eb7a8\qa-editor-comparison.jpg`
- Making-board focused comparison: `C:\Users\37227\.codex\visualizations\2026\07\19\019f78ad-05b4-7191-9773-0214089eb7a8\qa-make-board-comparison.jpg`

## QA history

1. First comparison found that the making palette did not correspond to the girl motif, so selecting A18 could not highlight the intended cells.
2. The girl motif was remapped to the current Artkal A06/A18/A33/A42 palette and recaptured. A18 highlighting, remaining/total counts, coordinate axes, board partitions, and the continuous-run guide now agree visibly.
3. Final mirror review found that the grid transform also reversed the color-code glyphs. A counter-transform was added to `.bead-code` so the pattern mirrors while labels remain readable.

## Findings

- P0: none.
- P1: none.
- P2: none.
- P3 accepted constraint: the implementation keeps the product's existing 24 × 24 mock grid and current Artkal palette instead of copying the reference chart's exact dimensions and artwork. The reference is used for the editing/viewing presentation model, not as replacement product data.
- Browser console severe errors: 0.
- Mobile horizontal overflow: 0 (`innerWidth`, `scrollWidth`, and body width all 390 px).
- Production build: passed.

## Final result

passed
