#!/usr/bin/python3
""" Console Module """
import cmd
from datetime import datetime
import re
import os
import sys
import uuid

from models.base_model import BaseModel
from models import storage
from models.user import User
from models.place import Place
from models.state import State
from models.city import City
from models.amenity import Amenity
from models.review import Review


class HBNBCommand(cmd.Cmd):
    """ Contains the functionality for the HBNB console"""

    # determines prompt for interactive/non-interactive modes
    prompt = '(hbnb) ' if sys.__stdin__.isatty() else ''

    classes = {
               'BaseModel': BaseModel, 'User': User, 'Place': Place,
               'State': State, 'City': City, 'Amenity': Amenity,
               'Review': Review
              }
    dot_cmds = ['all', 'count', 'show', 'destroy', 'update']
    types = {
             'number_rooms': int, 'number_bathrooms': int,
             'max_guest': int, 'price_by_night': int,
             'latitude': float, 'longitude': float
            }

    def preloop(self):
        """Prints if isatty is false"""
        if not sys.__stdin__.isatty():
            print('(hbnb)')

    def precmd(self, line):
        """Reformat command line for advanced command syntax.

        Usage: <class name>.<command>([<id> [<*args> or <**kwargs>]])
        (Brackets denote optional fields in usage example.)
        """
        _cmd = _cls = _id = _args = ''  # initialize line elements

        # scan for general formating - i.e '.', '(', ')'
        if not ('.' in line and '(' in line and ')' in line):
            return line

        try:  # parse line left to right
            pline = line[:]  # parsed line

            # isolate <class name>
            _cls = pline[:pline.find('.')]

            # isolate and validate <command>
            _cmd = pline[pline.find('.') + 1:pline.find('(')]
            if _cmd not in HBNBCommand.dot_cmds:
                raise Exception

            # if parantheses contain arguments, parse them
            pline = pline[pline.find('(') + 1:pline.find(')')]
            if pline:
                # partition args: (<id>, [<delim>], [<*args>])
                pline = pline.partition(', ')  # pline convert to tuple

                # isolate _id
                _id = pline[0]

                # if arguments exist beyond _id
                pline = pline[2]
                if pline:
                    # check for *args or **kwargs
                    if pline[0] == '{' and pline[-1] == '}'\
                            and type(eval(pline)) is dict:
                        _args = pline
                    else:
                        _args = pline.replace(',', '')
                        # _args = _args.replace('\"', '')

            # if command is all or count
            if _cmd == HBNBCommand.dot_cmds[0] or \
                    _cmd == HBNBCommand.dot_cmds[1]:
                line = ' '.join([_cmd, _cls])
            # if command is show or destroy
            if _cmd == HBNBCommand.dot_cmds[2] or \
                    _cmd == HBNBCommand.dot_cmds[3]:
                line = ' '.join([_cmd, _cls, _id])
            # if command is update
            if _cmd == HBNBCommand.dot_cmds[4]:
                line = ' '.join([_cmd, _cls, _id, _args])

        except Exception as mess:
            pass
        finally:
            return line

    def postcmd(self, stop, line):
        """Prints if isatty is false"""
        if not sys.__stdin__.isatty():
            print('(hbnb) ', end='')
        return stop

    def do_quit(self, command):
        """ Method to exit the HBNB console"""
        exit(0)

    def help_quit(self):
        """ Prints the help documentation for quit  """
        print("Exits the program with formatting\n")

    def do_EOF(self, arg):
        """ Handles EOF to exit program """
        exit(0)

    def help_EOF(self):
        """ Prints the help documentation for EOF """
        print("Exits the program without formatting\n")

    def emptyline(self):
        """ Overrides the emptyline method of CMD """
        return False

    def do_create(self, args):
        """ Create an object of any class"""
        ignored_attrs = ('id', 'created_at', 'updated_at', '__class__')
        class_name = ''
        name_pattern = r'(?P<name>(?:[a-zA-Z]|_)(?:[a-zA-Z]|\d|_)*)'
        class_match = re.match(name_pattern, args)
        obj_kwargs = {}
        if class_match is not None:
            class_name = class_match.group('name')
            params_str = args[len(class_name):].strip()
            params = params_str.split(' ')
            str_pattern = r'(?P<t_str>("([^"]|\")*")|(\'([^\']|\\\')*\'))'
            float_pattern = r'(?P<t_float>[-+]?\d+\.\d+)'
            int_pattern = r'(?P<t_int>[-+]?\d+)'
            param_pattern = '{}=({}|{}|{})'.format(
                name_pattern,
                str_pattern,
                float_pattern,
                int_pattern
            )
            for param in params:
                param_match = re.fullmatch(param_pattern, param)
                if param_match is not None:
                    key_name = param_match.group('name')
                    str_v = param_match.group('t_str')
                    float_v = param_match.group('t_float')
                    int_v = param_match.group('t_int')
                    if float_v is not None:
                        obj_kwargs[key_name] = float(float_v)
                    if int_v is not None:
                        obj_kwargs[key_name] = int(int_v)
                    if str_v is not None:
                        if '_' in str_v:
                            obj_kwargs[key_name] = \
                                str_v[1:-1].replace('_', ' ')
                        elif '\\"' or "\\'" in str_v:
                            obj_kwargs[key_name] = \
                                str_v[1:-1].replace('\\', '')
                        else:
                            obj_kwargs[key_name] = str_v[1:-1]
        else:
            class_name = args
        if not class_name:
            print("** class name missing **")
            return
        elif class_name not in HBNBCommand.classes:
            print("** class doesn't exist **")
            return
        if os.getenv('HBNB_TYPE_STORAGE') == 'db':
            if not hasattr(obj_kwargs, 'id'):
                obj_kwargs['id'] = str(uuid.uuid4())
            if not hasattr(obj_kwargs, 'created_at'):
                obj_kwargs['created_at'] = str(datetime.now())
            if not hasattr(obj_kwargs, 'updated_at'):
                obj_kwargs['updated_at'] = str(datetime.now())
            new_instance = HBNBCommand.classes[class_name](**obj_kwargs)
            new_instance.save()
            print(new_instance.id)
        else:
            new_instance = HBNBCommand.classes[class_name]()
            for key, value in obj_kwargs.items():
                if key not in ignored_attrs:
                    setattr(new_instance, key, value)
            new_instance.save()
            print(new_instance.id)

    def help_create(self):
        """ Help information for the create method """
        print("Creates a class of any type (with or without parameters)")
        print("(*) means required")
        print('[Usage]: create <class_name>* <param_name>="<param_value>"\n')

    def do_show(self, args):
        """ Method to show an individual object """
        new = args.partition(" ")
        c_name = new[0]
        c_id = new[2]

        # guard against trailing args
        if c_id and ' ' in c_id:
            c_id = c_id.partition(' ')[0]

        if not c_name:
            print("** class name missing **")
            return

        if c_name not in HBNBCommand.classes:
            print("** class doesn't exist **")
            return

        if not c_id:
            print("** instance id missing **")
            return

        key = c_name + "." + c_id
        try:
            print(storage.all()[key])
        except KeyError:
            print("** no instance found **")

    def help_show(self):
        """ Help information for the show command """
        print("Shows an individual instance of a class")
        print("(*) means required")
        print("[Usage]: show <class_name>* <class_instance_id>*\n")

    def do_destroy(self, args):
        """ Destroys a specified object """
        new = args.partition(" ")
        c_name = new[0]
        c_id = new[2]
        if c_id and ' ' in c_id:
            c_id = c_id.partition(' ')[0]

        if not c_name:
            print("** class name missing **")
            return

        if c_name not in HBNBCommand.classes:
            print("** class doesn't exist **")
            return

        if not c_id:
            print("** instance id missing **")
            return

        key = c_name + "." + c_id

        try:
            storage.delete(storage.all()[key])
            storage.save()
        except KeyError:
            print("** no instance found **")

    def help_destroy(self):
        """ Help information for the destroy command """
        print("Destroys an individual instance of a class")
        print("(*) means required")
        print("[Usage]: destroy <class_name>* <class_instance_id>*\n")

    def do_all(self, args):
        """ Shows all objects, or all objects of a class"""
        class_objects = []
        if args:
            args = args.split(' ')[0]  # remove possible trailing args
            if args not in HBNBCommand.classes:
                print("** class doesn't exist **")
                return
            for k, v in storage.all().items():
                if args == k.split('.')[0]:
                    class_objects.append(str(v))
        else:
            for k, v in storage.all().items():
                class_objects.append(str(v))

        if class_objects == []:
            print("** no instance found **")
        else:
            print(class_objects)

    def help_all(self):
        """ Help information for the all command """
        print("Shows all instances or all the instances of \
              an individual class")
        print("(*) means required")
        print("[Usage]: all <class_name>\n")

    def do_count(self, args):
        """Count current number of class instances"""
        # isolate class_name from args
        c_name = args.partition(" ")[0]
        if not c_name:
            print("** class name missing **")
            return
        if c_name not in HBNBCommand.classes:
            print("** class doesn't exist **")
            return

        count = 0
        for k, v in storage.all().items():
            if c_name == k.split('.')[0]:
                count += 1
        print(count)

    def help_count(self):
        """ Help information for the count command """
        print("Shows the number of instances of an individual class")
        print("(*) means required")
        print("Usage: count <class_name>*")

    def do_update(self, args):
        """ Updates a certain object with new info """
        c_name = c_id = param_name = param_val = kwargs = ''

        # isolate cls from id/args, ex: (<cls>, delim, <id/args>)
        args = args.partition(" ")
        if args[0]:
            c_name = args[0]
        else:  # class name not present
            print("** class name missing **")
            return
        if c_name not in HBNBCommand.classes:  # class name invalid
            print("** class doesn't exist **")
            return

        # isolate id from args
        args = args[2].partition(" ")
        if args[0]:
            c_id = args[0]
        else:  # id not present
            print("** instance id missing **")
            return

        # generate key from class and id
        key = c_name + "." + c_id

        # determine if key is present
        if key not in storage.all():
            print("** no instance found **")
            return

        # first determine if kwargs or args
        if '{' in args[2] and '}' in args[2] and type(eval(args[2])) is dict:
            kwargs = eval(args[2])
            args = []  # reformat kwargs into list, ex: [<name>, <value>, ...]
            for k, v in kwargs.items():
                args.append(k)
                args.append(v)
        else:  # isolate param args
            args = args[2].partition(" ")
            # check for any relevant arg
            if args[0]:
                # check for arg_checks in args
                arg_checks = ["''", '""', "'", '"', "' ' '", '" " "']
                if args[0] not in arg_checks:
                    # check for double quoted param_name arg
                    if args and args[0][0] == '"':
                        second_quote = args[0].find('"', 1)
                        param_name = args[0][1:second_quote]
                    # check for single quoted param_name arg
                    elif args and args[0][0] == "'":
                        second_quote = args[0].find("'", 1)
                        param_name = args[0][1:second_quote]
                    # check for param_name arg without quote
                    if not param_name and args[0] != " ":
                        param_name = args[0]
                else:
                    print("** parameter name missing **")
                    return

                # check for arg_checks in args
                if args[2] and args[2] not in arg_checks:
                    # check for double quoted param_val arg
                    if args and args[2][0] == '"':
                        second_quote = args[2].find('"', 1)
                        param_val = args[2][1:second_quote]
                    # check for single quoted param_val arg
                    elif args and args[2][0] == "'":
                        second_quote = args[2].find("'", 1)
                        param_val = args[2][1:second_quote]
                    # check for param_val arg without quote
                    if not param_val and args[2] != " ":
                        param_val = args[2].partition(" ")[0]
                else:
                    print("** parameter value missing **")
                    return
            else:
                print("** parameter name and value missing **")
                return

            args = [param_name, param_val]

        # retrieve dictionary of current objects
        new_dict = storage.all()[key]

        # iterate through attr names and values
        for index, param_name in enumerate(args):
            # block only runs on even iterations
            if (index % 2 == 0):
                param_val = args[index + 1]  # following item is value
                # type cast as necessary
                if param_name in HBNBCommand.types:
                    param_val = HBNBCommand.types[param_name](param_val)

                # update dictionary with name, value pair
                new_dict.__dict__.update({param_name: param_val})

        new_dict.save()  # save updates to file

    def help_update(self):
        """ Help information for the update class """
        print("Updates a parameter of an instance with new information")
        print("(*) means required")
        print("Usage: update <class_name>* <instance_id>* \
              (<param_name>* <param_value> or <dict_param>)*\n")


if __name__ == "__main__":
    HBNBCommand().cmdloop()
