# -*- coding: utf8 -*-

import sys, os, re
sys.path.append(os.path.abspath('.'))

import pylons.test

from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model

from paste.deploy import appconfig

import importfunctions

dictdata_path = 'quanthistling/dictdata'
