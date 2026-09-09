def merge_intervals(intervals):
    if not intervals:
        return []
    intervals.sort()
    result = [intervals[0]]
    for start, end in intervals[1:]:
        last_start, last_end = result[-1]
        if start <= last_end:
            result[-1][1] = max(last_end, end)
        else:
            result.append([start, end])
    return result