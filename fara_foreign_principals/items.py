# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

import arrow

from scrapy.item import Item, Field
from scrapy.loader import ItemLoader
from scrapy.loader.processors import Join, MapCompose, TakeFirst, Compose, Identity


def strip_string(field):
    if field is None:
        return None
    stripped_field = field.replace('\\u00a0', ' ').replace('\xa0', ' ').strip()
    if stripped_field == '':
        return None
    else:
        return stripped_field


class IdentityOrNone(object):
    def __call__(self, values):
        if values:
            return values
        return [None]


class FaraForeignPrincipalItem(Item):
    url = Field()
    foreign_principal = Field()
    address = Field(
        input_processor=Join(separator=', ')
    )
    country = Field()
    state = Field()
    registrant = Field()
    reg_num = Field()
    exhibit_url = Field()
    date = Field(
        input_processor=MapCompose(
            lambda date_string: arrow.get(date_string, 'MM/DD/YYYY').isoformat()),
        output_processor=TakeFirst()
    )


class FaraForeignPrincipalItemLoader(ItemLoader):
    default_input_processor = IdentityOrNone()
    default_output_processor = Compose(TakeFirst(), strip_string)
    default_item_class = FaraForeignPrincipalItem

    def load_item(self):
        item = self.item
        for field_name in tuple(self._values):
            item[field_name] = self.get_output_value(field_name)
        return item
