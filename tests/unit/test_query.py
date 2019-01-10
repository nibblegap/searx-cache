from searx.query import RawTextQuery
from unittest import TestCase


class TestQuery(TestCase):

    def test_simple_query(self):
        query_text = 'the query'
        query = RawTextQuery(query_text, [])
        query.parse_query()

        self.assertEqual(query.getFullQuery(), query_text)
        self.assertEqual(len(query.query_parts), 1)
        self.assertEqual(len(query.languages), 0)
        self.assertFalse(query.specific)

    def test_language_code(self):
        language = 'es-ES'
        query_text = 'the query'
        full_query = ':' + language + ' ' + query_text
        query = RawTextQuery(full_query, [])
        query.parse_query()

        self.assertEqual(query.getFullQuery(), full_query)
        self.assertEqual(len(query.query_parts), 3)
        self.assertEqual(len(query.languages), 1)
        self.assertIn(language, query.languages)
        self.assertFalse(query.specific)

    def test_language_name(self):
        language = 'english'
        query_text = 'the query'
        full_query = ':' + language + ' ' + query_text
        query = RawTextQuery(full_query, [])
        query.parse_query()

        self.assertEqual(query.getFullQuery(), full_query)
        self.assertEqual(len(query.query_parts), 3)
        self.assertIn('en', query.languages)
        self.assertFalse(query.specific)

    def test_unlisted_language_code(self):
        language = 'all'
        query_text = 'the query'
        full_query = ':' + language + ' ' + query_text
        query = RawTextQuery(full_query, [])
        query.parse_query()

        self.assertEqual(query.getFullQuery(), full_query)
        self.assertEqual(len(query.query_parts), 3)
        self.assertIn('all', query.languages)
        self.assertFalse(query.specific)

    def test_invalid_language_code(self):
        language = 'not_a_language'
        query_text = 'the query'
        full_query = ':' + language + ' ' + query_text
        query = RawTextQuery(full_query, [])
        query.parse_query()

        self.assertEqual(query.getFullQuery(), full_query)
        self.assertEqual(len(query.query_parts), 1)
        self.assertEqual(len(query.languages), 0)
        self.assertFalse(query.specific)
