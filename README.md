# OneFilter

One filter for all structured data.


## Getting started

```pycon
>>> from onefilter import F, And, Or, Eq, In, Gte, Lte, Exists
>>> from onefilter.es import ES
>>> f = F(a=1, b=In(2, 3, 4), c=And(Gte(5), Lte(9)), d=Or(Exists(False), Eq(0)))
>>> c = ES(f)
>>> import pprint; pprint.pprint(c)
{'bool': {'must': [{'term': {'a': 1}},
                   {'range': {'c': {'gte': 5, 'lte': 9}}},
                   {'terms': {'b': [2, 3, 4]}},
                   {'bool': {'should': [{'must_not': {'exists': {'field': 'd'}}},
                                        {'term': {'d': 0}}]}}]}}
```


## License

[MIT][3]


[3]: http://opensource.org/licenses/MIT
