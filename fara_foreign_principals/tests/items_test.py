import pytest

from ..items import (
    strip_string, 
    FaraForeignPrincipalItemLoader, 
    FaraForeignPrincipalItem
)


class TestItems:
    def test_string_strip(self):
        initial_string = ' sample string with\u00a0values\xa0\xa0'

        actual_stripped_string = strip_string(initial_string)

        expected_stripped_string = 'sample string with values'
        assert actual_stripped_string == expected_stripped_string


    def test_foreign_principal_item_loader(self):
        mock_data = {
            'url': 'http://sample_url.com',
            'foreign_principal': 'Piccolo San',
            'state': None,
            'registrant': "registrant 1",
            'country': "Planet Namek",
            'reg_num': "123",
            'date': '11/24/1984',
            'exhibit_url': 'http://sample_exhibit_url.com',
            'address': ['address line 1', 'adress\xa0line 2']
        }
        mock_principal_item_loader = FaraForeignPrincipalItemLoader(
            item=FaraForeignPrincipalItem())

        mock_principal_item_loader.add_value(None, mock_data)
        actual_item_value = mock_principal_item_loader.load_item()
        expected_item_value = {
            'address': 'address line 1, adress line 2',
            'country': 'Planet Namek',
            'date': '1984-11-24T00:00:00+00:00',
            'exhibit_url': 'http://sample_exhibit_url.com',
            'foreign_principal': 'Piccolo San',
            'reg_num': '123',
            'registrant': 'registrant 1',
            'state': None,
            'url': 'http://sample_url.com'
        }
        assert actual_item_value == expected_item_value

