# 3MT Presentation Outline (v2)

**Format:** 3 minutes, one static slide, non-specialist audience.

**Lessons from past winners:** Personal/narrative hook, one clear thesis question, findings framed as surprising, end on broader implications, zero unexplained jargon.

---

## Structure

### 1. Hook — Make It Personal (0:00–0:30)
- Open with something the audience has *experienced*, not a research example
  - e.g., "Last year I asked ChatGPT about a historical figure for a paper. It gave me a detailed biography — birth date, major works, career arc. Every word of it was wrong. The person existed, but nothing it said was true. And here's the thing: it sounded *exactly* like its correct answers."
  - Or: "If you've ever used ChatGPT, you've probably trusted something it told you. But how would you know if it was lying? It sounds just as confident either way."
- The point: AI fabrication looks identical to AI truth. That's the problem.

### 2. The Question — One Sentence (0:30–0:50)
- "My thesis asks: can we tell, just from the *question* alone — before the AI even starts answering — whether it's going to get it wrong?"
- Brief context: this matters because these models are being used for medical advice, legal research, education — and they fabricate with total confidence.

### 3. The Surprising Answer (0:50–1:30)
- "And the answer is yes — but not in the way you'd expect."
- Don't say "embedding space." Say: "When you feed a question to an AI, it gets converted into a point on a kind of map — a map of everything the model has been trained on."
- The finding: "Questions that land in *crowded* parts of the map — near lots of similar knowledge — get answered correctly. Questions that land in *empty* parts of the map, where the model has little to draw on, that's where it makes things up."
- The surprise: "And this isn't just about asking hard questions versus easy ones. Even among questions of the *same type and difficulty*, the ones in emptier neighborhoods are the ones the model gets wrong."

### 4. What We Did About It (1:30–2:15)
- "So we knew where the problem was. Could we fix it?"
- Step 1: "A single sentence of instruction — just telling the model to check whether something exists before answering — eliminated most of the fabrications."
- Step 2: "We took the model's best corrected answers and used them to permanently retrain it. Now the model is careful by default — no special instructions needed."
- The kicker (frame as surprising): "And the same map that told us *where* the model would fail also told us *which failures would resist correction.* Some fabrications are easy to fix. Others are stuck. And we could tell which was which before we even tried."

### 5. Why This Matters Beyond AI (2:15–2:45)
- Don't end on the technical contribution. End on what it means.
- "Any system that learns from data has regions where its knowledge is thin. Self-driving cars, medical diagnostics, financial models — they all have blind spots. Knowing *where* those blind spots are, before the system acts, is how we know when to trust it and when not to."
- "My thesis shows that for language models, those blind spots are readable from the geometry of the input. And once you find them, you can do something about it."

### 6. Closing Line (2:45–3:00)
- Accessible version: "We can read from the shape of a question whether an AI will get it wrong — and use that signal to make it right."
- Pause. "Thank you."

---

## Slide Design (one static slide)

### Constraints
- One static slide, viewed from a distance, for ~3 minutes
- Audience is non-specialist — the slide should *reinforce* the talk, not carry information the talk doesn't
- Winners' slides are typically very sparse: a title, one visual, maybe 2-3 words of labeling
- The audience should glance at it and get the gist; they should NOT need to read axis labels

### What goes on it
- **Title**: "The Geometry of Language Model Hallucination"
- **Name / concentration / advisor**: bottom or corner, small
- **One visual element** (see options below)

### Option A: Simplified 3-panel (based on intro_overview.png)
The existing `intro_overview.png` has the right *structure* — it tells the full story arc (geometry predicts → interventions reduce → behavior transfers). But it's designed for a thesis reader, not a 3MT audience:
- Axis labels like "Embedding Density (log scale)" are jargon
- p-value annotations mean nothing to non-specialists
- Three separate chart types require three separate mental models

**If using this:** redesign with lay-friendly labels. Panel (a) relabel as "Questions in emptier neighborhoods → more fabrication." Panel (b) relabel as "A one-sentence instruction cuts fabrication by 85%." Panel (c) relabel as "The fix becomes permanent." Strip p-values, strip axis labels, use color and bar height only.

