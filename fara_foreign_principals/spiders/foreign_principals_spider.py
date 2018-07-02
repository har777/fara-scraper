# -*- coding: utf-8 -*-

import scrapy
from scrapy.shell import inspect_response
from scrapy.loader import ItemLoader

from difflib import SequenceMatcher

import copy
import arrow

from ..items import FaraForeignPrincipalItem, FaraForeignPrincipalItemLoader
from ..fara_exceptions import (
    ApexFieldMissingError,
    ApexFieldMultipleValuesError,
    SelectorEmptyError,
    UnexpectedValueError
)


class ForeignPrincipalsSpider(scrapy.Spider):
    name = 'foreign_principals_spider'
    start_urls = [
        'https://efile.fara.gov/pls/apex/f?p=171:130:::NO:RP,130:P130_DATERANGE:N',
    ]

    #Will be set to a dict containing apex application data.
    apex_metadata = None
    #Will be set to total number of expected results.
    total_records = None

    def get_next_page_post_body_generator(self, total_rows, rows_per_page):
        """
        generator which returns post request body required to get next page of data.
        """
        first_row_in_page = 1
        while first_row_in_page <= total_rows:
            post_object = copy.deepcopy(self.apex_metadata)
            post_object['p_request'] = 'APXWGT'
            post_object['p_widget_name'] = 'worksheet'
            post_object['p_widget_mod'] = 'ACTION'
            post_object['p_widget_action'] = 'PAGE'

            if total_rows - first_row_in_page >= rows_per_page:
                post_object['p_widget_num_return'] = str(rows_per_page)
                post_object['p_widget_action_mod'] = (
                    'pgR_min_row={pgR_min_row}max_rows={max_rows}rows_fetched={rows_fetched}'.format(
                        pgR_min_row=first_row_in_page, max_rows=rows_per_page, rows_fetched=rows_per_page
                    )
                )
            else:
                post_object['p_widget_num_return'] = str(total_rows - first_row_in_page + 1)
                post_object['p_widget_action_mod'] = (
                    'pgR_min_row={pgR_min_row}max_rows={max_rows}rows_fetched={rows_fetched}'.format(
                        pgR_min_row=first_row_in_page, max_rows=total_rows - first_row_in_page + 1, rows_fetched=total_rows - first_row_in_page + 1
                    )
                )
            first_row_in_page += rows_per_page
            yield post_object


    def parse(self, response):
        self.set_metadata_from_initial_page_table(response)
        for next_page_post_request in self.get_next_page_post_body_generator(
                self.total_records, self.total_records):
            yield scrapy.http.FormRequest(
                'https://efile.fara.gov/pls/apex/wwv_flow.show',
                formdata=next_page_post_request,
                callback=self.extract_data_from_main_page
            )

    @staticmethod
    def parse_apex_xpath_element(selector, apex_field_id):
        """
        Exclusively used for extracting apex metadata fields.
        Each apex metadata field should return only one value.
        Given a xpath selector returns:
        * raises ApexFieldMissingError exception if selector is None.
        * raises ApexFieldMissingError exception if extracted selector is an empty array.
        * raises ApexFieldMultipleValuesError exception if extracted selector array has more than 1 value.
        * returns apex metadata value if extracted selector array has exactly one value.
        """
        if selector is None:
            raise ApexFieldMissingError(
                '{apex_field_id}: {selector}'.format(
                    apex_field_id=apex_field_id, selector=selector))
        else:
            elements = selector.extract()
            if len(elements) == 0:
                raise ApexFieldMissingError(
                    '{apex_field_id}: {elements}'.format(
                        apex_field_id=apex_field_id, elements=elements))
            elif len(elements) > 1:
                raise ApexFieldMultipleValuesError(
                    '{apex_field_id}: {elements}'.format(
                        apex_field_id=apex_field_id, elements=elements))
            else:
                return elements[0]


    @staticmethod
    def check_if_selector_empty(selector, field):
        """
        Raises SelectorEmptyError exception if:
        * selector is None.
        * extracted selector array is empty.
        """
        if selector is None or selector.extract() == []:
            raise SelectorEmptyError(
                'Selector {field} returned {selector}.'.format(field=field, selector=selector)
            )


    def set_metadata_from_initial_page_table(self, response):
        """
        Assigns apex_metadata field for doing further POST requests to the apex application.
        All fields are required to exists and hence raises exceptions in failure at this part.

        apex_metadata fields can actually be manually assigned as constants because they dont change for the app.
        This is automated here just so any future change to the website apex_metadata doesnt screw up the spider.
        """

        www_flow_form = response.selector.xpath('//form[@id="wwvFlowForm"]')
        self.check_if_selector_empty(www_flow_form, 'wwvFlowForm')

        apexir_worksheet = response.selector.xpath('//div[@id="apexir_WORKSHEET"]')
        self.check_if_selector_empty(apexir_worksheet, 'apexir_WORKSHEET')

        p_flow_id = self.parse_apex_xpath_element(
            www_flow_form.xpath(
                './/input[@id="pFlowId"]/@value'), 'pFlowId')

        p_flow_step_id = self.parse_apex_xpath_element(
            www_flow_form.xpath(
                './/input[@id="pFlowStepId"]/@value'), 'pFlowStepId')

        p_instance = self.parse_apex_xpath_element(
            www_flow_form.xpath(
                './/input[@id="pInstance"]/@value'), 'pInstance')

        # p_page_submission_id = self.parse_apex_xpath_element(
        #     www_flow_form.xpath(
        #         './/input[@id="pPageSubmissionId"]/@value'), 'pPageSubmissionId')

        apexir_worksheet_id = self.parse_apex_xpath_element(
            apexir_worksheet.xpath(
                './/input[@id="apexir_WORKSHEET_ID"]/@value'), 'apexir_WORKSHEET_ID(x0)')

        apexir_report_id = self.parse_apex_xpath_element(
            apexir_worksheet.xpath(
                './/input[@id="apexir_REPORT_ID"]/@value'), 'apexir_REPORT_ID(x1)')

        self.apex_metadata = {
            'p_flow_id': p_flow_id,
            'p_flow_step_id': p_flow_step_id,
            'p_instance': p_instance,
            'x01': apexir_worksheet_id,
            'x02': apexir_report_id
        }

        apexir_data_panel = apexir_worksheet.xpath('.//div[@id="apexir_DATA_PANEL"]')
        self.check_if_selector_empty(apexir_data_panel, 'apexir_data_panel')

        total_records_selector = apexir_data_panel.xpath(
            './/td[@class="pagination"]/span[@class="fielddata"]/text()')
        self.check_if_selector_empty(total_records_selector, 'fielddata(total_records_string)')

        total_records_list = total_records_selector.extract()
        if total_records_list is None or len(total_records_list) != 1:
            raise UnexpectedValueError(
                'total_records selector parsing has gone awry, Please check: {total_records_list}'
                .format(total_records_list=total_records_list))

        total_records_string = total_records_list[0].strip().split('of')
        if len(total_records_string) != 2:
            raise UnexpectedValueError(
                'total_records_string parsing has gone awry, Please check: {total_records_string}'
                .format(total_records_string=total_records_string))

        total_records_string = total_records_string[1].strip()
        try:
            self.total_records = int(total_records_string)
        except ValueError as verr:
            print('"%s" cannot be converted to an int: %s' % (total_records_string, verr))


    def extract_data_from_main_page(self, response):
        data_panel = response.selector.xpath('//div[@id="apexir_DATA_PANEL"]')
        worksheet_data = data_panel.xpath('.//table[@class="apexir_WORKSHEET_DATA"]')

        for row in worksheet_data.xpath('.//tr[@class="odd" or @class="even"][td]'):
            foreign_principal_row_data = {}

            partial_url = row.xpath('.//td[contains(@headers, "LINK")]/a/@href').extract_first()
            if partial_url is not None:
                stripped_partial_url = partial_url.split(':')
                stripped_partial_url[2] = ''
                stripped_partial_url = ':'.join(stripped_partial_url)
                full_url = response.urljoin(stripped_partial_url)
            else:
                full_url = None

            foreign_principal_row_data['url'] = full_url
            foreign_principal_row_data['foreign_principal'] = row.xpath(
                './/td[contains(@headers, "FP_NAME")]/text()').extract_first()
            foreign_principal_row_data['address'] = row.xpath(
                './/td[contains(@headers, "ADDRESS_1")]/text()').extract()
            foreign_principal_row_data['state'] = row.xpath(
                './/td[contains(@headers, "STATE")]/text()').extract_first()
            foreign_principal_row_data['registrant'] = row.xpath(
                './/td[contains(@headers, "REGISTRANT")]/text()').extract_first()
            foreign_principal_row_data['reg_num'] = row.xpath(
                './/td[contains(@headers, "REG_NUMBER")]/text()').extract_first()
            #setting to ISO 8601 formatted representation.
            foreign_principal_row_data['date'] = row.xpath(
                './/td[contains(@headers, "FP_REG_DATE")]/text()').extract_first()

            # Ok so this is a bit tricky.
            # Seems like country is in a <th> tag where the id has a number at the end corresponsing to the country.
            # That same id is present at the end of every header tag for the other fields we extract.
            # voila.
            # Another way is using the country found at the end of the url extracted above.
            country_number_id = row.xpath(
                './/td[contains(@headers, "FP_NAME")]/@headers').extract_first().split(' ')[1].split('_')[-1]
            foreign_principal_row_data['country'] = response.xpath(
                '//th[@class="apexir_REPEAT_HEADING" and @id="BREAK_COUNTRY_NAME_{country_number_id}"]/span/text()'.format(
                    country_number_id=country_number_id
                )).extract_first()

            yield scrapy.http.Request(
                response.urljoin(partial_url),
                callback=self.extract_data_from_exhibit_url_page,
                meta={'foreign_principal_row_data': foreign_principal_row_data},
                dont_filter=True
            )


    def extract_data_from_exhibit_url_page(self, response):
        foreign_principal_item = copy.deepcopy(response.meta['foreign_principal_row_data'])

        data_table = response.selector.xpath('//div[@id="apexir_DATA_PANEL"]')
        worksheet_data = data_table.xpath('.//table[@class="apexir_WORKSHEET_DATA"]')
        worksheet_rows = worksheet_data.xpath('.//tr[@class="even" or @class="odd"]')
        worksheet_rows_list = worksheet_rows.extract()

        if len(worksheet_rows_list) == 0:
            #Found no links.
            exhibit_url = None
        elif len(worksheet_rows_list) == 1:
            #Yay only one row. Hence only one link.
            exhibit_urls = worksheet_data.xpath(
                './/td[@headers="DOCLINK"]/a[contains(@target, "Exhibit")]/@href').extract()
            if len(exhibit_urls) == 0:
                exhibit_url = None
            else:
                exhibit_url = exhibit_urls[0]
        else:
            # Dammit multiple urls. Do a string match scoring to select.
            # On equal scores take the latest date link.
            row_data_list = []
            for worksheet_row in worksheet_rows:
                row_data = {
                    'exhibit_date': worksheet_row.xpath(
                            './/td[@headers="DATE_STAMPED"]/text()').extract_first(),
                    'exhibit_foreign_principal': worksheet_row.xpath(
                        './/td[@headers="DOCLINK"]/a[contains(@target, "Exhibit")]/span/text()').extract_first(),
                    'exhibit_url': worksheet_row.xpath(
                        './/td[@headers="DOCLINK"]/a[contains(@target, "Exhibit")]/@href').extract_first(),
                }
                row_data_list.append(row_data)
            exhibit_url = self.get_exhibit_url_when_multiple_present(
                row_data_list, foreign_principal_item['foreign_principal'])

        foreign_principal_item_loader = FaraForeignPrincipalItemLoader(
            item=FaraForeignPrincipalItem())
        foreign_principal_item['exhibit_url'] = exhibit_url
        foreign_principal_item_loader.add_value(None, foreign_principal_item)

        yield foreign_principal_item_loader.load_item()


    @staticmethod
    def get_exhibit_url_when_multiple_present(exhibit_url_row_data_list, foreign_principal):
        """
        Selects exhibit url when multiple instances of the url present.
        exhibit_url_row_data_list: list of dict objects each having the exhibit_date objects, exhibit_url string and exhibit_foreign_princial string.
        exhibit_foreign_principal: actual foreign principal from which exhibit_url page loaded.
        Sort first by date. Then by score. Both descending.
        Hence the first dict will have the url with the highest score and latest date.
        """

        # Add string match score ratios and date objects.
        exhibit_url_row_data_list_with_scores = []
        for row_data in exhibit_url_row_data_list:
            if row_data['exhibit_url'] is not None:
                    row_data['exhibit_score'] = SequenceMatcher(
                        None,
                        row_data['exhibit_foreign_principal'],
                        foreign_principal
                    ).ratio()
                    date_string = row_data['exhibit_date']
                    row_data['exhibit_date'] = arrow.get(date_string, 'MM/DD/YYYY')
                    exhibit_url_row_data_list_with_scores.append(row_data)

        # Sort first by date then by score. Both are in descending order.
        exhibit_url_row_data_list_with_scores = sorted(
            exhibit_url_row_data_list_with_scores, key=lambda key: key['exhibit_date'], reverse=True)
        exhibit_url_row_data_list_with_scores = sorted(
            exhibit_url_row_data_list_with_scores, key=lambda key: key['exhibit_score'], reverse=True)

        if len(exhibit_url_row_data_list_with_scores) != 0:
            return exhibit_url_row_data_list_with_scores[0]['exhibit_url']
        else:
            return None
