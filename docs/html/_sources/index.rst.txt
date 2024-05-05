BIM-DES integration demo
========================

**Authors:**

* Yin-Chi Chan, Institute for Manufacturing, University of Cambridge (maintainer)
* Nicola Moretti, Bartlett School of Sustainable Construction, University College London

This Python package contains code for a BIM-DES (building information modelling and discrete event
simulation) integration model of the histopathology lab at Addenbrooke's Hospital, Cambridge, UK.
By parsing an .ifc (`Industry Foundation Classes <https://technical.buildingsmart.org/standards/ifc/>`_)
file, a :py:class:`~histopath_bim_des.config.runners.RunnerTimesConfig` object can be constructed,
which is used in turn to build a simulation model that can estimate key performance indicators such
as the proportion of specimens completed within a given number of days.

By enabling or disabling pathways in the parsed .ifc file, different runner times will be
calculated, resulting in different performance with respect to the key performance indicators
(KPIs) such as mean lab turnaround time (TAT) and service level (% of lab TAT less than *N* days).
Examples can be found in the ``notebooks/`` directory of this project.

.. toctree::
   :maxdepth: 2
   :caption: Contents

   config
   simulation
   processes
   `Jupyter notebooks <https://github.com/yinchi/histopath-bim-des/tree/main/notebooks>`_

.. toctree::
   :maxdepth: 2
   :caption: API reference:

   apidoc/histopath_bim_des

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
