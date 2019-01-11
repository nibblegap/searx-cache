# -*- coding: utf-8 -*-

from mock import Mock

from searx.answerers import answerers
from unittest import TestCase


class AnswererTest(TestCase):

    def test_unicode_input(self):
        query = Mock()
        unicode_payload = 'árvíztűrő tükörfúrógép'
        for answerer in answerers:
            query.query = '{} {}'.format(answerer.keywords[0], unicode_payload)
            self.assertTrue(isinstance(answerer.answer(query), list))
