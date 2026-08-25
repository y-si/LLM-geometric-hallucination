# 3MT Speech — Draft 3

**Target:** ~430 words / 3 minutes at ~150 wpm. Bracketed notes are stage directions.

---

The other day, I asked ChatGPT to describe the Nexus Monument in New Meridian. It told me it was "a breathtaking architectural marvel... a pearlescent sphere symbolizing unity." Except — the monument doesn't exist. The city of New Meridian isn't even real. But ChatGPT had no idea.

[beat]

You've probably experienced something similar — a chatbot getting something wrong with complete confidence. This is called a hallucination. The problem is, these same AI models are being used for things like legal research, self-driving cars, research on joints — fields where the consequences can be grave, and yet AI fabricates with full confidence. So my thesis asks: can we predict hallucinations from our input question alone — before the AI even responds?

[beat]

And the answer is yes — but not in the way you'd expect.

When you feed a question to an AI, it doesn't just read the words. It converts that question into a point on a map of all the data the AI's been trained on. [gesture toward slide] And what we found is that this map has a geometry. Some regions are crowded with similar information, and questions that land here get answered correctly. But other regions are sparse — they're empty neighborhoods where the model has almost nothing to draw from. And that's where the AI makes things up.

This isn't just about hard versus easy questions — even at the same difficulty, emptier neighborhoods are where the model fails. So the shape of the map predicts the mistakes.

So we found where the problem is. Then the next question becomes: can we fix it?

The solution was actually quite simple. We added one instruction to every question: "Check whether something exists before answering, and be honest if you don't know." It's sounds a bit silly, but that alone cut hallucination rates by up to 89%. We then used those corrected answers to permanently retrain the models, so they're careful by default.

And here's what I didn't expect: the same map that told us where the AI would fail also told us which failures we could and could not fix. The questions stuck in the emptiest parts of the map — those are the ones that resist correction. So the geometry doesn't just predict the mistakes. It predicts which ones we can fix.

[slow down]

Every system that learns from data has blind spots. What this thesis shows is that the blind spots aren’t hidden — they’re legible, from the shape of the question itself. And that means we no longer have to trust AI blindly to know if it's true.

Hallucination isn't random. It has a structure — and once you find it, you can fix it.

[pause]

Thank you.


---

**Word count:** ~430
**Estimated time:** 2:52 at 150 wpm (leaves ~8 seconds for pauses)
