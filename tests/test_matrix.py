from unittest import TestCase, skip
from unittest.mock import Mock
from worchestic.matrix import (
    Matrix,
    MatrixOutput,
    LockedOutput,
    AlreadyUnlocked,
)

from utils import make_signal


class MatrixOuputTests(TestCase):
    def setUp(self):
        self.idx = 0
        self.o = MatrixOutput(Mock(), self.idx)

    def test_output_select_forwards_call_to_matrix(self):
        source = make_signal()
        self.o.select(source)
        self.o._device._select.assert_called_with(self.idx, source)

    def test_output_select_locks_output(self):
        source = make_signal()
        self.o.select(source)
        self.assertTrue(self.o.locked)

    def test_output_select_sets_sources_atttribute(self):
        source = make_signal()
        self.o.select(source)
        self.assertEqual(self.o._source, source)

    def test_output_select_doesnt_lock_output_with_nolock(self):
        source = make_signal()
        self.o.select(source, nolock=True)
        self.assertFalse(self.o.locked)

    def test_claiming_an_output_locks_it(self):
        self.o.claim()
        self.assertTrue(self.o.locked)

    def test_selecting_on_a_locked_outout_raises_LockedOutput(self):
        self.o.select(make_signal())
        with self.assertRaises(LockedOutput):
            self.o.select(make_signal())

    def test_releasing_an_output_allows_reassignment(self):
        self.o.claim()
        self.o.release()
        self.o.select(make_signal())

    def test_unlock_doesnt_happen_if_release_arent_balanced(self):
        self.o.claim()
        self.o.claim()
        self.o.release()
        self.assertTrue(self.o.locked)

    def test_unlock_happens_if_release_are_balanced(self):
        self.o.claim()
        self.o.claim()
        self.o.release()
        self.o.release()
        self.assertFalse(self.o.locked)

    def test_releasing_an_unlocked_output_raises_AlreadyUnlocked(self):
        with self.assertRaises(AlreadyUnlocked):
            self.o.release()


class SimpleMatrixTests(TestCase):
    def setUp(self):
        self.driver = Mock()
        self.sources = [make_signal(), make_signal(), None]
        self.m = Matrix("simple", self.driver, self.sources, 2)

    def test_matrix_is_truthy(self):
        self.assertTrue(self.m)

    def test_aavailable_source_with_no_cascade_reports_valid_inputs(self):
        self.assertSetEqual(self.m.available_sources,
                            set([
                                s for s in
                                self.sources
                                if s is not None
                            ]))

    def test_select_on_single_matrix_calls_the_driver(self):
        self.m.select(1, self.sources[0])
        self.driver.select.assert_called_with(1, 0)

    def test_can_construct_matrix_cascades(self):
        sources2 = [make_signal(), make_signal()]
        m2 = Matrix("m2", Mock(), sources2, 2)
        master = Matrix("master", Mock(), self.m.outputs + m2.outputs, 2)
        self.assertTrue(master)

    def test_select_on_single_matrix_updates_the_source_of_the_output(self):
        self.m.select(1, self.sources[0])
        self.assertEqual(self.m.outputs[1].source, self.sources[0])


