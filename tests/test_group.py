from unittest import TestCase, skip
from unittest.mock import Mock, patch, call
from utils import make_signal
from worchestic.matrix import Matrix
from worchestic.group import MatrixGroup, SourceGroup


class SourceGroupTest(TestCase):
    def setUp(self):
        self.video = [make_signal(), make_signal(), make_signal()]
        self.usb = [make_signal(), make_signal(), make_signal()]
        self.signal_group = SourceGroup(
                    video_a=self.video[:2],
                    video_b=self.video[2:],
                    usb=self.usb
        )

    def test_get_companions_returns_the_empty_list_for_unknown_sources(self):
        self.assertEqual(self.signal_group.get_companions(make_signal), set())

    def test_given_a_source_its_companions_can_be_retrieved(self):
        companions_0 = set([self.video[2], self.usb[0]])
        self.assertSetEqual(set(self.signal_group.get_companions(self.video[0])),
                            companions_0)


class SingalGroupInitTests(TestCase):
    def test_assign_out_set_preferred_ouptut(self):
        self.video = [make_signal(), make_signal(), make_signal(), make_signal()]
        self.usb = [make_signal(), make_signal(), make_signal(), make_signal()]
        self.mat_video = Matrix("video", Mock(), self.video, 2)
        self.mat_usb = Matrix("usb", Mock(), self.usb, 1)
        self.signal_group = SourceGroup(
                    video_a=self.video[:2],
                    video_b=self.video[2:],
                    usb=self.usb,
                    assign_outputs={
                        'usb': self.mat_usb.outputs[0],
                        'video_a': self.mat_video.outputs[0],
                        'video_b': self.mat_video.outputs[1],

                    }
        )
        for i, signal in enumerate(self.video):
            self.assertEqual(
                signal.preferred_out, self.mat_video.outputs[i // 2]
            )
        for i, signal in enumerate(self.usb):
            self.assertEqual(signal.preferred_out, self.mat_usb.outputs[0])



class MatrixGroupTest(TestCase):
    def setUp(self):
        self.video = [make_signal(), make_signal(), make_signal(), make_signal()]
        self.usb = [make_signal(), make_signal(), make_signal(), make_signal()]
        self.signal_group = SourceGroup(
                    video_a=self.video[:2],
                    video_b=self.video[2:],
                    usb=self.usb
        )
        self.mat_video = Matrix("video", Mock(), self.video, 2)
        self.mat_usb = Matrix("usb", Mock(), self.usb, 1)
        for hid in self.usb:
            hid.preferred_out = self.mat_usb.outputs[0]

        for idx, screen in enumerate(self.video):
            screen.preferred_out = self.mat_video.outputs[idx // 2]

        self.mgroup = MatrixGroup(
                self.signal_group,
                usb=self.mat_usb, video=self.mat_video
        )

    def test_selecting_a_source_selects_it_in_the_matrix_and_nothing_else_if_no_companions_is_true(self):
        with patch.object(self.mat_video, "_select") as vid_sel:
            self.mgroup.select("video", 0, self.video[0], no_companions=True)

        self.mat_usb._driver.assert_not_called()
        vid_sel.assert_called_once_with(0, self.video[0])

    def test_selecting_a_source_selects_it_in_the_matrix_and_companions_is_default(self):
        with patch.object(self.mat_video, "_select") as vid_sel, \
             patch.object(self.mat_usb, "_select") as usb_sel:
            self.mgroup.select("video", 0, self.video[0])

        usb_sel.assert_called_once_with(0, self.usb[0])
        vid_sel.assert_has_calls([
                call(0, self.video[0]),
                call(1, self.video[2]),
        ])

    def test_selecting_a_source_selects_it_in_the_matrix_and_skip_companons_for_the_chosen_output(self):
        with patch.object(self.mat_video, "_select") as vid_sel, \
             patch.object(self.mat_usb, "_select") as usb_sel:
            self.mgroup.select("video", 1, self.video[0])

        usb_sel.assert_called_once_with(0, self.usb[0])
        vid_sel.assert_called_once_with(1, self.video[0])

    def test_get_outpots_returns_indexed_ouptut_from_named_matrix(self):
        mname = "video"
        index = 1
        self.assertIs(
            self.mgroup.get_output(mname, index),
            self.mat_video.outputs[index]
        )

    def test_matrixgroup_has_and_available_method_which_it_calls_on_the_sub_matricies(self):
        kbds = self.mgroup.available('usb')
        self.assertSetEqual(kbds, set(self.usb))
