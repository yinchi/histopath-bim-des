BIM-DES integration demo
========================

**Authors:**

* `Yin-Chi Chan <https://yinchi.github.io>`_,
  Institute for Manufacturing, University of Cambridge (maintainer)
* `Nicola Moretti <https://profiles.ucl.ac.uk/89826-nicola-moretti/>`_, Bartlett School of Sustainable Construction, University College London

This Python package contains code for a BIM-DES (building information modelling and discrete event
simulation) integration model of the histopathology lab at Addenbrooke's Hospital, Cambridge, UK.
By parsing an .ifc (`Industry Foundation Classes <https://technical.buildingsmart.org/standards/ifc/>`_)
file, a :py:class:`~histopath_bim_des.config.runners.RunnerTimesConfig` object can be constructed,
which is used in turn to build a simulation model that can estimate key performance indicators such
as the proportion of specimens completed within a given number of days.

By enabling or disabling pathways in the parsed .ifc file, different runner times will be
calculated, resulting in different performance with respect to the key performance indicators
(KPIs) such as mean lab turnaround time (TAT) and service level (% of lab TAT less than *N* days).
Examples can be found in the `notebooks/ <https://github.com/yinchi/histopath-bim-des/tree/main/notebooks>`_ directory of this project.


.. toctree::
   :maxdepth: 2
   :caption: Contents
   :hidden:

   Jupyter notebooks 🔗 <https://github.com/yinchi/histopath-bim-des/tree/main/notebooks>
   config
   simulation
   processes

.. toctree::
   :maxdepth: 2
   :caption: Technical 
   :hidden:

   Installation ⬇️ <installation>
   Third-party libraries 📚 <thirdparty>

.. toctree::
   :maxdepth: 2
   :caption: API reference 📖
   :hidden:

   apidoc/histopath_bim_des

.. toctree::
   :maxdepth: 0
   :caption: Indicies and Tables 🔍
   :hidden:

   genindex
   modindex
   search
