Scrapes from abse url: `https://efile.fara.gov/pls/apex/f?p=171:130:::NO:RP,130:P130_DATERANGE:N`

A sample output json file is also present in the repository: `sample_fara_foreign_principals.json`

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
