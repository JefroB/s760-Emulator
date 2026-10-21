# Limits of firmware screen extraction

The repository's [screen extractor](../../../.agents/scripts/extract_screen_layout.py) searches for candidate descriptor patterns, plausible coordinates/attributes, ASCII labels and softkey strings. Its pattern recognition and fallback ranges are heuristics. Finding nearby text does not establish a complete screen, every field binding or pixel-perfect geometry.

Promote an extracted descriptor only after validating its original bytes, bank context, callers and runtime use. Compare the resulting display against a matched physical photograph or firmware-driven native frame. Distinguish static label recovery, inferred structure and observed rendering in the report.

The previous mathematical wireframes were not a validated screen specification and have been removed. Use the [physical catalog](index.md) and the [firmware documentation](../../firmware/README.md) as starting points for further analysis.
