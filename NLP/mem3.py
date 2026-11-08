def calculate_reproducibility_score(basic_feats, signals):
    score = 50  # Base starting score out of 100
    breakdown = []

    # Rule 1: Hyperparameters Specified (+20 pts)
    if signals["has_hyperparameters"]:
        score += 20
        breakdown.append(" +20: Explicit hyperparameters detected.")
    else:
        breakdown.append(" -10: Few or no explicit hyperparameters found.")

    # Rule 2: Tables Present (+15 pts)
    if basic_feats["tables_count"] > 0:
        score += 15
        breakdown.append(f" +15: Found {basic_feats['tables_count']} tables (provides explicit evaluation targets).")

    # Rule 3: Compute Hardware Specified (+10 pts)
    if signals["has_compute_specs"]:
        score += 10
        breakdown.append(" +10: Compute resources/hardware specified.")

    # Rule 4: Equation Density Penalty/Bonus
    eq_density = basic_feats["eq_per_page"]
    if eq_density <= 2.5:
        score += 10
        breakdown.append(" +10: Balanced mathematical equation density.")
    elif eq_density > 5.0:
        score -= 10
        breakdown.append(" -10: High equation density (may increase implementation complexity).")

    # Rule 5: Code/Repository Link Available (+10 pts)
    if signals["has_code_link"]:
        score += 10
        breakdown.append(" +10: Open-source repository link detected.")

    # Bound score between 0 and 100
    final_score = max(0, min(100, score))
    return final_score, breakdown