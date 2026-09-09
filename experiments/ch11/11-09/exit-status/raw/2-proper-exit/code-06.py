def merge_intervals(intervals):
    if not intervals:
        return []
    # Sort intervals by start time
    sorted_intervals = sorted(intervals)
    result = [sorted_intervals[0][:]]  # Create a copy of the first interval
    for start, end in sorted_intervals[1:]:
        last_start, last_end = result[-1]
        # If current interval overlaps or touches the last merged interval
        if start <= last_end:  # Touching is allowed, so <=
            # Merge by extending the end if needed
            result[-1][1] = max(last_end, end)
        else:
            # No overlap, add as new interval
            result.append([start, end])
    return result
