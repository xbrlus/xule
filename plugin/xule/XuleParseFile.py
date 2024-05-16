import datetime
import os
import sys
import threading
from queue import Queue

from .xule_grammar import get_grammar


def parseFile(full_file_name, stack_size, recursion_limit):
    if threading.stack_size() != stack_size:
        threading.stack_size(stack_size)
    if sys.getrecursionlimit() < recursion_limit:
        sys.setrecursionlimit(recursion_limit)
    start_time = datetime.datetime.today()
    file_name = os.path.basename(full_file_name)
    print("%s: %s parse start" % (datetime.datetime.isoformat(start_time), file_name))

    parseResQueue = Queue()

    def threaded_parse():
        xule_grammar = get_grammar()
        parseRes = xule_grammar.parseFile(full_file_name).as_dict()
        parseResQueue.put(parseRes)

    threading.Thread(target=threaded_parse).start()
    parseRes = parseResQueue.get()

    end_time = datetime.datetime.today()
    print("%s: %s parse end. Took %s" % (datetime.datetime.isoformat(end_time), file_name, end_time - start_time))
    return parseRes
