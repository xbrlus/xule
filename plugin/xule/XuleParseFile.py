import datetime
import os
import sys
import threading
from queue import Queue

from .xule_grammar import get_grammar


def _resolve_redirect(full_file_name):
    """Return the real file to parse for *full_file_name*.

    Some .xule files are redirect stubs whose entire content is a relative
    path to a shared library file, e.g.:
        ../../lib/version.xule
    Detect this by checking whether the file's stripped content looks like a
    path (no whitespace, ends with .xule, resolves to an existing file
    relative to the stub's directory).  Returns the resolved absolute path
    when a redirect is found, otherwise returns *full_file_name* unchanged.
    """
    try:
        with open(full_file_name, 'r', encoding='utf-8') as fh:
            content = fh.read().strip()
        # A redirect is a single token (no internal whitespace) that ends in
        # .xule and is not a xule statement (those never start with '.' or '/').
        if '\n' not in content and ' ' not in content and content.lower().endswith('.xule'):
            base_dir = os.path.dirname(full_file_name)
            target = os.path.normpath(os.path.join(base_dir, content))
            if os.path.isfile(target):
                print("Redirect: %s -> %s" % (os.path.basename(full_file_name), target))
                return target
    except Exception:
        pass
    return full_file_name


def parseFile(full_file_name, stack_size, recursion_limit):
    if threading.stack_size() != stack_size:
        threading.stack_size(stack_size)
    if sys.getrecursionlimit() < recursion_limit:
        sys.setrecursionlimit(recursion_limit)

    # Resolve redirect stubs before parsing.
    full_file_name = _resolve_redirect(full_file_name)

    start_time = datetime.datetime.today()
    file_name = os.path.basename(full_file_name)
    print("%s: %s parse start" % (datetime.datetime.isoformat(start_time), file_name))

    parseResQueue = Queue()

    def threaded_parse():
        try:
            xule_grammar = get_grammar()
            parseRes = xule_grammar.parseFile(full_file_name).as_dict()
            parseResQueue.put(parseRes)
        except Exception as e:
            print("PARSE ERROR in file: %s" % full_file_name)
            print("  Error: %s" % e)
            parseResQueue.put(e)   # unblock the main thread

    threading.Thread(target=threaded_parse).start()
    parseRes = parseResQueue.get()
    if isinstance(parseRes, Exception):
        raise parseRes

    end_time = datetime.datetime.today()
    print("%s: %s parse end. Took %s" % (datetime.datetime.isoformat(end_time), file_name, end_time - start_time))
    return parseRes