**Verdict:** Decent but busy. Three panels is a lot for one static slide at distance.

### Option B: Single UMAP "map" figure (v3_category_manifolds_umap.png) ⭐ RECOMMENDED
This directly supports the central metaphor of the talk ("a kind of map"). Four panels showing:
- **Factual (2% hallucinated)**: dense blue cluster, almost no red
- **Nonexistent (86% hallucinated)**: overwhelmingly red
- The visual is immediately intuitive: blue dots = correct, red X's = wrong, and you can *see* the clustering

**Why this works for 3MT:**
- It IS the "map" the talk describes — the audience sees what you're talking about
- No axis labels needed (you never say "UMAP" — you say "map")
- The red-vs-blue pattern is readable from 20 feet away
- It creates a moment: "This is what the inside of an AI looks like" (even though that's a simplification)

**If using this:** crop to just the Factual and Nonexistent panels (drop Impossible and Ambiguous — too much detail). Add large plain-English labels: "Questions it knows → gets right" / "Questions it doesn't know → makes things up." Remove axis tick marks entirely.

**Verdict:** Strongest single visual. Maps directly to the talk's metaphor. Tells one story clearly.

### Option C: Two-panel custom (UMAP + bar chart)
- Left: simplified UMAP (Option B, cropped to 2 panels)
- Right: the dramatic bar drop from `ch7_hallucination_comparison.png` (11.8% → 1.3%), stripped to just the bars with labels "Before" and "After"

**Why this works:** Covers both claims — geometry predicts, and we fixed it. The bar chart is universally readable.

**Risk:** Two panels with different visual languages. The audience has to process two things. May be too much for a glance.

**Verdict:** Good if you want to emphasize the intervention story. Slightly busy.

### Option D: Conceptual infographic (custom, not from thesis)
A hand-designed schematic:
- A stylized "map" with a dense region (labeled "knows this") and a sparse region (labeled "doesn't know this")
- An arrow or annotation showing "hallucination happens here"
- Maybe a second panel showing the fix

**Why this works:** Maximum accessibility. No real data to misread. Clean, professional, memorable.

**Risk:** Looks like a TED talk, not a research presentation. Some judges may want to see actual data. Takes design effort.

**Verdict:** High ceiling if executed well. Higher risk if not.

### Option E: "The Knowledge Landscape" (conceptual diagram) ⭐ RECOMMENDED

A stylized topographic or terrain-like visualization that shows the AI's knowledge as a landscape. Dense regions = reliable. Sparse regions = hallucination-prone. This is the thesis contribution made visual — the audience sees the "map" you're describing.

#### Detailed visual spec

**Overall composition:** A single landscape occupying the center ~70% of the slide. Horizontal orientation. No panels, no charts, no axes. Think stylized terrain viewed from above, like a topographic map or a heat map rendered as elevation.

**The landscape itself:**
- **Left/center region — "dense neighborhood":** A cluster of many overlapping dots or a warm-colored elevated terrain. The dots/peaks are packed close together. Color: rich blues and teals, or warm golds — something that reads as "full, alive, known." If using dots, they should be semi-transparent and overlapping, creating a sense of depth and density.
- **Right/edge region — "sparse neighborhood":** Scattered, isolated dots or a flat, empty terrain. Wide gaps between points. Color: muted, cool, desaturated — grays, pale blues, or a faded wash. It should feel empty, thin, uncertain.
- **Transition:** The landscape should grade smoothly from dense to sparse, not be a hard split. This communicates that it's a continuum, not a binary.

**The dots (questions):**
- Scattered across the landscape are ~15-25 dots representing individual questions.
- In the dense region: dots are colored green or blue, with small checkmarks or a glow. These are the correctly-answered questions.
- In the sparse region: dots are colored red or orange, with small X marks. These are the hallucinated answers.
- In the transition zone: a mix — some blue, some red — showing that it's probabilistic, not deterministic.
- The dots should be large enough to see from across the room, but not so large they obscure the landscape.

**Labels (minimal, large font):**
- Over the dense region: **"Reliable"** or **"The AI knows this well"** — in a clean sans-serif, large enough to read from the back row.
- Over the sparse region: **"Blind spot"** or **"The AI is guessing"** — same font, same size.
- No other text on the figure itself. No axis labels, no legend box, no numbers.

**What NOT to include:**
- No axes or coordinate systems — this is a metaphor, not a plot
- No legends or color bars
- No arrows or flow diagrams
- No numbers, percentages, or p-values
- No jargon (no "embedding," "density," "UMAP")

#### Why this works
1. **It IS the thesis.** The landscape is the geometry. Dense = knowledge-rich = reliable. Sparse = knowledge-poor = hallucination. That's the core finding of Chapter 5, rendered as intuition.
2. **It matches the spoken words exactly.** When you say "crowded parts of the map" at 0:55, the audience sees the crowded part. When you say "empty parts of the map," they see the empty part. The slide and the talk are synchronized.
3. **It preempts the naive objection.** The gradient from dense to sparse, with mixed dots in the transition, shows this isn't "easy vs hard" — it's structural. The geometry has texture.
4. **It's visually distinctive.** None of the past winners used anything like this. A terrain/landscape visual stands out from bar charts and Venn diagrams.
5. **It works at distance.** The dense-vs-sparse contrast is visible from the back of the room. The red/blue dots are readable. The two labels are large. Nothing requires squinting.
6. **It ages well across the talk.** At 0:30, it's just a mysterious map. At 1:00, the audience understands what the regions mean. At 2:00, when you say "the same map told us which failures would resist correction," the landscape takes on new meaning. A single image that deepens over 3 minutes.

#### How to build it
- **Best option:** Figma or Illustrator. Start with a Gaussian blob or noise field as the base terrain. Overlay dots manually. Add labels. Export at high resolution.
- **Acceptable option:** Python (matplotlib or plotly) with a KDE or contour plot of actual embedding data, heavily stylized — strip all axes, smooth the contours, overlay colored dots, add text annotations. This has the advantage of being grounded in real data even though it looks conceptual.
- **Fallback:** TikZ in LaTeX. Can produce clean results but harder to get the organic, terrain-like feel.

#### Pairing with the talk
| Talk moment | What audience sees on slide |
|---|---|
| 0:00–0:30 (Hook) | Glances at slide, sees a landscape with colored dots. Doesn't understand yet. |
| 0:50 ("converted into a point on a kind of map") | Looks at slide — oh, THIS is the map. |
| 1:00 ("crowded parts... get answered correctly") | Eyes go to the dense region. Blue/green dots. |
| 1:10 ("empty parts... makes things up") | Eyes go to the sparse region. Red dots. |
| 1:30–2:15 (interventions) | Slide stays up. The landscape is now internalized. Voice carries the new information. |
| 2:30 ("blind spots") | Eyes return to the sparse region. The word "blind spot" on the slide clicks. |

### Recommendation
**Go with Option E** (The Knowledge Landscape). It's the only option that visualizes the thesis contribution itself — not just the problem, not just the results, but the core insight that knowledge has a *shape* and that shape predicts failure. It gives the audience a mental model they'll remember after the talk.

**Fallback:** Option B (UMAP scatter plot) if design time is limited. It's real data that tells a similar story, just less polished.

**Do NOT use:** the geometry heatmaps (5-panel, too technical), the ft_bridge scatter (beautiful but requires understanding axes), or any table.

---

## Key Principles (from winners)
1. **Story first, research second.** The audience needs to care before they need to understand.
2. **One thesis question, stated as a question.** "My thesis asks: ..."
3. **Frame findings as surprising.** "And the answer is yes — but not in the way you'd expect."
4. **Zero jargon.** No "embedding density," no "Bonferroni correction," no "AUC." Use "map," "neighborhood," "crowded vs empty."
5. **End on the world, not the thesis.** Winners end on democracy, environmental protection, education — not on their specific results.
6. **Carry one example through.** Don't introduce multiple scenarios. One question, one fabrication, one fix.
7. **Confidence, not hedging.** In 3 minutes, every "this is preliminary" or "further work is needed" is wasted time. State what you found.
