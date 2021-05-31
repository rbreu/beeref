def queue2list(queue):
    qlist = []
    while not queue.empty():
        qlist.append(queue.get())
    return qlist
