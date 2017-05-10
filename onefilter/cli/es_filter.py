# -*- coding: utf8 -*-

from __future__ import absolute_import, unicode_literals

import argparse
import json

from elasticsearch import Elasticsearch

import onefilter as of
from onefilter.es import ES


def make_onefilter_namespace():
    op_names = ('F', 'And', 'Or', 'Eq', 'In', 'Gte', 'Lte', 'Exists')
    return {op_name: getattr(of, op_name) for op_name in op_names}


def make_query_body(dsl):
    body = eval(dsl, make_onefilter_namespace())
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
            query=json.dumps(query, sort_keys=True, ensure_ascii=False)
        )
    )
    print(curl_cmd)
    

def filter(args):
    es_client = Elasticsearch(['%s:%s' % (args.host, args.port)])
    body = eval(args.filter, make_onefilter_namespace())
    try:
        query = make_query_body(args.filter)
        result = es_client.search(args.index, args.doc_type, query)
    except Exception as exc:
        print(str(exc))
    else:
        if args.pretty:
            output = json.dumps(result, sort_keys=True,
                                ensure_ascii=False, indent=2)
        else:
            output = result
        print(output)


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--host', '-h', default='localhost')
    parser.add_argument('--port', '-p', type=int, default=9200)
    parser.add_argument('--index', '-i', required=True)
    parser.add_argument('--doc-type', '-d')
    parser.add_argument('--filter', '-f')
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
