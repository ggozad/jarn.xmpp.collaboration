from setuptools import setup, find_packages
import os

version = '0.1b3'

setup(name='jarn.xmpp.collaboration',
      version=version,
      description="Collaborative editing for Plone",
      long_description=open("README.rst").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Development Status :: 3 - Alpha",
        "Framework :: Plone",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        ],
      keywords='',
      author='Yiorgis Gozadinos',
      author_email='ggozad@jarn.com',
      url='https://github.com/ggozad/jarn.xmpp.collaboration',
      license='GPL',
      packages=find_packages(),
      namespace_packages=['jarn', 'jarn.xmpp'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'jarn.xmpp.core'
      ],
      extras_require = {
          'test': [
              'plone.app.testing',
              ],
          'dexterity': [
              'plone.app.dexterity',
              'plone.app.referenceablebehavior',
              ]
      },
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
