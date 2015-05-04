from unittest import TestCase

from algorithms.utils.history import DefaultHistory


#noinspection PyPep8Naming
class TestHistoryBasic(TestCase):
    def setUp(self):
        self.a = DefaultHistory(3, default_factory=None)

    def testOldest(self):
        for oldest in [0, 1, 2]:
            self.a.push(oldest)
        for oldest in [0, 1, 2]:
            self.assertEqual(self.a.oldest(), oldest)
            self.a.next()

    def testNewest(self):
        for oldest in range(3):
            self.a.push(oldest)
        for newest in [2, 3, 4]:
            self.assertEqual(self.a.newest(), newest)
            self.a.push(newest + 1)

    def testManual(self):
        a = self.a
        a.push(42)
        self.assertEqual(a.newest(), 42)
        self.assertEqual(a.oldest(), None)
        a.push(None)
        self.assertEqual(a.newest(), None)
        self.assertEqual(a.oldest(), None)
        a.push(1984)
        self.assertEqual(a.newest(), 1984)
        self.assertEqual(a.oldest(), 42)
        a.push(2000)
        self.assertEqual(a.newest(), 2000)
        self.assertEqual(a.oldest(), None)
        a.push(None)
        self.assertEqual(a.newest(), None)
        self.assertEqual(a.oldest(), 1984)
        a.next()
        self.assertEqual(a.newest(), 1984)

    def testDefault(self):
        for i in range(7 * 7 + 1):
            self.assertEqual(self.a.newest(), None)
            self.assertEqual(self.a.oldest(), None)
            self.a.next()

    def testBig(self):
        for i in range(10):
            self.a.push(i)

        for i in range(10, 1000000):
            self.a.push(i)
            self.assertEqual(self.a.newest(), i)
            self.assertEqual(self.a.oldest(), i - 2)

        self.assertEqual(len(self.a.history), 3)
