# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import argparse
import json
import sys

from elasticsearch import Elasticsearch

import onefilter as of
from onefilter.es import ES


def utf8_print(unicode_str):
    print(unicode_str.encode('utf-8'))


def make_onefilter_namespace():
    op_names = ('F', 'And', 'Or', 'Eq', 'In', 'Gte', 'Lte', 'Exists')
    return {op_name: getattr(of, op_name) for op_name in op_names}


def make_query_body(dsl):
    if not dsl:
        return {'query': {'match_all': {}}}
    try:
        body = eval(dsl, make_onefilter_namespace())
    except Exception:
        utf8_print('Unrecognized filter `{}`'.format(dsl))
        sys.exit(1)
    else:
        return {'query': ES(body)}


def to_curl(args):
    query = make_query_body(args.filter)
    curl_cmd = (
        "curl http://{host}:{port}/{index}{doc_type}/_search{pretty} "
        "-d '{query}'".format(
            host=args.host,
            port=args.port,
            index=args.index,
            doc_type='/%s' % args.doc_type if args.doc_type else '',
            pretty='?pretty' if args.pretty else '',
            query=json.dumps(query, ensure_ascii=False)
        )
    )
    utf8_print(curl_cmd)
    

def filter(args):
    es_client = Elasticsearch(['%s:%s' % (args.host, args.port)])
    try:
        query = make_query_body(args.filter)
        result = es_client.search(args.index, args.doc_type, query)
    except Exception as exc:
        utf8_print(unicode(exc))
    else:
        # Indent and sort keys by name, if the user asks for pretty
        kwargs = dict(sort_keys=True, indent=2) if args.pretty else {}
        # Always avoid unicode escapes to improve readability
        output = json.dumps(result, ensure_ascii=False, **kwargs)
        utf8_print(output)


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--host', '-h', default='localhost')
    parser.add_argument('--port', '-p', type=int, default=9200)
    parser.add_argument('--index', '-i', required=True)
    parser.add_argument('--doc-type', '-d')
    parser.add_argument('--filter', '-f',
                        type=lambda s: unicode(s, sys.stdin.encoding))
    parser.add_argument('--pretty', action='store_true')
    parser.add_argument('--to-curl', action='store_true')
    parser.add_argument('--help', action='help',
                        help='show this help message and exit')
    args = parser.parse_args()

    if args.to_curl:
        to_curl(args)
    else:
        filter(args)


if __name__ == '__main__':
    main()
