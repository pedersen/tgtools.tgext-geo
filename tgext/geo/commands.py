"""Paster Commands, for use tgext.geo project

The command(s) listed here are for use with Paste to enable easy creation of
various tgext.geo files. The controller, model and layer commands are based
on the MapFish paster commands.

Currently available commands:

    geo-controller, geo-model, geo-layer, geo-tilecache
"""

import os
import sys
from ConfigParser import ConfigParser, NoOptionError

from paste.script.command import Command, BadCommand
from paste.script.filemaker import FileOp

import pylons.util as util

__all__ = ['TGGeoControllerCommand', 'TGGeoModelCommand', \
		'TGGeoLayerCommand', 'TGGeoTileCacheCommand']

def can_import(name):
    """Attempt to __import__ the specified package/module, returning True when
    succeeding, otherwise False"""
    try:
        __import__(name)
        return True
    except ImportError:
        return False

def validateName(name):
    """Validate that the name for the layer isn't present on the
    path already"""
    if not name:
        # This happens when the name is an existing directory
        raise BadCommand('Please give the name of a layer.')
    # 'setup' is a valid controller name, but when paster controller is ran
    # from the root directory of a project, importing setup will import the
    # project's setup.py causing a sys.exit(). Blame relative imports
    if name != 'setup' and can_import(name):
        raise BadCommand(
            "\n\nA module named '%s' is already present in your "
            "PYTHON_PATH.\nChoosing a conflicting name will likely cause "
            "import problems in\nyour controller at some point. It's "
            "suggested that you choose an\nalternate name, and if you'd "
            "like that name to be accessible as\n'%s', add a route "
            "to your projects config/routing.py file similar\nto:\n"
            "    map.connect('%s', controller='my_%s')" \
            % (name, name, name, name))
    return True


class TGGeoControllerCommand(Command):
    """Create a geo controller and accompanying functional test

    The TGGeoController command will create the standard controller template
    file and associated functional test.

    Example usage::

        yourproj% paster geo-controller foos
        Creating yourproj/yourproj/controllers/foos.py
        Creating yourproj/yourproj/tests/functional/test_foos.py

    If you'd like to have controllers underneath a directory, just include
    the path as the controller name and the necessary directories will be
    created for you::

        yourproj% paster geo-controller admin/foos
        Creating yourproj/controllers/admin
        Creating yourproj/yourproj/controllers/admin/foos.py
        Creating yourproj/yourproj/tests/functional/test_admin_foos.py
    """
    summary = __doc__.splitlines()[0]
    usage = '\n' + __doc__

    min_args = 1
    max_args = 1
    group_name = 'tgext.geo'

    default_verbosity = 3

    parser = Command.standard_parser(simulate=True)
    parser.add_option('--no-test',
                      action='store_true',
                      dest='no_test',
                      help="Don't create the test; just the controller")

    def command(self):
        """Main command to create a tgext.geo controller"""
        try:
            fileOp = FileOp(source_dir=os.path.join(
                os.path.dirname(__file__), 'paster_templates'))
            try:
                name, directory = fileOp.parse_path_name_args(self.args[0])
            except:
                raise BadCommand('No egg_info directory was found')

            # read layers.ini
            config = ConfigParser()
            config.read(['layers.ini'])
            # check passed layer is in layers.ini
            if not config.has_section(name):
                raise BadCommand(
                    'There is no layer named %s in layers.ini' % name)

            # get layer parameters
            singularName = config.get(name, 'singular')
            pluralName = config.get(name, 'plural')
            epsg = config.get(name, 'epsg')
            units = config.get(name, 'units')

            # check the name isn't the same as the package
            basePkg = fileOp.find_dir('controllers', True)[0]
            if basePkg.lower() == name.lower():
                raise BadCommand(
                    'Your controller name should not be the same as '
                    'the package name %s' % basePkg)

            # validate the name
            name = name.replace('-', '_')
            validateName(name)

            # set test file name
            fullName = os.path.join(directory, name)
            if not fullName.startswith(os.sep):
                fullName = os.sep + fullName
            testName = fullName.replace(os.sep, '_')[1:]

            # set template vars
            modName = name
            fullModName = os.path.join(directory, name)
            contrClass = util.class_name_from_module_name(name)
            modelClass = util.class_name_from_module_name(singularName)
            modelTabObj = name + '_table'

            # setup the controller
            fileOp.template_vars.update(
                {'modName': modName,
                 'fullModName': fullModName,
                 'singularName': singularName,
                 'pluralName': pluralName,
                 'contrClass': contrClass,
                 'modelClass': modelClass,
                 'modelTabObj': modelTabObj,
                 'basePkg': basePkg,
                 'epsg': epsg,
                 'units': units})
            fileOp.copy_file(template='controller.py_tmpl',
                         dest=os.path.join('controllers', directory),
                         filename=name)
            if not self.options.no_test:
                fileOp.copy_file(template='test_controller.py_tmpl',
                             dest=os.path.join('tests', 'functional'),
                             filename='test_' + testName)

        except BadCommand, e:
            raise BadCommand('An error occurred. %s' % e)
        except:
            msg = str(sys.exc_info()[1])
            raise BadCommand('An unknown error occurred. %s' % msg)

