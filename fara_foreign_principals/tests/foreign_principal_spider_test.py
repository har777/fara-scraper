import pytest
import scrapy
import os

from scrapy.http import HtmlResponse, Request

from ..spiders.foreign_principals_spider import ForeignPrincipalsSpider
from ..fara_exceptions import (
    ApexFieldMissingError,
    ApexFieldMultipleValuesError,
    SelectorEmptyError
)


class TestFaraExceptions:
    sample_empty_selector = scrapy.selector.Selector(text="<body></body>").xpath(
        '//div[@id="sample"]')
    sample_multiple_result_selector = scrapy.selector.Selector(
        text="<ul><li>1</li><li>2</li><li>3</li></ul>").xpath(
            '//li/text()')

    def test_parse_apex_xpath_element_for_none_selector(self):
        with pytest.raises(ApexFieldMissingError):
            ForeignPrincipalsSpider.parse_apex_xpath_element(
                None, 'apex_field_1')

    def test_parse_apex_xpath_element_for_empty_selector(self):
        with pytest.raises(ApexFieldMissingError):
            ForeignPrincipalsSpider.parse_apex_xpath_element(
                self.sample_empty_selector, 'apex_field_1')

    def test_parse_apex_xpath_element_for_multiple_value_selector(self):
        with pytest.raises(ApexFieldMultipleValuesError):
            ForeignPrincipalsSpider.parse_apex_xpath_element(
                self.sample_multiple_result_selector, 'apex_field_1')

    def test_check_if_selector_empty(self):
        with pytest.raises(SelectorEmptyError):
            ForeignPrincipalsSpider.check_if_selector_empty(
                self.sample_empty_selector, 'apex_field_1')


