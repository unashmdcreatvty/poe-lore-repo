def get_confidence(upvotes, downvotes):
    total = upvotes + downvotes
    net = upvotes - downvotes

    if total == 0:
        return 'grey'

    ratio = upvotes / total

    if total >= 5 and abs(net) <= 1:
        return 'purple'
    if total >= 10 and ratio >= 0.85:
        return 'green'
    if total >= 5 and ratio >= 0.70:
        return 'yellow'
    if net > 0:
        return 'orange'
    return 'grey'
