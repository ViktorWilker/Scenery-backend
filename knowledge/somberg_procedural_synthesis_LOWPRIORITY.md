# ═══ LOW PRIORITY — PROCEDURAL SYNTHESIS (future use, not applicable today) ═══

This entire file covers real-time procedural audio synthesis — generating sound
from algorithms and oscillators rather than selecting and layering pre-recorded
samples. This is NOT Scenery's current method (Scenery composes scenes from
pre-recorded previews sourced from Freesound). This content is kept for
potential future use if Scenery ever moves toward generative/synthesized audio,
but should be weighted very low (or excluded) in retrieval for the current
sample-based composition agent.

### Knowledge Base Extraction: Procedural Ambience and Soundscape Principles

#### Stochastic Foundations for Environmental Ambience

**Source:** Game Audio Programming 5 (Somberg, ed.)

In the design of procedural soundscapes, stochastic signals serve as the "organic grit" required for non-pitched environmental textures. White noise is the primary building block, defined by possessing equal energy across the frequency spectrum. Design requirements often dictate the use of other noise "colors" — pink, brown, or blue noise — to simulate different energy distributions found in nature. The goal in psychoacoustic terms is not absolute mathematical randomness but "perceptual randomness" — by applying filtering and resonance to stochastic foundations, a synthesis system can mimic natural chaos, allowing a soundscape to feel living and unpredictable rather than mechanical.

**Practical application (hypothetical, future synthesis use):** A future procedural synthesis layer could use filtered/colored noise generators to create wind, rushing water, or rustling leaves entirely algorithmically, without needing pre-recorded source material for these texture types.

---

#### Harmonic Waveform Selection for Materiality

**Source:** Game Audio Programming 5 (Somberg, ed.)

While noise provides texture, harmonic waveforms provide structural identity and "materiality." The selection of fundamental waveforms — sawtooth, square, and triangle — is dictated by their harmonic signatures. Sawtooth waves, containing both even and odd harmonics, create bright, buzzy textures suited to machinery or intense drones. Triangle waves, containing only odd harmonics that diminish quickly, produce a soft, delicate quality. Square waves possess a distinct "hollow" identity due to their odd-only harmonic content, useful for alarms or rhythmic effects via pulse-width modulation. The harmonic profile of a waveform informs whether a synthesized material reads as "hard" (machinery) or "soft" (gentle air and water).

**Practical application (hypothetical, future synthesis use):** A future synthesis engine could select base waveform types according to desired materiality — sawtooth for industrial/mechanical textures, triangle for soft air and water sounds, square with PWM for alarms or chiptune-style tones.

---

#### Perceptual Clarity via Spectral Band-Limiting

**Source:** Game Audio Programming 5 (Somberg, ed.)

A primary risk in real-time synthesis is "aliasing" — audible digital artifacts that occur when high-frequency components exceed the Nyquist limit and fold back into the audible range. Maintaining fidelity in a synthesis system requires smoothing discontinuities to push these artifacts out of the audible range or render them perceptually insignificant. Band-limiting techniques trade off computational cost against quality: lighter methods suit resource-constrained environments like mobile platforms, while heavier methods provide higher quality at greater computational cost.

**Practical application (hypothetical, future synthesis use):** Any future oscillator-based synthesis for sharp waveforms (saw, square) would need band-limiting to avoid audible digital artifacts — a concern entirely specific to synthesis and not applicable to pre-recorded sample playback.

---

# ═══ END OF LOW PRIORITY SECTION — the section below is NOT low priority ═══

#### Audio Density and Reductionist Mixing Logic

**Source:** Game Audio Programming 5 (Somberg, ed.), Chapter on audio optimization

Optimizing a dense interactive soundscape requires a mindset of reduction rather than addition — in a dense mix, more concurrent signals collapse into indistinguishable noise rather than adding richness. A listener can only perceptually track a small number of distinct sound layers before a mix becomes cluttered. Actively culling and subtracting irrelevant ambient layers preserves a legible soundscape, ensuring the most important sounds in a scene remain audible and prioritized.

**Practical application:** This principle is not specific to synthesis — it applies equally to sample-based composition. In high-density scenes, prioritize a small number of clearly audible layers over a large number of quiet, competing ones; treat "subtracting a layer" as a valid and often superior choice to "adding more layers."
