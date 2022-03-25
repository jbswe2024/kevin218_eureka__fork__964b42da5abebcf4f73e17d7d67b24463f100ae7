
import numpy as np
import os

"""
    This class loads a Eureka! Parameter File (epf) and lets you
    query the parameters and values.

    Modification History:
    --------------------
    2022-03-24 taylor     Made based on readECF with significant edits for Eureka
                          by Taylor J Bell          bell@baeri.org

"""

class EPF:
    def __init__(self, folder=None, file=None):
        # load all parameters
        if folder is not None and file is not None and os.path.isfile(os.path.join(folder, file)):
            self.read(folder, file)
            self.params = {}
            for line in self.cleanlines:
                par = np.array(line.split())
                name = par[0]
                vals = []
                for i in range(len(par[1:])):
                    try:
                        vals.append(eval(par[i+1]))
                    except:
                        vals.append(par[i+1])
                self.params[name] = vals

    def __str__(self):
        output = ''
        for line in self.cleanlines:
            output += line+'\n'
        return output[:-1]

    def __repr__(self):
        output = type(self).__module__+'.'+type(self).__qualname__+'('
        output += f"folder='{self.folder}', file='{self.filename}')\n"
        output += str(self)
        return output

    def read(self, folder, file):
        """
        Function to read the file:
        """
        self.filename = file
        self.folder = folder
        # Read the file
        with open(os.path.join(folder, file), 'r') as file:
            self.lines = file.readlines()

        self.cleanlines = []   # list with only the important lines
        # Clean the lines:
        for line in self.lines:
            # Strip off comments:
            if "#" in line:
                line = line[0:line.index('#')]
            line = line.strip()

            line = ' '.join(line.split())

            # Keep only useful lines:
            if len(line) > 0:
                self.cleanlines.append(line)

        return

    def write(self, folder):
        with open(os.path.join(folder, self.filename), 'w') as file:
            file.writelines(self.lines)
        return

class Parameter:
    """A generic parameter class"""
    def __init__(self, name, value, ptype, mn=None, mx=None, prior=None):
        """Instantiate a Parameter with a name and value at least

        Parameters
        ----------
        name: str
            The name of the parameter
        value: float, int, str, list, tuple
            The value of the parameter
        ptype: str
            The parameter type from ['free','fixed','independent','shared']
        mn: float, int, str, list, tuple (optioal)
            The first prior input value: lower-bound for uniform/log uniform priors, or mean for normal priors.
        mx: float, int, str, list, tuple (optioal)
            The second prior input value: upper-bound for uniform/log uniform priors, or std. dev. for normal priors.
        prior: str
            Type of prior, ['U','LU','N']
        """
        # If value is a list, distribute the elements
        if isinstance(value, list):
            value, *other = value
            if len(other) > 1:
                ptype, *other = other
            if len(other) > 0:
                mn, mx = other

        # Set the attributes
        self.name = name
        self.value = value
        self.mn = mn
        self.mx = mx
        self.ptype = ptype
        self.prior = prior

    def __str__(self):
        return str(self.values)

    def __repr__(self):
        output = type(self).__module__+'.'+type(self).__qualname__+'('
        keys = ['name', 'value', 'ptype', 'mn', 'mx', 'prior']
        for name in keys:
            val = getattr(self, name)
            if isinstance(val, str):
                val = "'"+val+"'"
            else:
                val = str(val)
            output += name+'='+val+', '
        output = output[:-2]+')'
        return output

    @property
    def ptype(self):
        """Getter for the ptype"""
        return self._ptype

    @ptype.setter
    def ptype(self, param_type):
        """Setter for ptype

        Parameters
        ----------
        param_type: str
            Parameter type, ['free','fixed','independent','shared']
        """
        if param_type in [True, False]:
            raise ValueError("Boolean ptype values are deprecated. ptype must now be 'free', 'fixed', 'independent', or 'shared'")
        elif param_type not in ['free', 'fixed', 'independent', 'shared']:
            raise ValueError("ptype must be 'free', 'fixed', 'independent', or 'shared'")

        self._ptype = param_type

    @property
    def values(self):
        """Return all values for this parameter"""
        vals = self.name, self.value, self.ptype, self.mn, self.mx, self.prior

        return list(filter(lambda x: x is not None, vals))


class Parameters:
    """A class to hold the Parameter instances
    """
    def __init__(self, param_path='./', param_file=None, **kwargs):
        """Initialize the parameter object

        Parameters
        ----------
        param_file: str
            A text file of the parameters to parse
        """

        # Make an empty params dict
        self.params = {}
        self.dict = {}

        # If a param_file is given, make sure it exists
        if param_file is not None and param_path is not None and os.path.exists(os.path.join(param_path,param_file)):

            # Parse the file
            if param_file.endswith('.txt') or param_file.endswith('.json'):
                raise AssertionError('ERROR: S5 parameter files in txt or json file formats have been deprecated.\n'+
                                     'Please change to using EPF (Eureka! Parameter File) file formats.')
            elif param_file.endswith('.ecf'):
                print('WARNING, using ECF file formats for S5 parameter files has been deprecated.')
                print('Please update the file format to an EPF (Eureka! Parameter File; .epf).')

            self.epf = EPF(param_path, param_file)
            self.params = self.epf.params

        # Add any kwargs to the parameter dict
        self.params.update(kwargs)
        
        # Try to store each as an attribute
        for param, value in self.params.items():
            setattr(self, param, value)

    def __str__(self):
        output = ''
        for key in self.params:
            output += key+': '+str(getattr(self, key))+'\n'
        return output[:-1]

    def __repr__(self):
        output = type(self).__module__+'.'+type(self).__qualname__+'('
        output += "param_path='./', param_file=None, "
        output += "**"+str(self.params)
        output = output+')'
        return output

    def __setattr__(self, item, value):
        """Maps attributes to values

        Parameters
        ----------
        item: str
            The name for the attribute
        value: any
            The attribute value
        """
        if item=='epf' or item=='params' or item=='dict':
            self.__dict__[item] = value
            return

        if isinstance(value, (str, float, int, bool)):
            # Convert single items to list
            value = [value,]
        elif isinstance(value, tuple):
            # Convert tuple to list
            value = list(value)
        elif not isinstance(value, list):
            raise TypeError("Cannot set {}={}.".format(item, value))

        # Set the attribute
        self.__dict__[item] = Parameter(item, *value)

        # Add it to the list of parameters
        self.__dict__['dict'][item] = self.__dict__[item].values[1:]

        return