class TwoLevelMatrixTests(TestCase):
    """Two level matrix checks the basic interactions
    bwtween matrix an outputs as inputs"""
    def setUp(self):
        self.sources1 = [make_signal(), make_signal(), make_signal()]
        self.m1 = Matrix("m1", Mock(), self.sources1, 2)
        # Share the middle source on both leaf matricies
        self.sources2 = [self.sources1[1], make_signal()]
        self.m2 = Matrix("m2", Mock(), self.sources2, 2)
        self.root_m = Matrix("root",
                             Mock(),
                             self.m1.outputs + self.m2.outputs, 3)

    def test_available_source_removes_repeated_options(self):
        self.assertSetEqual(self.root_m.available_sources,
                            set(self.sources1 + [self.sources2[1]]))

    def test_iter_sources_has_pathlen2_and_all_sources(self):
        sources = list(self.root_m.iter_sources())
        self.assertEqual(len(sources), 10)
        self.assertEqual([s.path_len for s in sources], [2] * 10)

    def test_selecting_a_source_at_the_root_selects_it_at_the_leaf(self):
        self.root_m.select(0, self.sources1[1])
        # Actaully  the driver being called with either (0,0), or (0,1)
        # is valid but it depends on the routing algo which one
        # is actually chosen - the current code chooses (0,0)
        self.root_m._driver.select.assert_called_with(0, 0)
        self.m1._driver.select.assert_called_with(0, 1)

    def test_selecting_a_second_source_doesnt_reuse_a_path(self):
        self.root_m.select(0, self.sources1[1])
        self.root_m._driver.select.assert_called_with(0, 0)
        self.m1._driver.select.assert_called_with(0, 1)
        self.root_m.select(1, self.sources1[0])
        self.root_m._driver.select.assert_called_with(1, 1)
        self.m1._driver.select.assert_called_with(1, 0)

    def tie_up_m1(self):
        # Tie up all the outputs from _m1.
        self.root_m.select(0, self.sources1[1])
        self.root_m._driver.select.assert_called_with(0, 0)
        self.m1._driver.select.assert_called_with(0, 1)
        self.root_m.select(1, self.sources1[0])
        self.root_m._driver.select.assert_called_with(1, 1)
        self.m1._driver.select.assert_called_with(1, 0)

    def test_selecting_an_unroutable_source_raises_an_exception(self):
        self.tie_up_m1()
        # Select a source only available on an m1 output
        with self.assertRaises(Exception):
            self.root_m.select(2, self.sources1[2])

    def test_reselecting_an_ouptut_works_if_resource_are_swapped(self):
        self.tie_up_m1()
        # Select a source only available on an m1 output
        self.root_m.select(1, self.sources1[2])

    def test_reselecting_an_ouptut_releases_uinused_resources(self):
        self.tie_up_m1()
        # Select a source only available on an m1 output
        self.root_m.select(1, self.sources2[1])
        self.assertEqual(
                1,
                # Count locked outputs
                sum(1 for o in self.m1.outputs if o.locked)
        )

    def test_selecting_an_ouptut_as_a_mirror_claims_and_existing_input(self):
        self.tie_up_m1()
        # Select an alreay in use source
        self.root_m.select(0, self.sources1[0])
        self.assertFalse(self.m1.outputs[0].locked)
        self.assertEqual(self.m1.outputs[1]._sem.load(), 2)


class ThreeLevelMatrixTests(TestCase):
    """A three level system is need to test
    recursion happens correctly""
    """
    def setUp(self):
        self.sources1 = [make_signal(), make_signal(), make_signal()]
        self.m1 = Matrix("m1", Mock(), self.sources1, 2)
        # Share the middle source on both leaf matricies
        self.sources2 = [self.sources1[1], make_signal()]
        self.m2 = Matrix("m2", Mock(), self.sources2, 2)
        self.sources3 = [make_signal(), make_signal()]
        self.m3 = Matrix("m3", Mock(), self.sources3, 2)
        self.n1 = Matrix("n1",
                         Mock(),
                         self.m1.outputs + [self.m2.outputs[0]], 2)

        self.n2 = Matrix("n2",
                         Mock(),
                         self.m3.outputs + [self.m2.outputs[1]], 2)

        self.root_m = Matrix("root",
                             Mock(),
                             self.n1.outputs + self.n2.outputs, 3)

    def test_selecting_in_input_recursively_claims_outputs(self):
        self.root_m.select(0, self.sources1[0])
        self.assertEqual(
                1,
                # Count locked outputs
                sum(1 for o in self.m1.outputs if o.locked)
        )
        self.assertEqual(
                1,
                # Count locked outputs
                sum(1 for o in self.n1.outputs if o.locked)
        )

    def test_a_selecting_a_different_input_recursively_releases_outputs(self):
        self.root_m.select(0, self.sources1[0])
        self.root_m.select(0, self.sources3[0])
        self.assertEqual(
                0,
                # Count locked outputs
                sum(1 for o in self.n1.outputs if o.locked)
        )
        self.assertEqual(
                0,
                # Count locked outputs
                sum(1 for o in self.m1.outputs if o.locked)
        )

    def test_updating_a_selected_input_source_cascades_to_the_output(self,):
        self.root_m.select(0, self.sources1[0])
        self.assertEqual(self.root_m.outputs[0].uuid, self.sources1[0].uuid)
        self.m1.replug_input(0, self.sources3[-1])
        self.assertEqual(self.root_m.outputs[0].uuid, self.sources3[-1].uuid)
