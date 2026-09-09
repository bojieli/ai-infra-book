def merge_intervals(intervals):
    if not intervals:
        return []
    intervals.sort()
    result = []
    for start, end in intervals:
        if result and start <= result[-1][1]:
            result[-1][1] = end
        else:
            result.append([start, end])
    return result