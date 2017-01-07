# OneFilter

One filter for all structured data.


## Getting started

```pycon
>>> from onefilter import F, And, Or, Exists, Eq, Gte, Lte 
>>> from onefilter.es import ES
>>> f = F(a=Or([Exists(False), Eq(0)]), b=And([Gte(10), Lte(20)]))
>>> c = ES(f)
>>> import pprint; pprint.pprint(c)
{'bool': {'must': [{'bool': {'should': [{'must_not': {'exists': {'field': 'a'}}},
                                        {'term': {'a': 0}}]}},
                   {'range': {'b': {'gte': 10, 'lte': 20}}}]}}
```


## License

[MIT][3]


[3]: http://opensource.org/licenses/MIT
