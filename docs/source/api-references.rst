.. _api-references:

API References
==============

chartparse.chart module
-----------------------

.. automodule:: chartparse.chart

chartparse.metadata module
--------------------------

.. automodule:: chartparse.metadata

chartparse.globalevents module
------------------------------

.. automodule:: chartparse.globalevents

chartparse.sync module
----------------------

.. automodule:: chartparse.sync

chartparse.instrument module
----------------------------

..
    :exclude-members: value is a hack to hide the `value` attribute added to enums to satisfy mypy.
    This is probably dangerous, because it recursively hides everything named `value` everywhere.
.. automodule:: chartparse.instrument
   :exclude-members: value

chartparse.event module
-----------------------

.. automodule:: chartparse.event

chartparse.track module
-----------------------

.. automodule:: chartparse.track
   :private-members:

chartparse.tick module
-----------------------

.. automodule:: chartparse.tick

chartparse.exceptions module
----------------------------

..
    no-inherited-members prevents an error: `Handler <function process_docstring at
    0x7f3abc09c1f0> for event 'autodoc-process-docstring' threw an exception (exception: no
    signature found for builtin <method 'with_traceback' of 'BaseException' objects>)`
.. automodule:: chartparse.exceptions
   :no-inherited-members:

chartparse.util module
----------------------

.. automodule:: chartparse.util

chartparse.hints module
------------------------------

.. automodule:: chartparse.hints