class TGGeoModelCommand(Command):
    """Create a geo model

    The TGGeoModel command will create the standard model template file.

    Example usage::

        yourproj% paster geo-model foos
        Creating yourproj/yourproj/model/foos.py

    If you'd like to have models underneath a directory, just include
    the path as the model name and the necessary directories will be
    created for you::

        yourproj% paster geo-model admin/foos
        Creating yourproj/model/admin
        Creating yourproj/yourproj/model/admin/foos.py
    """
    summary = __doc__.splitlines()[0]
    usage = '\n' + __doc__

    min_args = 1
    max_args = 1
    group_name = 'tgext.geo'

    default_verbosity = 3

    parser = Command.standard_parser(simulate=True)

    def command(self):
        """Main command to create tgext.geo model"""
        try:
            fileOp = FileOp(source_dir=os.path.join(
                os.path.dirname(__file__), 'paster_templates'))
            try:
                name, directory = fileOp.parse_path_name_args(self.args[0])
            except:
                raise BadCommand('No egg_info directory was found')

            # read layers.ini
            config = ConfigParser()
            config.read(['layers.ini'])
            # check passed layer is in layers.ini
            if not config.has_section(name):
                raise BadCommand(
                    'There is no layer named %s in layers.ini' % name)

            # get layer parameters
            singularName = config.get(name, 'singular')
            db = config.get(name, 'db')
            table = config.get(name, 'table')
            epsg = config.get(name, 'epsg')
            idColType, idColName = \
                config.get(name, 'idcolumn').split(':')[:2]
            geomColName = config.get(name, 'geomcolumn')

            # check the name isn't the same as the package
            basePkg = fileOp.find_dir('controllers', True)[0]
            if basePkg.lower() == name.lower():
                raise BadCommand(
                    'Your controller name should not be the same as '
                    'the package name %s' % basePkg)

            # validate the name
            name = name.replace('-', '_')
            validateName(name)

            # set template vars
            modelClass = util.class_name_from_module_name(singularName)
            modelTabObj = name + '_table'

            # setup the model
            fileOp.template_vars.update(
                {'modelClass': modelClass,
                 'modelTabObj': modelTabObj,
                 'db': db,
                 'table': table,
                 'epsg': epsg,
                 'idColType': idColType,
                 'idColName': idColName,
                 'geomColName': geomColName})
            fileOp.copy_file(template='model.py_tmpl',
                         dest=os.path.join('model', directory),
                         filename=name)

        except BadCommand, e:
            raise BadCommand('An error occurred. %s' % e)
        except:
            msg = str(sys.exc_info()[1])
            raise BadCommand('An unknown error occurred. %s' % msg)

class TGGeoLayerCommand(Command):
    """Create a geo layer (controller + model).

    The TGGeoLayer command will create the standard controller and model
    template files. It combines the TGGeoController and TGGeoModel
    commands.

    Example usage::

        yourproj% paster geo-layer foos
        Creating yourproj/yourproj/controllers/foos.py
        Creating yourproj/yourproj/tests/functional/test_foos.py
        Creating yourproj/yourproj/model/foos.py

    If you'd like to have controllers and models underneath a directory, just
    include the path as the controller name and the necessary directories will
    be created for you::

        yourproj% paster geo-layer admin/foos
        Creating yourproj/controllers/admin
        Creating yourproj/yourproj/controllers/admin/foos.py
        Creating yourproj/yourproj/tests/functional/test_admin_foos.py
        Creating yourproj/model/admin
        Creating yourproj/yourproj/model/admin/foos.py
    """
    summary = __doc__.splitlines()[0]
    usage = '\n' + __doc__

    min_args = 1
    max_args = 1
    group_name = 'tgext.geo'

    default_verbosity = 3

    parser = Command.standard_parser(simulate=True)
    parser.add_option('--no-test',
                      action='store_true',
                      dest='no_test',
                      help="Don't create the test; just the controller")

    def run(self, args):
        try:
            contrCmd = TGGeoControllerCommand('geo-controller')
            contrCmd.run(args)
            modelCmd = TGGeoModelCommand('geo-model')
            modelCmd.run(args)
        except BadCommand, e:
            raise BadCommand('An error occurred. %s' % e)
        except:
            msg = str(sys.exc_info()[1])
            raise BadCommand('An unknown error occurred. %s' % msg)

