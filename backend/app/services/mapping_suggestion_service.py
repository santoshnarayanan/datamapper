import difflib


def normalize(text: str):
    return text.lower().replace("_", "").replace(" ", "")


def suggest_mappings(source_columns, target_columns):
    suggestions = []

    for src in source_columns:
        best_match = None
        best_score = 0

        for tgt in target_columns:
            score = difflib.SequenceMatcher(
                None,
                normalize(src),
                normalize(tgt)
            ).ratio()

            if score > best_score:
                best_score = score
                best_match = tgt

        # Threshold to avoid bad matches
        if best_score > 0.5:
            suggestions.append({
                "source": src,
                "target": best_match,
                "confidence": round(best_score, 2)
            })

    return suggestions