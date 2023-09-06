
def compute_average_rating(ratings):
    """Berechnet den durchschnittlichen Wert einer Liste von Bewertungen"""
    if ratings:
        return round(sum(ratings) / len(ratings))
    return None