class TGGeoTileCacheCommand(Command):
    """Create a tilecache controller and accompanying functional test

    The TGGeoTileCache command will create the tilecache controller template
    file and associated functional test.

    Example usage::

        yourproj% paster geo-tilecache tiles
        Creating yourproj/yourproj/controllers/tiles.py
        Creating yourproj/yourproj/tests/functional/test_tiles.py

    If you'd like to have controllers underneath a directory, just include
    the path as the controller name and the necessary directories will be
    created for you::

        yourproj% paster geo-controller admin/tiles
        Creating yourproj/controllers/admin
        Creating yourproj/yourproj/controllers/admin/tiles.py
        Creating yourproj/yourproj/tests/functional/test_admin_tiles.py
    """
    summary = __doc__.splitlines()[0]
    usage = '\n' + __doc__

    min_args = 1
    max_args = 1
    group_name = 'tgext.geo'

    default_verbosity = 3

    parser = Command.standard_parser(simulate=True)
    parser.add_option('--no-test',
                      action='store_true',
                      dest='no_test',
                      help="Don't create the test; just the controller")

    def command(self):
        """Main command to create a tgext.geo tilecache controller"""
        try:
            fileOp = FileOp(source_dir=os.path.join(
                os.path.dirname(__file__), 'paster_templates'))
            try:
                name, directory = fileOp.parse_path_name_args(self.args[0])
            except:
                raise BadCommand('No egg_info directory was found')

            # read tilecache.cfg
            config = ConfigParser()
            config.read(['tilecache.cfg'])
            # check for cache section in tilecache.cfg
            if not config.has_section('cache'):
                raise BadCommand(
                    'There is no cache path defined in tilecache.cfg')

            # get the sections
            sections = config.sections()

            # create the template vars
            tilecacheLayers = []
            importString = ''
            layersString = ''
            for section in config.sections():
                if (section == 'cache'):
                    baseDir = config.get(section, 'base')
                    cacheType = config.get(section, 'type')
                else:
                    params = {}
                    params['layer'] = section
                    layersString += '\n    "%s": ' % section
                    for item in config.items(section):
                        params['%s' % item[0]] = item[1]
                        if (item[0] == 'type'):
                            importString += 'from TileCache.Layers import %s as %s\n' % (item[1], item[1])
                            layersString += '%s.%s("%s", ' % (item[1], item[1], section)
                    for item in config.items(section):
                        if (item[0] == 'url'):
                            layersString += '"%s", ' % item[1]
                    layersString += '\n\t'
                    for item in config.items(section):
                        if (item[0] not in ['url', 'type']):
                            layersString += '%s="%s", ' % (item[0], item[1])
                    layersString = layersString[:-2] + '),'
                    d = {}
                    d['%s' % section] = params #config.items(section)
                    tilecacheLayers.append(d)
            layersString = layersString[:-1] + '\n'

            # create import strings
            

            # check the name isn't the same as the package
            basePkg = fileOp.find_dir('controllers', True)[0]
            if basePkg.lower() == name.lower():
                raise BadCommand(
                    'Your tilecache controller name should not be '
                    'the same as the package name %s' % basePkg)

            # validate the name
            name = name.replace('-', '_')
            validateName(name)

            # set test file name
            fullName = os.path.join(directory, name)
            if not fullName.startswith(os.sep):
                fullName = os.sep + fullName
            testName = fullName.replace(os.sep, '_')[1:]

            # set template vars
            modName = name
            fullModName = os.path.join(directory, name)
            contrClass = util.class_name_from_module_name(name)

            # setup the tilecache controller
            fileOp.template_vars.update(
                {'modName': modName,
                 'fullModName': fullModName,
                 'contrClass': contrClass,
                 'basePkg': basePkg,
                 'baseDir': baseDir,
                 'cacheType': cacheType,
                 'importString': importString,
                 'layersString': layersString,
                 'tilecacheLayers': tilecacheLayers})
            fileOp.copy_file(template='tilecache.py_tmpl',
                         dest=os.path.join('controllers', directory),
                         filename=name)
            if not self.options.no_test:
                fileOp.copy_file(template='test_controller.py_tmpl',
                             dest=os.path.join('tests', 'functional'),
                             filename='test_' + testName)

        except BadCommand, e:
            raise BadCommand('An error occurred. %s' % e)
        except:
            msg = str(sys.exc_info()[1])
            raise BadCommand('An unknown error occurred. %s' % msg)

