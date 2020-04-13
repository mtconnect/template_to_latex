# template_to_latex
Automating new content defined in Templates from Project Site into the MTConnect Standard LaTeX documents.


Templates
---------

Following are the Templates defined. The usages and examples can be found in `templates/`. For more detailed examples, refer to `templates/newcontent_1.6`.

* Glossary Entry Template
  
  To add or update a term in the Glossary.

* New Section Template
  
  To add or update a section.

* Kind Template
  
  To add or update a row entry in a Table.
  
  * Can also be done using `newSectionTemplate`

* Component Template
  
  To add or update a Component.
  
  * Can also be done using `newSectionTemplate`

* Composition Template
  
  To add or update a Composition.
  
  * Can also be done using `newSectionTemplate`

* Event Template
  
  To add or update a dataitem type of category = EVENT

* Sample Template
  
  To add or update a dataitem type of category = SAMPLE


LaTeX Documents
---------------

MTConnect Standard documents are maintained in latex files using the Overleaf platform (See https://www.overleaf.com/ for more details.)

See `overleaf/` for different versions of the MTconnect Standard as generated using code and maintained in Overleaf.


# How to use

Update Paths
------------

Update Perl and LaTeX path in the config file `config/template.cfg` and verify the names of all the MTConnect Part LaTeX projects.


Update Template Content
-----------------------

Within `templates/` create a new directory `newcontent_X`, where `X` is version number. Look at the existing directories for example and guidance.

Note: Make sure to update path of latex directory in `config/template.cfg` to match the `X` version number mentioned above.


Update Overleaf Respositories
-----------------------------

Within `overleaf/` clone the overleaf git repository for the latest version. Use existing clones of older versions as an example on how to name the new cloned repository.


Run
---

Before running the code, make sure the following things have been addressed:

* Templated content are correctly edited.
* If creating redline (using latexdiff) documents, uncomment lines 275-280 in `writetodoc.py`.
* If not creating redline documents and want to sort the rows in the tables do the following:
  * Update the argument `sort` to `sort = True` in line 316 in `writetodoc.py`.
  * Add the names of tables to be sorted if not already mentioned in list `tables_to_sort` on line 326 in `writetodoc.py`.

To generate documents, run the following code:
  
  `python writetodoc.py`
