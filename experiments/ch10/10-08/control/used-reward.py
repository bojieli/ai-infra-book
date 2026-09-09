def compute_score(data_source,solution_str,ground_truth,extra_info=None,**kwargs):
    return float(solution_str.strip()==str(ground_truth))


def compute_control_score(data_source,solution_str,ground_truth,extra_info=None,**kwargs):
    """Preregistered plumbing control, unrelated to arithmetic correctness.

    Fixed per-prompt signs, never selected from generated output or scores.
    Official REINFORCE++ computes and normalizes the advantages itself.
    """
    signs={'2':1.0,'15':-1.0,'7':1.0,'12':-1.0}
    if str(ground_truth) not in signs:
        raise ValueError('Unknown control prompt ground truth')
    return signs[str(ground_truth)] if solution_str.strip() else 0.0