class TestForeignPrincipalsSpider:
    def test_setting_apex_metadata(self):
        """Testing apex_metadata assignment.
        """
        mock_response = mock_response_from_file(
            'sample_main_page.html', 'https://efile.fara.gov/pls/apex/')

        foreign_principal_spider = ForeignPrincipalsSpider()
        foreign_principal_spider.set_metadata_from_initial_page_table(mock_response)

        actual_apex_metadata = foreign_principal_spider.apex_metadata
        expected_apex_metadata = {
            'p_flow_id': '171', 'p_flow_step_id': '130', 
            'p_instance': '15405200750185', 'x01': '80340213897823017', 
            'x02': '80341508791823021'
        }
        assert actual_apex_metadata == expected_apex_metadata

    def test_data_extracted(self):
        """Testing data exrtaction from main page.
        """
        mock_main_page_response = mock_response_from_file(
            'sample_main_page.html', 'https://efile.fara.gov/pls/apex/')

        foreign_principal_spider = ForeignPrincipalsSpider()
        main_page_results_generator = foreign_principal_spider.extract_data_from_main_page(mock_main_page_response)
        main_page_first_result = next(main_page_results_generator)

        actual_meta = main_page_first_result.meta
        expected_meta = {'foreign_principal_row_data': {'url': 'https://efile.fara.gov/pls/apex/f?p=171:200:::NO:RP,200:P200_REG_NUMBER,P200_DOC_TYPE,P200_COUNTRY:6065,Exhibit%20AB,AFGHANISTAN', 'foreign_principal': 'Transformation and Continuity', 'address': ['8105 Ainsworth Avenue', 'Springfield\xa0\xa022152'], 'state': 'VA', 'registrant': 'Roberti + White, LLC', 'reg_num': '6065', 'date': '07/03/2014', 'country': 'AFGHANISTAN'}}
        assert actual_meta == expected_meta

    def test_get_exhibit_url_when_multiple_present(self):
        mock_exhibit_url_row_data_list = [
            {'exhibit_date': '01/15/2017', 'exhibit_foreign_principal': 'Embassy of the Republic of Azerbaijan ', 'exhibit_url': 'http://www.fara.gov/docs/5926-Exhibit-AB-20170315-97.pdf'}, {'exhibit_date': '02/23/2017', 'exhibit_foreign_principal': 'Embassy of the Republic of Azerbaijan ', 'exhibit_url': 'http://www.fara.gov/docs/5926-Exhibit-AB-20170223-94.pdf'}, {'exhibit_date': '01/20/2017', 'exhibit_foreign_principal': 'Embassy of the Republic of Azerbaijan ', 'exhibit_url': 'http://www.fara.gov/docs/5926-Exhibit-AB-20170120-92.pdf'}, {'exhibit_date': '09/28/2016', 'exhibit_foreign_principal': 'Embassy of the Republic of Azerbaijan ', 'exhibit_url': 'http://www.fara.gov/docs/5926-Exhibit-AB-20160928-87.pdf'}, {'exhibit_date': '09/09/2016', 'exhibit_foreign_principal': 'Embassy of the Republic of Azerbaijan ', 'exhibit_url': 'http://www.fara.gov/docs/5926-Exhibit-AB-20160909-86.pdf'}, {'exhibit_date': '07/06/2016', 'exhibit_foreign_principal': 'Embassy of the Republic of Azerbaijan ', 'exhibit_url': 'http://www.fara.gov/docs/5926-Exhibit-AB-20160706-83.pdf'}, {'exhibit_date': '04/08/2016', 'exhibit_foreign_principal': 'Embassy of the Republic of Azerbaijan ', 'exhibit_url': 'http://www.fara.gov/docs/5926-Exhibit-AB-20160408-77.pdf'}, {'exhibit_date': '02/01/2016', 'exhibit_foreign_principal': 'Embassy of the Republic of Azerbaijan ', 'exhibit_url': 'http://www.fara.gov/docs/5926-Exhibit-AB-20160201-72.pdf'}, {'exhibit_date': '06/05/2015', 'exhibit_foreign_principal': 'Embassy of the Republic of Azerbaijan ', 'exhibit_url': 'http://www.fara.gov/docs/5926-Exhibit-AB-20150605-62.pdf'}, {'exhibit_date': '01/27/2015', 'exhibit_foreign_principal': 'Embassy of the Republic of Azerbaijan ', 'exhibit_url': 'http://www.fara.gov/docs/5926-Exhibit-AB-20150127-54.pdf'}, {'exhibit_date': '12/17/2014', 'exhibit_foreign_principal': 'Embassy of the Republic of Azerbaijan ', 'exhibit_url': 'http://www.fara.gov/docs/5926-Exhibit-AB-20141217-52.pdf'}, {'exhibit_date': '04/30/2014', 'exhibit_foreign_principal': 'Embassy of the Republic of Azerbaijan ', 'exhibit_url': 'http://www.fara.gov/docs/5926-Exhibit-AB-20140430-41.pdf'}, {'exhibit_date': '04/04/2013', 'exhibit_foreign_principal': 'Embassy of the Republic of Azerbaijan ', 'exhibit_url': 'http://www.fara.gov/docs/5926-Exhibit-AB-20130404-27.pdf'}, {'exhibit_date': '01/31/2013', 'exhibit_foreign_principal': 'Uruguay ', 'exhibit_url': 'http://www.fara.gov/docs/5926-Exhibit-AB-20130131-23.pdf'}, {'exhibit_date': '03/15/2017', 'exhibit_foreign_principal': 'Random 1 ', 'exhibit_url': 'random_url_1.pdf'}, {'exhibit_date': '03/15/2018', 'exhibit_foreign_principal': 'Random 2 ', 'exhibit_url': 'random_url_2'}
        ]
        mock_foreign_principal = 'Azerbaijan'

        actual_exhibit_url = ForeignPrincipalsSpider.get_exhibit_url_when_multiple_present(
            mock_exhibit_url_row_data_list, mock_foreign_principal)
        expected_exhibit_url = 'http://www.fara.gov/docs/5926-Exhibit-AB-20170223-94.pdf'
        assert actual_exhibit_url == expected_exhibit_url


def mock_response_from_file(file_name, url):
    """
    Create a Scrapy mock HTTP response from a HTML file
    @param file_name: The relative filename from the responses directory,
                      but absolute paths are also accepted.
    @param url: The URL of the response.
    returns: A scrapy HTTP response which can be used for unittesting.
    """

    request = Request(url=url)
    if not file_name[0] == '/':
        responses_dir = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(responses_dir, file_name)
    else:
        file_path = file_name

    file_content = str(open(file_path, 'r').read())

    response = HtmlResponse(
        url=url, request=request, body=file_content, encoding='utf-8')
    return response
