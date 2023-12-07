from unittest import TestCase
from worchestic.signals import Source


class SourceTests(TestCase):
    def setUp(self):
        Source.reset_registry()
        self.source = Source(
            name="test"
        )
        self.source2 = Source(
            name="test2"
        )

    def test_that_the_source_class_lists_created_sources(self):
        sources = Source.list()
        self.assertEqual(len(sources), 2)
        self.assertSetEqual(set(sources),
                            set([self.source, self.source2]))

    def test_that_the_source_class_has_get_byuuid_classmethod(self):
        source = Source.get(self.source.uuid)
        self.assertIs(source, self.source)
