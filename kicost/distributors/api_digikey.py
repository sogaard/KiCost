# -*- coding: utf-8 -*-
# MIT license
#
# Copyright (C) 2021 by Salvador E. Tropea / Instituto Nacional de Tecnologia Industrial
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Author information.
__author__ = 'Salvador Eduardo Tropea'
__webpage__ = 'https://github.com/set-soft'
__company__ = 'Instituto Nacional de Tecnologia Industrial - Argentina'

# Libraries.
import pprint

# KiCost definitions.
from ..global_vars import DEBUG_OVERVIEW, DEBUG_DETAILED, DEBUG_OBSESSIVE, W_NOINFO, KiCostError, ERR_SCRAPE, W_APIFAIL
from .. import DistData
# Distributors definitions.
from .distributor import distributor_class

available = True
try:
    from kicost_digikey_api_v3 import by_digikey_pn, by_manf_pn, by_keyword, configure, DigikeyError
except ImportError:
    available = False
# from kicost_digikey_api_v3 import by_digikey_pn, by_manf_pn, by_keyword, configure, DigikeyError  # noqa: E402

DIST_NAME = 'digikey'

__all__ = ['api_digikey']


class api_digikey(distributor_class):
    name = 'Digi-Key'
    type = 'api'
    # Currently enabled only by request
    enabled = available
    url = 'https://developer.digikey.com/'  # Web site API information.
    api_distributors = [DIST_NAME]

    @classmethod
    def init_dist_dict(cls):
        if not cls.enabled:
            return
        # Try to configure the plug-in
        try:
            configure(a_logger=distributor_class.logger)
        except DigikeyError as e:
            distributor_class.logger.warning(W_APIFAIL+'Failed to init Digi-Key API, reason: {}'.format(e.args[0]))
            cls.enabled = False
        if cls.enabled:
            distributor_class.add_distributors(cls.api_distributors)

    @staticmethod
    def _query_part_info(parts, distributors, currency):
        '''Fill-in the parts with price/qty/etc info from KitSpace.'''
        if DIST_NAME not in distributors:
            distributor_class.logger.log(DEBUG_OVERVIEW, '# Skipping Digi-Key plug-in')
            return
        distributor_class.logger.log(DEBUG_OVERVIEW, '# Getting part data from Digi-Key...')
        field_cat = DIST_NAME + '#'

        # Setup progress bar to track progress of server queries.
        progress = distributor_class.progress(len(parts), distributor_class.logger)
        for part in parts:
            data = None
            # Get the Digi-Key P/N for this part
            part_stock = part.fields.get(field_cat)
            if part_stock:
                distributor_class.logger.log(DEBUG_DETAILED, '\n**** Digi-Key P/N: {}'.format(part_stock))
                o = by_digikey_pn(part_stock)
                data = o.search()
                if data is None:
                    distributor_class.logger.warning(W_NOINFO+'The \'{}\' Digi-Key code is not valid'.format(part_stock))
                    o = by_keyword(part_stock)
                    data = o.search()
            else:
                # No Digi-Key P/N, search using the manufacturer code
                part_manf = part.fields.get('manf', '')
                part_code = part.fields.get('manf#')
                if part_code:
                    if part_manf:
                        distributor_class.logger.log(DEBUG_DETAILED, '\n**** Manufacturer: {} P/N: {}'.format(part_manf, part_code))
                    else:
                        distributor_class.logger.log(DEBUG_DETAILED, '\n**** P/N: {}'.format(part_code))
                    o = by_manf_pn(part_code)
                    data = o.search()
                    if data is None:
                        o = by_keyword(part_code)
                        data = o.search()
            if data is None:
                distributor_class.logger.warning(W_NOINFO+'No information found at Digi-Key for part/s \'{}\''.format(part.refs))
            else:
                distributor_class.logger.log(DEBUG_OBSESSIVE, '* Part info before adding data:')
                distributor_class.logger.log(DEBUG_OBSESSIVE, pprint.pformat(part.__dict__))
                distributor_class.logger.log(DEBUG_OBSESSIVE, '* Data found:')
                distributor_class.logger.log(DEBUG_OBSESSIVE, str(data))
                part.datasheet = data.primary_datasheet
                part.lifecycle = data.product_status.lower()
                specs = {sp.parameter.lower(): (sp.parameter, sp.value) for sp in data.parameters}
                specs['rohs'] = ('RoHS', data.ro_hs_status)
                part.update_specs(specs)
                dd = part.dd.get(DIST_NAME, DistData())
                dd.qty_increment = dd.moq = data.minimum_order_quantity
                dd.url = data.product_url
                dd.part_num = data.digi_key_part_number
                dd.qty_avail = data.quantity_available
                dd.currency = data.search_locale_used.currency
                dd.description = data.product_description
                dd.price_tiers = {p.break_quantity: p.unit_price for p in data.standard_pricing}
                part.dd[DIST_NAME] = dd
                distributor_class.logger.log(DEBUG_OBSESSIVE, '* Part info after adding data:')
                distributor_class.logger.log(DEBUG_OBSESSIVE, pprint.pformat(part.__dict__))
                distributor_class.logger.log(DEBUG_OBSESSIVE, pprint.pformat(dd.__dict__))
            progress.update(1)
        progress.close()

    @staticmethod
    def query_part_info(parts, distributors, currency):
        msg = None
        try:
            api_digikey._query_part_info(parts, distributors, currency)
        except DigikeyError as e:
            msg = e.args[0]
        if msg is not None:
            raise KiCostError(msg, ERR_SCRAPE)
        return set([DIST_NAME])


distributor_class.register(api_digikey, 100)
