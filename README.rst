Worchestic
==========


..  image:: https://github.com/rgammans/worchestic/actions/workflows/unittest.yml/badge.svg
    :alt: Python package tests
    :target: https://github.com/rgammans/worchestic/actions/workflows/unittest.yml

Worchestic is a controller for signal switch fabrics, for connection 
orientated switching, such as traditional telephone systems or video
routing matrices. Worchestic is agnostic on the type of signal being
routed over the fabric.

Worchestic abstracts the actual hardware control to driver classes,
we send the control commands to the fabric, but Worchestic can track
use of outputs from cascaded individual switches and route companion 
signals together across distinct fabrics. Such as USB, and HDMI in 
a KVM switch which is the initial use case Worchestic is targetting.


