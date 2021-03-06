.. note::
    :class: sphx-glr-download-link-note

    Click :ref:`here <sphx_glr_download_auto_examples_fingerprint_optimalpresenter.py>` to download the full example code
.. rst-class:: sphx-glr-example-title

.. _sphx_glr_auto_examples_fingerprint_optimalpresenter.py:


=============================
Optimal presenter
=============================

An example of how to reorder stimuli with the optimal presenter class




.. code-block:: python


    # Code source: Andrew Heusser
    # License: MIT

    import numpy as np
    import quail
    from quail import Fingerprint, OptimalPresenter

    # generate some fake data
    next_presented = ['CAT', 'DOG', 'SHOE', 'BAT']
    next_recalled = ['DOG', 'CAT', 'BAT', 'SHOE']

    next_features = [{
                        'category' : 'animal',
                        'size' : 'bigger',
                        'starting letter' : 'C',
                        'length' : 3
                     },
                     {
                        'category' : 'animal',
                        'size' : 'bigger',
                        'starting letter' : 'D',
                        'length' : 3
                     },
                     {
                        'category' : 'object',
                        'size' : 'smaller',
                        'starting letter' : 'S',
                        'length' : 4
                     },
                     {
                        'category' : 'animal',
                        'size' : 'bigger',
                        'starting letter' : 'B',
                        'length' : 3
                     }]

    egg = quail.Egg(pres=[next_presented], rec=[next_recalled], features=[next_features])

    # initialize fingerprint
    fingerprint = Fingerprint(init=egg)

    # initialize presenter
    params = {
        'fingerprint' : fingerprint}
    presenter = OptimalPresenter(params=params, strategy='stabilize')

    # update the fingerprint
    fingerprint.update(egg)

    # reorder next list
    reordered_egg = presenter.order(egg, method='permute', nperms=100)

**Total running time of the script:** ( 0 minutes  0.000 seconds)


.. _sphx_glr_download_auto_examples_fingerprint_optimalpresenter.py:


.. only :: html

 .. container:: sphx-glr-footer
    :class: sphx-glr-footer-example



  .. container:: sphx-glr-download

     :download:`Download Python source code: fingerprint_optimalpresenter.py <fingerprint_optimalpresenter.py>`



  .. container:: sphx-glr-download

     :download:`Download Jupyter notebook: fingerprint_optimalpresenter.ipynb <fingerprint_optimalpresenter.ipynb>`


.. only:: html

 .. rst-class:: sphx-glr-signature

    `Gallery generated by Sphinx-Gallery <https://sphinx-gallery.readthedocs.io>`_
