#### Tested on Python 3.6

```
pyvenv env
. env/bin/activate

pip install -r requirements.txt

env/bin/scrapy crawl foreign_principals_spider -o fara_foreign_principals.json
```

#### Run tests
```
pytest fara_foreign_principals
```

##### Tests aren't quite done yet. Need to add spider contracts and tests for scrapy item's.
