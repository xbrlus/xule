import sys
sys.path.append('..')
import argparse
import pprint
import json
import datetime

aparser = argparse.ArgumentParser()
aparser.add_argument("-f")
aparser.add_argument("-s")
aparser.add_argument("-g")
args = aparser.parse_args()

def timeCall(functionInfo, *args, **kwargs):
    functionStartTime = datetime.datetime.today()
    if isinstance(functionInfo, tuple):
        function = functionInfo[0]
        note = functionInfo[1]
    else:
        function = functionInfo
        note = None
    result = function(*args, **kwargs)

    functionEndTime = datetime.datetime.today()
    hours, remainder = divmod((functionEndTime - functionStartTime).total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
        
    print("%s - %s%s" % ('%02.0f:%02.0f:%02.4f' % (hours, minutes, seconds), function.__name__, ' - ' + note if note else ''))
    return result

if args.g is None:
    from xule_grammar3 import get_grammar
    print('grammar 3')
else:
    if args.g == '2':
        from xule_grammar2 import get_grammar
        print('grammar 2')
    elif args.g == '3':
        from xule_grammar3 import get_grammar
        print('grammar 3')
    elif args.g == '4':
        from xule_grammar4 import get_grammar
        print('grammar 4')
    else:
        print("Grammar for -g = " + args.g + " does not exists")
        exit()

xule_parser = timeCall(get_grammar)

if args.f:
    res = xule_parser.parseFile(args.f, parseAll=True)
    print(json.dumps(res.asDict(), indent=4))

elif args.s:
    res = xule_parser.parseString(args.s, parseAll=True)
    print(res.asDict())
#     print(json.dumps(res.asDict(), indent=4))
#     print(res.dump())
#     print(res)
    pprint.pprint(res.asDict())
#     pprint.pprint(res.asList())
#     print(res.pprint())
    #pprint.pprint(res.asDict())
else:
    print("no file or string provided")