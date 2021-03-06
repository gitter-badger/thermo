# -*- coding: utf-8 -*-
'''Chemical Engineering Design Library (ChEDL). Utilities for process modeling.
Copyright (C) 2016, Caleb Bell <Caleb.Andrew.Bell@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.'''

from __future__ import division
from math import log, exp
import numpy as np
from scipy.constants import R
from scipy.optimize import brenth
from scipy.misc import derivative
from scipy.integrate import quad
from scipy.interpolate import interp1d, interp2d
import matplotlib.pyplot as plt


def to_num(values):
    r'''Legacy function to turn a list of strings into either floats
    (if numeric), stripped strings (if not) or None if the string is empty.
    Accepts any numeric formatting the float function does.

    Parameters
    ----------
    values : list
        list of strings

    Returns
    -------
    values : list
        list of floats, strings, and None values [-]

    Examples
    --------
    >>> to_num(['1', '1.1', '1E5', '0xB4', ''])
    [1.0, 1.1, 100000.0, '0xB4', None]
    '''
    for i in range(len(values)):
        try:
            values[i] = float(values[i])
        except:
            if values[i] == '':
                values[i] = None
            else:
                values[i] = values[i].strip()
                pass
    return values


def CAS2int(i):
    r'''Converts CAS number of a compounds from a string to an int. This is
    helpful when storing large amounts of CAS numbers, as their strings take up
    more memory than their numerical representational. All CAS numbers fit into
    64 bit ints.

    Parameters
    ----------
    CASRN : string
        CASRN [-]

    Returns
    -------
    CASRN : int
        CASRN [-]

    Notes
    -----
    Accomplishes conversion by removing dashes only, and then converting to an
    int. An incorrect CAS number will change without exception.

    Examples
    --------
    >>> CAS2int('7704-34-9')
    7704349
    '''
    return int(i.replace('-', ''))


def int2CAS(i):
    r'''Converts CAS number of a compounds from an int to an string. This is
    helpful when dealing with int CAS numbers.

    Parameters
    ----------
    CASRN : int
        CASRN [-]

    Returns
    -------
    CASRN : string
        CASRN [-]

    Notes
    -----
    Handles CAS numbers with an unspecified number of digits. Does not work on
    floats.

    Examples
    --------
    >>> int2CAS(7704349)
    '7704-34-9'
    '''
    i = str(i)
    return i[:-3]+'-'+i[-3:-1]+'-'+i[-1]




def Parachor(sigma, MW, rhol, rhog):
    '''Calculates a Chemical's Parachor according to DIPPR Method.

    >>> Parachor(0.02117, 114.22852, 700.03, 5.2609) # Octane; DIPPR: 350.6
    352.66655018657565
    '''
    rhol, rhog = rhol/1000., rhog/1000.
    sigma = sigma*1000
    P = sigma**0.25*MW/(rhol-rhog)
    return P


#def Parachor2(sigma, Vml, Vmg):
#    r'''Calculate Parachor for a pure species, using its molar volumes in
#    liquid and vapor form, and surface tension.
#
#    .. math::
#        P = \frac{ \sigma^{0.25} MW}{\rho_L - \rho_V}=\sigma^{0.25} (V_L - V_V)
#
#    Parameters
#    ----------
#    sigma : float
#        Surface tension, [N/m]
#    Vml : float
#        Liquid molar volume [m^3/mol]
#    Vmg : float
#        Gas molar volume [m^3/mol]
#
#    Returns
#    -------
#    P : float
#        Parachor, [-]
#
#    Notes
#    -----
#    Parachor is normally specified in units of [], in which molar volumes must
#    be converted to mL/mol, and surface tension in mN/m. Pure SI units are:
#
#    .. math::
#        \frac{\text{kg}^{0.25}\cdot\text{meter}^3}
#        {\text{mole}\cdot \text{second}^{0.5}}
#
#    The conversion to pure SI is to multiply by 1.77828e-7.
#
#    Examples
#    --------
#    Example 12.1 in [1]_.
#
#    >>> Parachor(sigma=0.02119, Vml=9.6525097e-05, Vmg=0)
#    207.09660808998868
#
#    References
#    ----------
#    .. [1] Poling, Bruce E. The Properties of Gases and Liquids. 5th edition.
#       New York: McGraw-Hill Professional, 2000.
#    '''
#    Vml, Vmg = Vml*1E6, Vmg*1E6
#    sigma = sigma*1000
#    P = sigma**0.25/(Vmg-Vml)
#    return P

#print([Parachor2(sigma=0.02119, Vml=9.6525097e-05, Vmg=0)])

def property_molar_to_mass(A_molar, MW):  # pragma: no cover
    if A_molar is None:
        return None
    A = A_molar*1000/MW
    return A


def property_mass_to_molar(A_mass, MW):  # pragma: no cover
    if A_mass is None:
        return None
    A_molar = A_mass*MW/1000
    return A_molar


def isobaric_expansion(V1=None, V2=None, dT=0.01):  # pragma: no cover
    if not (V1 and V2 and dT):
        return None
    V = (V1+V2)/2.
    beta = 1/V*(V2-V1)/dT
    return beta


def JT(T=None, V=None, Cp=None, isobaric_expansion=None):  # pragma: no cover
    if not (T and V and Cp and isobaric_expansion):
        return None
    _JT = V/Cp*(T*isobaric_expansion - 1.)
    return _JT


def isentropic_exponent(Cp, Cv):
    r'''Calculate the isentropic coefficient of a gas, given its constant-
    pressure and constant-volume heat capacity.

    .. math::
        k = \frac{C_p}{C_v}

    Parameters
    ----------
    Cp : float
        Gas heat capacity at constant pressure, [J/mol/K]
    Cv : float
        Gas heat capacity at constant volume, [J/mol/K]

    Returns
    -------
    k : float
        Isentropic exponent, [-]

    Examples
    --------
    >>> isentropic_exponent(33.6, 25.27)
    1.329639889196676

    References
    ----------
    .. [1] Poling, Bruce E. The Properties of Gases and Liquids. 5th edition.
       New York: McGraw-Hill Professional, 2000.
    '''
    return Cp/Cv


def Vm_to_rho(Vm, MW):
    r'''Calculate the density of a chemical, given its molar volume and
    molecular weight.

    .. math::
        \rho = \frac{MW}{1000\cdot VM}

    Parameters
    ----------
    Vm : float
        Molar volume, [m^3/mol]
    MW : float
        Molecular weight, [g/mol]

    Returns
    -------
    rho : float
        Density, [kg/m^3]

    Examples
    --------
    >>> Vm_to_rho(0.000132, 86.18)
    652.8787878787879

    References
    ----------
    .. [1] Poling, Bruce E. The Properties of Gases and Liquids. 5th edition.
       New York: McGraw-Hill Professional, 2000.
    '''
    return (Vm)**-1*MW/1000.


def rho_to_Vm(rho, MW):
    r'''Calculate the molar volume of a chemical, given its density and
    molecular weight.

    .. math::
        V_m = \left(\frac{1000 \rho}{MW}\right)^{-1}

    Parameters
    ----------
    rho : float
        Density, [kg/m^3]
    MW : float
        Molecular weight, [g/mol]

    Returns
    -------
    Vm : float
        Molar volume, [m^3/mol]

    Examples
    --------
    >>> rho_to_Vm(652.9, 86.18)
    0.00013199571144126206

    References
    ----------
    .. [1] Poling, Bruce E. The Properties of Gases and Liquids. 5th edition.
       New York: McGraw-Hill Professional, 2000.
    '''
    return (rho*1000./MW)**-1


def Z(T, P, V):
    r'''Calculates the compressibility factor of a gas, given its
    temperature, pressure, and molar volume.

    .. math::
        Z = \frac{PV}{RT}

    Parameters
    ----------
    T : float
        Temperature, [K]
    P : float
        Pressure [Pa]
    V : float
        Molar volume, [m^3/mol]

    Returns
    -------
    Z : float
        Compressibility factor, [-]

    Examples
    --------
    >>> Z(600, P=1E6, V=0.00463)
    0.9281019876560912

    References
    ----------
    .. [1] Poling, Bruce E. The Properties of Gases and Liquids. 5th edition.
       New York: McGraw-Hill Professional, 2000.
    '''
    _Z = V*P/T/R
    return _Z


def B_To_Z(B, T, P):
    r'''Calculates the compressibility factor of a gas, given its
    second virial coefficient.

    .. math::
        Z = 1 + \frac{BP}{RT}

    Parameters
    ----------
    B : float
        Second virial coefficient, [m^3/mol]
    T : float
        Temperature, [K]
    P : float
        Pressure [Pa]

    Returns
    -------
    Z : float
        Compressibility factor, [-]

    Notes
    -----
    Other forms of the virial coefficient exist.

    Examples
    --------
    >>> B_To_Z(-0.0015, 300, 1E5)
    0.9398638020957176

    References
    ----------
    .. [1] Poling, Bruce E. The Properties of Gases and Liquids. 5th edition.
       New York: McGraw-Hill Professional, 2000.
    '''
    return 1. + B*P/R/T


def B_from_Z(Z, T, P):
    r'''Calculates the second virial coefficient of a pure species, given the
    compressibility factor of the gas.

    .. math::
        B = \frac{RT(Z-1)}{P}

    Parameters
    ----------
    Z : float
        Compressibility factor, [-]
    T : float
        Temperature, [K]
    P : float
        Pressure [Pa]

    Returns
    -------
    B : float
        Second virial coefficient, [m^3/mol]

    Notes
    -----
    Other forms of the virial coefficient exist.

    Examples
    --------
    >>> B_from_Z(0.94, 300, 1E5)
    -0.0014966027640000014

    References
    ----------
    .. [1] Poling, Bruce E. The Properties of Gases and Liquids. 5th edition.
       New York: McGraw-Hill Professional, 2000.
    '''
    return (Z - 1)*R*T/P


def zs_to_ws(zs, MWs):
    r'''Converts a list of mole fractions to mass fractions. Requires molecular
    weights for all species.

    .. math::
        w_i = \frac{z_i MW_i}{MW_{avg}}

        MW_{avg} = \sum_i z_i MW_i

    Parameters
    ----------
    zs : iterable
        Mole fractions [-]
    MWs : iterable
        Molecular weights [g/mol]

    Returns
    -------
    ws : iterable
        Mass fractions [-]

    Notes
    -----
    Does not check that the sums add to one. Does not check that inputs are of
    the same length.

    Examples
    --------
    >>> zs_to_ws([0.5, 0.5], [10, 20])
    [0.3333333333333333, 0.6666666666666666]
    '''
    Mavg = sum(zi*MWi for zi, MWi in zip(zs, MWs))
    ws = [zi*MWi/Mavg for zi, MWi in zip(zs, MWs)]
    return ws


def ws_to_zs(ws, MWs):
    r'''Converts a list of mass fractions to mole fractions. Requires molecular
    weights for all species.

    .. math::
        z_i = \frac{\frac{w_i}{MW_i}}{\sum_i \frac{w_i}{MW_i}}

    Parameters
    ----------
    ws : iterable
        Mass fractions [-]
    MWs : iterable
        Molecular weights [g/mol]

    Returns
    -------
    zs : iterable
        Mole fractions [-]

    Notes
    -----
    Does not check that the sums add to one. Does not check that inputs are of
    the same length.

    Examples
    --------
    >>> ws_to_zs([0.3333333333333333, 0.6666666666666666], [10, 20])
    [0.5, 0.5]
    '''
    tot = sum(w/MW for w, MW in zip(ws, MWs))
    zs = [w/MW/tot for w, MW in zip(ws, MWs)]
    return zs


def zs_to_Vfs(zs, Vms):
    r'''Converts a list of mole fractions to volume fractions. Requires molar
    volumes for all species.

    .. math::
        \text{Vf}_i = \frac{z_i V_{m,i}}{\sum_i z_i V_{m,i}}

    Parameters
    ----------
    zs : iterable
        Mole fractions [-]
    VMs : iterable
        Molar volumes of species [m^3/mol]

    Returns
    -------
    Vfs : list
        Molar volume fractions [-]

    Notes
    -----
    Does not check that the sums add to one. Does not check that inputs are of
    the same length.

    Molar volumes are specified in terms of pure components only. Function
    works with any phase.

    Examples
    --------
    Acetone and benzene example

    >>> zs_to_Vfs([0.637, 0.363], [8.0234e-05, 9.543e-05])
    [0.5960229712956298, 0.4039770287043703]
    '''
    vol_is = [zi*Vmi for zi, Vmi in zip(zs, Vms)]
    tot = sum(vol_is)
    return [vol_i/tot for vol_i in vol_is]


def Vfs_to_zs(Vfs, Vms):
    r'''Converts a list of mass fractions to mole fractions. Requires molecular
    weights for all species.

    .. math::
        z_i = \frac{\frac{\text{Vf}_i}{V_{m,i}}}{\sum_i
        \frac{\text{Vf}_i}{V_{m,i}}}

    Parameters
    ----------
    Vfs : iterable
        Molar volume fractions [-]
    VMs : iterable
        Molar volumes of species [m^3/mol]

    Returns
    -------
    zs : list
        Mole fractions [-]

    Notes
    -----
    Does not check that the sums add to one. Does not check that inputs are of
    the same length.

    Molar volumes are specified in terms of pure components only. Function
    works with any phase.

    Examples
    --------
    Acetone and benzene example

    >>> Vfs_to_zs([0.596, 0.404], [8.0234e-05, 9.543e-05])
    [0.6369779395901142, 0.3630220604098858]
    '''
    mols_i = [Vfi/Vmi for Vfi, Vmi in zip(Vfs, Vms)]
    mols = sum(mols_i)
    return [mol_i/mols for mol_i in mols_i]


def none_and_length_check(all_inputs, length=None):
    r'''Checks inputs for suitability of use by a mixing rule which requires
    all inputs to be of the same length and non-None. A number of variations
    were attempted for this function; this was found to be the quickest.

    Parameters
    ----------
    all_inputs : array-like of array-like
        list of all the lists of inputs, [-]
    length : int, optional
        Length of the desired inputs, [-]

    Returns
    -------
    False/True : bool
        Returns True only if all inputs are the same length (or length `length`)
        and none of the inputs contain None [-]

    Notes
    -----
    Does not check for nan values.

    Examples
    --------
    >>> none_and_length_check(([1, 1], [1, 1], [1, 30], [10,0]), length=2)
    True
    '''
    if not length:
        length = len(all_inputs[0])
    for things in all_inputs:
        if None in things or len(things) != length:
            return False
    return True


def normalize(values):
    r'''Simple function which normalizes a series of values to be from 0 to 1,
    and for their sum to add to 1.

    .. math::
        x = \frac{x}{sum_i x_i}

    Parameters
    ----------
    values : array-like
        array of values

    Returns
    -------
    fractions : array-like
        Array of values from 0 to 1

    Notes
    -----
    Does not work on negative values.

    Examples
    --------
    >>> normalize([3, 2, 1])
    [0.5, 0.3333333333333333, 0.16666666666666666]
    '''
    tot = sum(values)
    return [i/tot for i in values]


def mixing_simple(fracs, props):
    r'''Simple function calculates a property based on weighted averages of
    properties. Weights could be mole fractions, volume fractions, mass
    fractions, or anything else.

    .. math::
        y = \sum_i \text{frac}_i \cdot \text{prop}_i

    Parameters
    ----------
    fracs : array-like
        Fractions of a mixture
    props: array-like
        Properties

    Returns
    -------
    prop : value
        Calculated property

    Notes
    -----
    Returns None if any fractions or properties are missing or are not of the
    same length.

    Examples
    --------
    >>> mixing_simple([0.1, 0.9], [0.01, 0.02])
    0.019
    '''
    if not none_and_length_check([fracs, props]):
        return None
    result = sum(frac*prop for frac, prop in zip(fracs, props))
    return result


def mixing_logarithmic(fracs, props):
    r'''Simple function calculates a property based on weighted averages of
    logarithmic properties.

    .. math::
        y = \sum_i \text{frac}_i \cdot \log(\text{prop}_i)

    Parameters
    ----------
    fracs : array-like
        Fractions of a mixture
    props: array-like
        Properties

    Returns
    -------
    prop : value
        Calculated property

    Notes
    -----
    Does not work on negative values.
    Returns None if any fractions or properties are missing or are not of the
    same length.

    Examples
    --------
    >>> mixing_logarithmic([0.1, 0.9], [0.01, 0.02])
    0.01866065983073615
    '''
    if not none_and_length_check([fracs, props]):
        return None
    return exp(sum(frac*log(prop) for frac, prop in zip(fracs, props)))


def phase_set_property(phase=None, s=None, l=None, g=None, V_over_F=None):
    r'''Determines which phase's property should be set as a default, given
    the phase a chemical is, and the property values of various phases. For the
    case of liquid-gas phase, returns None. If the property is not available
    for the current phase, or if the current phase is not known, returns None.

    Parameters
    ----------
    phase : str
        One of {'s', 'l', 'g', 'two-phase'}
    s : float
        Solid-phase property
    l : float
        Liquid-phase property
    g : float
        Gas-phase property
    V_over_F : float
        Vapor phase fraction

    Returns
    -------
    prop : float
        The selected/calculated property for the relevant phase

    Notes
    -----
    Could calculate mole-fraction weighted properties for the two phase regime.
    Could also implement equilibria with solid phases.

    Examples
    --------
    >>> phase_set_property(phase='g', l=1560.14, g=3312.)
    3312.0
    '''
    if phase == 's':
        return s
    elif phase == 'l':
        return l
    elif phase == 'g':
        return g
    elif phase == 'two-phase':
        return None  #TODO: all two-phase properties?
    elif phase is None:
        return None
    else:
        raise Exception('Property not recognized')

#print phase_set_property(phase='l', l=1560.14, g=3312.)


TEST_METHOD_1 = 'Test method 1'
TEST_METHOD_2 = 'Test method 2'


class TDependentProperty(object):
    '''Class for calculating temperature-dependent chemical properties. Should load
    all data about a given chemical on creation. As data is often stored in pandas
    DataFrames, this means that creation is slow. However, the calculation of
    a property at a given temperature is very fast. As coefficients are stored
    in every instance, a user could alter them from those loaded by default.

    Designed to intelligently select which method to use at a given temperature,
    according to (1) selections made by the user specifying a list of ordered
    method preferences and (2) by using a default list of prefered methods.

    All methods should have defined criteria for determining if they are valid before
    calculation, i.e. a minimum and maximum temperature for coefficients to be
    valid. For constant property values used due to lack of
    temperature-dependent data, a short range is normally specified as valid.
    It is not assumed that any given method will succeed; for example many expressions are
    not mathematically valid past the critical point. If the method raises an
    exception, the next method is tried until either one method works or all
    the supposedly valid have been
    exhausted. Furthermore, all properties returned by the method are checked
    by a sanity function :obj:`test_property_validity`, which has sanity checks for
    all properties.

    Works nicely with tabular data, which is interpolated from if specified.
    Interpolation is cubic-spline based if 5 or more points are given, and
    linearly interpolated with if few points are given. Extrapolation is
    permitted if :obj:`tabular_extrapolation_permitted` is set to True.
    For both interpolation and
    extrapolation, a transform may be applied so that a property such as
    vapor pressure can be interpolated non-linearly. These are functions or
    lambda expressions which must be set for the variables :obj:`interpolation_T`,
    :obj:`interpolation_property`, and :obj:`interpolation_property_inv`.

    Attributes
    ----------
    name : str
        The name of the property being calculated
    units : str
        The units of the property
    method : str
        The method was which was last used successfully to calculate a property;
        set only after the first property calculation.
    forced : bool
        If True, only user specified methods will be considered; otherwise all
        methods will be considered if none of the user specified methods succeed
    interpolation_T : function
        A function or lambda expression to transform the temperatures of
        tabular data for interpolation; e.g. 'lambda self, T: 1./T'
    interpolation_property : function
        A function or lambda expression to transform tabular property values
        prior to interpolation; e.g. 'lambda self, P: log(P)'
    interpolation_property_inv : function
        A function or property expression to transform interpolated property
        values from the transform performed by `interpolation_property` back
        to their actual form, e.g.  'lambda self, P: exp(P)'
    tabular_extrapolation_permitted : bool
        Whether or not to allow extrapolation from tabulated data for a
        property
    Tmin : float
        Maximum temperature at which no method can calculate the property above;
        set based on rough rules for some methods. Used to solve for a
        particular property value, and as a default minimum for plotting. Often
        higher than where the property is theoretically higher, i.e. liquid
        density above the triple point, but this information may still be
        needed for liquid mixtures with elevated critical points.
    Tmax : float
        Minimum temperature at which no method can calculate the property under;
        set based on rough rules for some methods. Used to solve for a
        particular property value, and as a default minimum for plotting. Often
        lower than where the property is theoretically higher, i.e. liquid
        density beneath the triple point, but this information may still be
        needed for subcooled liquids or mixtures with depressed freezing points.
    property_min : float
        Lowest value expected for a property while still being valid;
        this is a criteria used by `test_method_validity`.
    property_max : float
        Highest value expected for a property while still being valid;
        this is a criteria used by `test_method_validity`.
    ranked_methods : list
        Constant list of ranked methods by default
    tabular_data : dict
        Stores all user-supplied property data for interpolation in format
        {name: (Ts, properties)}
    tabular_data_interpolators : dict
        Stores all interpolation objects, idexed by name and property
        transform methods with the format {(name, interpolation_T,
        interpolation_property, interpolation_property_inv):
        (extrapolator, spline)}
    sorted_valid_methods : list
        Sorted and valid methods stored from the last T_dependent_property
        call
    user_methods : list
        Sorted methods as specified by the user
    '''
    # Dummy properties
    name = 'Property name'
    units = 'Property units'
    tabular_extrapolation_permitted = True

    interpolation_T = None
    interpolation_property = None
    interpolation_property_inv = None

    method = None
    forced = False

    property_min = 0
    property_max = 1E4  # Arbitrary max

#    Tmin = None
#    Tmax = None
    ranked_methods = []

    def set_user_methods(self, user_methods, forced=False):
        r'''Method used to select certain property methods as having a higher
        priority than were set by default. If `forced` is true, then methods
        which were not specified are excluded from consideration.

        As a side effect, `method` is removed to ensure than the new methods
        will be used in calculations afterwards.

        An exception is raised if any of the methods specified aren't available
        for the chemical. An exception is raised if no methods are provided.

        Parameters
        ----------
        user_methods : str or list
            Methods by name to be considered or prefered
        forced : bool, optional
            If True, only the user specified methods will ever be considered;
            if False other methods will be considered if no user methods
            suceed
        '''
        # Accept either a string or a list of methods, and whether
        # or not to only consider the false methods
        if isinstance(user_methods, str):
            user_methods = [user_methods]

        # The user's order matters and is retained for use by select_valid_methods
        self.user_methods = user_methods
        self.forced = forced

        # Validate that the user's specified methods are actual methods
        if set(self.user_methods).difference(self.all_methods):
            raise Exception("One of the given methods is not available for this chemical")
        if not self.user_methods and self.forced:
            raise Exception('Only user specified methods are considered when forced is True, but no methods were provided')

        # Remove previously selected methods
        self.method = None
        self.sorted_valid_methods = []

    def select_valid_methods(self, T):
        r'''Method to obtain a sorted list methods which are valid at `T`
        according to `test_method_validity`. Considers either only user methods
        if forced is True, or all methods. User methods are first tested
        according to their listed order, and unless forced is True, then all
        methods are tested and sorted by their order in `ranked_methods`.

        Parameters
        ----------
        T : float
            Temperature at which to test methods, [K]

        Returns
        -------
        sorted_valid_methods : list
            Sorted lists of methods valid at T according to
            `test_method_validity`
        '''
        # Consider either only the user's methods or all methods
        # Tabular data will be in both when inserted
        if self.forced:
            considered_methods = list(self.user_methods)
        else:
            considered_methods = list(self.all_methods)

        # User methods (incl. tabular data); add back later, after ranking the rest
        if self.user_methods:
            [considered_methods.remove(i) for i in self.user_methods]

        # Index the rest of the methods by ranked_methods, and add them to a list, sorted_methods
        preferences = sorted([self.ranked_methods.index(i) for i in considered_methods])
        sorted_methods = [self.ranked_methods[i] for i in preferences]

        # Add back the user's methods to the top, in order.
        if self.user_methods:
            [sorted_methods.insert(0, i) for i in reversed(self.user_methods)]

        sorted_valid_methods = []
        for method in sorted_methods:
            if self.test_method_validity(T, method):
                sorted_valid_methods.append(method)

        return sorted_valid_methods

    @classmethod
    def test_property_validity(self, prop):
        r'''Method to test the validity of a calculated property. Normally,
        this method is used by a given property class, and has maximum and
        minimum limits controlled by the variables `property_min` and
        `property_max`.

        Parameters
        ----------
        prop : float
            property to be tested, [`units`]

        Returns
        -------
        validity : bool
            Whether or not a specifid method is valid
        '''
        if isinstance(prop, complex):
            return False
        elif prop < self.property_min:
            return False
        elif prop > self.property_max:
            return False
        return True

    def T_dependent_property(self, T):
        r'''Method to calculate the property with sanity checking and without
        specifying a specific method. `select_valid_methods` is used to obtain
        a sorted list of methods to try. Methods are then tried in order until
        one succeeds. The methods are allowed to fail, and their results are
        checked with `test_property_validity`. On success, the used method
        is stored in the variable `method`.

        If `method` is set, this method is first checked for validity with
        `test_method_validity` for the specified temperature, and if it is
        valid, it is then used to calculate the property. The result is checked
        for validity, and returned if it is valid. If either of th checks fail,
        the function retrieves a full list of valid methods with
        `select_valid_methods` and attempts them as described above.

        If no methods are found which succeed, returns None.

        Parameters
        ----------
        T : float
            Temperature at which to calculate the property, [K]

        Returns
        -------
        prop : float
            Calculated property, [`units`]
        '''
        # Optimistic track, with the already set method
        if self.method:
            # retest within range
            if self.test_method_validity(T, self.method):
                try:
                    prop = self.calculate(T, self.method)
                    if self.test_property_validity(prop):
                        return prop
                except:  # pragma: no cover
                    pass

        # get valid methods at T, and try them until one yields a valid
        # property; store the method and return the answer
        self.sorted_valid_methods = self.select_valid_methods(T)
        for method in self.sorted_valid_methods:
            try:
                prop = self.calculate(T, method)
                if self.test_property_validity(prop):
                    self.method = method
                    return prop
            except:  # pragma: no cover
                pass

        # Function returns None if it does not work.
        return None

#    def plot(self, Tmin=None, Tmax=None, methods=[], pts=50, only_valid=True, order=0): # pragma: no cover
#            return self.plot_T_dependent_property(Tmin=Tmin, Tmax=Tmax, methods=methods, pts=pts, only_valid=only_valid, order=order)

    def plot_T_dependent_property(self, Tmin=None, Tmax=None, methods=[],
                                  pts=50, only_valid=True, order=0):  # pragma: no cover
        r'''Method to create a plot of the property vs temperature according to
        either a specified list of methods, or user methods (if set), or all
        methods. User-selectable number of points, and temperature range. If
        only_valid is set,`test_method_validity` will be used to check if each
        temperature in the specified range is valid, and
        `test_property_validity` will be used to test the answer, and the
        method is allowed to fail; only the valid points will be plotted.
        Otherwise, the result will be calculated and displayed as-is. This will
        not suceed if the method fails.

        Parameters
        ----------
        Tmin : float
            Minimum temperature, to begin calculating the property, [K]
        Tmax : float
            Maximum temperature, to stop calculating the property, [K]
        methods : list, optional
            List of methods to consider
        pts : int, optional
            A list of points to calculate the property at; if Tmin to Tmax
            covers a wide range of method validities, only a few points may end
            up calculated for a given method so this may need to be large
        only_valid : bool
            If True, only plot successful methods and calculated properties,
            and handle errors; if False, attempt calculation without any
            checking and use methods outside their bounds
        '''
        # This function cannot be tested
        if Tmin is None:
            if self.Tmin is not None:
                Tmin = self.Tmin
            else:
                raise Exception('Minimum temperature could not be auto-detected; please provide it')
        if Tmax is None:
            if self.Tmax is not None:
                Tmax = self.Tmax
            else:
                raise Exception('Maximum temperature could not be auto-detected; please provide it')

        if not methods:
            if self.user_methods:
                methods = self.user_methods
            else:
                methods = self.all_methods
        Ts = np.linspace(Tmin, Tmax, pts)
        if order == 0:
            for method in methods:
                if only_valid:
                    properties, Ts2 = [], []
                    for T in Ts:
                        if self.test_method_validity(T, method):
                            try:
                                p = self.calculate(T=T, method=method)
                                if self.test_property_validity(p):
                                    properties.append(p)
                                    Ts2.append(T)
                            except:
                                pass
                    plt.plot(Ts2, properties, label=method)
                else:
                    properties = [self.calculate(T=T, method=method) for T in Ts]
                    plt.plot(Ts, properties, label=method)
            plt.ylabel(self.name + ', ' + self.units)
            plt.title(self.name + ' of ' + self.CASRN)
        elif order > 0:
            for method in methods:
                if only_valid:
                    properties, Ts2 = [], []
                    for T in Ts:
                        if self.test_method_validity(T, method):
                            try:
                                p = self.calculate_derivative(T=T, method=method, order=order)
                                properties.append(p)
                                Ts2.append(T)
                            except:
                                pass
                    plt.plot(Ts2, properties, label=method)
                else:
                    properties = [self.calculate_derivative(T=T, method=method, order=order) for T in Ts]
                    plt.plot(Ts, properties, label=method)
            plt.ylabel(self.name + ', ' + self.units + '/K^%d derivative of order %d' % (order, order))
            plt.title(self.name + ' derivative of order %d' % order + ' of ' + self.CASRN)
        plt.legend()
        plt.xlabel('Temperature, K')
        plt.show()

    def interpolate(self, T, name):
        r'''Method to perform interpolation on a given tabular data set
        previously added via :obj:`set_tabular_data`. This method will create the
        interpolators the first time it is used on a property set, and store
        them for quick future use.

        Interpolation is cubic-spline based if 5 or more points are available,
        and linearly interpolated if not. Extrapolation is always performed
        linearly. This function uses the transforms `interpolation_T`,
        `interpolation_property`, and `interpolation_property_inv` if set. If
        any of these are changed after the interpolators were first created,
        new interpolators are created with the new transforms.
        All interpolation is performed via the `interp1d` function.

        Parameters
        ----------
        T : float
            Temperature at which to interpolate the property, [K]
        name : str
            The name assigned to the tabular data set

        Returns
        -------
        prop : float
            Calculated property, [`units`]
        '''
        key = (name, self.interpolation_T, self.interpolation_property, self.interpolation_property_inv)

        # If the interpolator and extrapolator has already been created, load it
#        if isinstance(self.tabular_data_interpolators, dict) and key in self.tabular_data_interpolators:
#            extrapolator, spline = self.tabular_data_interpolators[key]

        if key in self.tabular_data_interpolators:
            extrapolator, spline = self.tabular_data_interpolators[key]
        else:
            Ts, properties = self.tabular_data[name]

            if self.interpolation_T:  # Transform ths Ts with interpolation_T if set
                Ts2 = [self.interpolation_T(T2) for T2 in Ts]
            else:
                Ts2 = Ts
            if self.interpolation_property:  # Transform ths props with interpolation_property if set
                properties2 = [self.interpolation_property(p) for p in properties]
            else:
                properties2 = properties
            # Only allow linear extrapolation, but with whatever transforms are specified
            extrapolator = interp1d(Ts2, properties2, fill_value='extrapolate')
            # If more than 5 property points, create a spline interpolation
            if len(properties) >= 5:
                spline = interp1d(Ts2, properties2, kind='cubic')
            else:
                spline = None
#            if isinstance(self.tabular_data_interpolators, dict):
#                self.tabular_data_interpolators[key] = (extrapolator, spline)
#            else:
#                self.tabular_data_interpolators = {key: (extrapolator, spline)}
            self.tabular_data_interpolators[key] = (extrapolator, spline)

        # Load the stores values, tor checking which interpolation strategy to
        # use.
        Ts, properties = self.tabular_data[name]

        if T < Ts[0] or T > Ts[-1] or not spline:
            tool = extrapolator
        else:
            tool = spline

        if self.interpolation_T:
            T = self.interpolation_T(T)
        prop = tool(T)  # either spline, or linear interpolation

        if self.interpolation_property:
            prop = self.interpolation_property_inv(prop)

        return float(prop)

    def set_tabular_data(self, Ts, properties, name=None, check_properties=True):
        r'''Method to set tabular data to be used for interpolation.
        Ts must be in increasing order. If no name is given, data will be
        assigned the name 'Tabular data series #x', where x is the number of
        previously added tabular data series. The name is added to all
        methods and iserted at the start of user methods,

        Parameters
        ----------
        Ts : array-like
            Increasing array of temperatures at which properties are specified, [K]
        properties : array-like
            List of properties at Ts, [`units`]
        name : str, optional
            Name assigned to the data
        check_properties : bool
            If True, the properties will be checked for validity with
            `test_property_validity` and raise an exception if any are not
            valid
        '''
        # Ts must be in increasing order.
        if check_properties:
            for p in properties:
                if not self.test_property_validity(p):
                    raise Exception('One of the properties specified are not feasible')
        if not all(b > a for a, b in zip(Ts, Ts[1:])):
            raise Exception('Temperatures are not sorted in increasing order')

        if name is None:
            name = 'Tabular data series #' + str(len(self.tabular_data))  # Will overwrite a poorly named series
        self.tabular_data[name] = (Ts, properties)

        self.method = None
        self.user_methods.insert(0, name)
        self.all_methods.add(name)

        self.set_user_methods(user_methods=self.user_methods, forced=self.forced)

    def solve_prop(self, goal, reset_method=True):
        r'''Method to solve for the temperature at which a property is at a
        specified value. `T_dependent_property` is used to calculate the value
        of the property as a function of temperature; if `reset_method` is True,
        the best method is used at each temperature as the solver seeks a
        solution. This slows the solution moderately.

        Checks the given property value with `test_property_validity` first
        and raises an exception if it is not valid. Requires that Tmin and
        Tmax have been set to know what range to search within.

        Search is performed with the brenth solver from SciPy.

        Parameters
        ----------
        goal : float
            Propoerty value desired, [`units`]
        reset_method : bool
            Whether or not to reset the method as the solver searches

        Returns
        -------
        T : float
            Temperature at which the property is the specified value [K]
        '''
        if self.Tmin is None or self.Tmax is None:
            raise Exception('Both a minimum and a maximum value are not present indicating there is not enough data for temperature dependency.')
        if not self.test_property_validity(goal):
            raise Exception('Input property is not considered plausible; no method would calculate it.')

        def error(T):
            if reset_method:
                self.method = None
            return self.T_dependent_property(T) - goal
        try:
            return brenth(error, self.Tmin, self.Tmax)
        except ValueError:
            raise Exception('To within the implemented temperature range, it is not possible to calculate the desired value.')

    def calculate_derivative(self, T, method, order=1):
        r'''Method to calculate a derivative of a property with respect to 
        temperature, of a given order  using a specified method. Uses SciPy's 
        derivative function, with a delta of 1E-6 K and a number of points 
        equal to 2*order + 1.

        This method can be overwritten by subclasses who may perfer to add
        analytical methods for some or all methods as this is much faster.

        If the calculation does not succeed, returns the actual error
        encountered .

        Parameters
        ----------
        T : float
            Temperature at which to calculate the derivative, [K]
        order : int
            Order of the derivative, > 1
        method : str
            Method for which to find the derivative

        Returns
        -------
        derivative : float
            Calculated derivative property, [`units/K^order`]
        '''
        return derivative(self.calculate, T, dx=1e-6, args=[method], n=order, order=1+order*2)

    def T_dependent_property_derivative(self, T, order=1):
        r'''Method to obtain a derivative of a property with respect to 
        temperature, of a given order. Methods found valid by 
        `select_valid_methods` are attempted until a method succeeds. If no 
        methods are valid and succeed, None is returned.

        Calls `calculate_derivative` internally to perform the actual
        calculation.
        
        .. math::
            \text{derivative} = \frac{d (\text{property})}{d T}

        Parameters
        ----------
        T : float
            Temperature at which to calculate the derivative, [K]
        order : int
            Order of the derivative, > 1

        Returns
        -------
        derivative : float
            Calculated derivative property, [`units/K^order`]
        '''
        sorted_valid_methods = self.select_valid_methods(T)
        for method in sorted_valid_methods:
            try:
                return self.calculate_derivative(T, method, order)
            except:
                pass
        return None


    def calculate_integral(self, T1, T2, method):
        r'''Method to calculate the integral of a property with respect to
        temperature, using a specified method. Uses SciPy's `quad` function
        to perform the integral, with no options.
        
        This method can be overwritten by subclasses who may perfer to add
        analytical methods for some or all methods as this is much faster.

        If the calculation does not succeed, returns the actual error
        encountered.

        Parameters
        ----------
        T1 : float
            Lower limit of integration, [K]
        T2 : float
            Upper limit of integration, [K]
        method : str
            Method for which to find the integral

        Returns
        -------
        integral : float
            Calculated integral of the property over the given range, 
            [`units*K`]
        '''
        return float(quad(self.calculate, T1, T2, args=(method))[0])

    def T_dependent_property_integral(self, T1, T2):
        r'''Method to calculate the integral of a property with respect to
        temperature, using a specified method. Methods found valid by 
        `select_valid_methods` are attempted until a method succeeds. If no 
        methods are valid and succeed, None is returned.
        
        Calls `calculate_integral` internally to perform the actual
        calculation.

        .. math::
            \text{integral} = \int_{T_1}^{T_2} \text{property} \; dT

        Parameters
        ----------
        T1 : float
            Lower limit of integration, [K]
        T2 : float
            Upper limit of integration, [K]
        method : str
            Method for which to find the integral

        Returns
        -------
        integral : float
            Calculated integral of the property over the given range, 
            [`units*K`]
        '''
        sorted_valid_methods = self.select_valid_methods(T1)
        for method in sorted_valid_methods:
            try:
                return self.calculate_integral(T1, T2, method)
            except:
                pass
        return None

    def calculate_integral_over_T(self, T1, T2, method):
        r'''Method to calculate the integral of a property over temperature
        with respect to temperature, using a specified method. Uses SciPy's 
        `quad` function to perform the integral, with no options.
        
        This method can be overwritten by subclasses who may perfer to add
        analytical methods for some or all methods as this is much faster.

        If the calculation does not succeed, returns the actual error
        encountered.

        Parameters
        ----------
        T1 : float
            Lower limit of integration, [K]
        T2 : float
            Upper limit of integration, [K]
        method : str
            Method for which to find the integral

        Returns
        -------
        integral : float
            Calculated integral of the property over the given range, 
            [`units`]
        '''
        return float(quad(lambda T: self.calculate(T, method)/T, T1, T2)[0])

    def T_dependent_property_integral_over_T(self, T1, T2):
        r'''Method to calculate the integral of a property over temperature 
        with respect to temperature, using a specified method. Methods found
        valid by `select_valid_methods` are attempted until a method succeeds. 
        If no methods are valid and succeed, None is returned.
        
        Calls `calculate_integral_over_T` internally to perform the actual
        calculation.
        
        .. math::
            \text{integral} = \int_{T_1}^{T_2} \frac{\text{property}}{T} \; dT

        Parameters
        ----------
        T1 : float
            Lower limit of integration, [K]
        T2 : float
            Upper limit of integration, [K]
        method : str
            Method for which to find the integral

        Returns
        -------
        integral : float
            Calculated integral of the property over the given range, 
            [`units`]
        '''
        sorted_valid_methods = self.select_valid_methods(T1)
        for method in sorted_valid_methods:
            try:
                return self.calculate_integral_over_T(T1, T2, method)
            except:
                pass
        return None


    # Dummy functions, always to be overwritten, only for testing

    def __init__(self, CASRN=''):
        '''Create an instance of TDependentProperty. Should be overwritten by
        a method created specific to a property. Should take all constant
        properties on creation.

        Attributes
        ----------
        '''
        self.CASRN = CASRN
        self.load_all_methods()

        self.ranked_methods = [TEST_METHOD_2, TEST_METHOD_1]  # Never changes
        self.tabular_data = {}
        self.tabular_data_interpolators = {}

        self.sorted_valid_methods = []
        self.user_methods = []

    def load_all_methods(self):
        r'''Method to load all data, and set all_methods based on the available
        data and properties. Demo function for testing only; must be
        implemented according to the methods available for each individual
        method.
        '''
        methods = []
        Tmins, Tmaxs = [], []
        if self.CASRN in ['7732-18-5', '67-56-1', '64-17-5']:
            methods.append(TEST_METHOD_1)
            self.TEST_METHOD_1_Tmin = 200.
            self.TEST_METHOD_1_Tmax = 350
            self.TEST_METHOD_1_coeffs = [1, .002]
            Tmins.append(self.TEST_METHOD_1_Tmin); Tmaxs.append(self.TEST_METHOD_1_Tmax)
        if self.CASRN in ['67-56-1']:
            methods.append(TEST_METHOD_2)
            self.TEST_METHOD_2_Tmin = 300.
            self.TEST_METHOD_2_Tmax = 400
            self.TEST_METHOD_2_coeffs = [1, .003]
            Tmins.append(self.TEST_METHOD_2_Tmin); Tmaxs.append(self.TEST_METHOD_2_Tmax)
        self.all_methods = set(methods)
        if Tmins and Tmaxs:
            self.Tmin = min(Tmins)
            self.Tmax = max(Tmaxs)

    def calculate(self, T, method):
        r'''Method to calculate a property with a specified method, with no
        validity checking or error handling. Demo function for testing only;
        must be implemented according to the methods available for each
        individual method. Include the interpolation call here.

        Parameters
        ----------
        T : float
            Temperature at which to calculate the property, [K]
        method : str
            Method name to use

        Returns
        -------
        prop : float
            Calculated property, [`units`]
        '''
        if method == TEST_METHOD_1:
            prop = self.TEST_METHOD_1_coeffs[0] + self.TEST_METHOD_1_coeffs[1]*T
        elif method == TEST_METHOD_2:
            prop = self.TEST_METHOD_2_coeffs[0] + self.TEST_METHOD_2_coeffs[1]*T
        elif method in self.tabular_data:
            prop = self.interpolate(T, method)
        return prop

    def test_method_validity(self, T, method):
        r'''Method to test the validity of a specified method for a given
        temperature. Demo function for testing only;
        must be implemented according to the methods available for each
        individual method. Include the interpolation check here.

        Parameters
        ----------
        T : float
            Temperature at which to determine the validity of the method, [K]
        method : str
            Method name to use

        Returns
        -------
        validity : bool
            Whether or not a specifid method is valid
        '''
        validity = True
        if method == TEST_METHOD_1:
            if T < self.TEST_METHOD_1_Tmin or T > self.TEST_METHOD_1_Tmax:
                validity = False
        elif method == TEST_METHOD_2:
            if T < self.TEST_METHOD_2_Tmin or T > self.TEST_METHOD_2_Tmax:
                validity = False
        elif method in self.tabular_data:
            # if tabular_extrapolation_permitted, good to go without checking
            if not self.tabular_extrapolation_permitted:
                Ts, properties = self.tabular_data[method]
                if T < Ts[0] or T > Ts[-1]:
                    validity = False
        else:
            raise Exception('Method not valid')
        return validity


class TPDependentProperty(TDependentProperty):
    '''Class for calculating temperature and pressure dependent chemical
    properties.'''
    interpolation_P = None
    method_P = None
    forced_P = False

    def set_user_methods_P(self, user_methods_P, forced_P=False):
        r'''Method to set the pressure-dependent property methods desired for
        consideration by the user. Can be used to exclude certain methods which
        might have unacceptable accuracy.

        As a side effect, the previously selected method is removed when
        this method is called to ensure user methods are tried in the desired
        order.

        Parameters
        ----------
        user_methods_P : str or list
            Methods by name to be considered or prefered for pressure effect
        forced : bool, optional
            If True, only the user specified methods will ever be considered;
            if False other methods will be considered if no user methods
            suceed
        '''
        # Accept either a string or a list of methods, and whether
        # or not to only consider the false methods
        if isinstance(user_methods_P, str):
            user_methods_P = [user_methods_P]

        # The user's order matters and is retained for use by select_valid_methods
        self.user_methods_P = user_methods_P
        self.forced_P = forced_P

        # Validate that the user's specified methods are actual methods
        if set(self.user_methods_P).difference(self.all_methods_P):
            raise Exception("One of the given methods is not available for this chemical")
        if not self.user_methods_P and self.forced:
            raise Exception('Only user specified methods are considered when forced is True, but no methods were provided')

        # Remove previously selected methods
        self.method_P = None
        self.sorted_valid_methods_P = []

    def select_valid_methods_P(self, T, P):
        r'''Method to obtain a sorted list methods which are valid at `T`
        according to `test_method_validity`. Considers either only user methods
        if forced is True, or all methods. User methods are first tested
        according to their listed order, and unless forced is True, then all
        methods are tested and sorted by their order in `ranked_methods`.

        Parameters
        ----------
        T : float
            Temperature at which to test methods, [K]
        P : float
            Pressure at which to test methods, [Pa]

        Returns
        -------
        sorted_valid_methods_P : list
            Sorted lists of methods valid at T and P according to
            `test_method_validity`
        '''
        # Same as select_valid_methods but with _P added to variables
        if self.forced_P:
            considered_methods = list(self.user_methods_P)
        else:
            considered_methods = list(self.all_methods_P)

        if self.user_methods_P:
            [considered_methods.remove(i) for i in self.user_methods_P]

        preferences = sorted([self.ranked_methods_P.index(i) for i in considered_methods])
        sorted_methods = [self.ranked_methods_P[i] for i in preferences]

        if self.user_methods_P:
            [sorted_methods.insert(0, i) for i in reversed(self.user_methods_P)]

        sorted_valid_methods_P = []
        for method in sorted_methods:
            if self.test_method_validity_P(T, P, method):
                sorted_valid_methods_P.append(method)

        return sorted_valid_methods_P

    def TP_dependent_property(self, T, P):
        r'''Method to calculate the property with sanity checking and without
        specifying a specific method. `select_valid_methods_P` is used to obtain
        a sorted list of methods to try. Methods are then tried in order until
        one succeeds. The methods are allowed to fail, and their results are
        checked with `test_property_validity`. On success, the used method
        is stored in the variable `method_P`.

        If `method_P` is set, this method is first checked for validity with
        `test_method_validity_P` for the specified temperature, and if it is
        valid, it is then used to calculate the property. The result is checked
        for validity, and returned if it is valid. If either of the checks fail,
        the function retrieves a full list of valid methods with
        `select_valid_methods_P` and attempts them as described above.

        If no methods are found which succeed, returns None.

        Parameters
        ----------
        T : float
            Temperature at which to calculate the property, [K]
        P : float
            Pressure at which to calculate the property, [Oa]

        Returns
        -------
        prop : float
            Calculated property, [`units`]
        '''
        # Optimistic track, with the already set method
        if self.method_P:
            # retest within range
            if self.test_method_validity_P(T, P, self.method_P):
                try:
                    prop = self.calculate_P(T, P, self.method_P)
                    if self.test_property_validity(prop):
                        return prop
                except:  # pragma: no cover
                    pass

        # get valid methods at T, and try them until one yields a valid
        # property; store the method_P and return the answer
        self.sorted_valid_methods_P = self.select_valid_methods_P(T, P)
        for method_P in self.sorted_valid_methods_P:
            try:
                prop = self.calculate_P(T, P, method_P)
                if self.test_property_validity(prop):
                    self.method_P = method_P
                    return prop
            except:  # pragma: no cover
                pass
        # Function returns None if it does not work.
        return None

    def set_tabular_data_P(self, Ts, Ps, properties, name=None, check_properties=True):
        r'''Method to set tabular data to be used for interpolation.
        Ts and Psmust be in increasing order. If no name is given, data will be
        assigned the name 'Tabular data series #x', where x is the number of
        previously added tabular data series. The name is added to all
        methods and is inserted at the start of user methods,

        Parameters
        ----------
        Ts : array-like
            Increasing array of temperatures at which properties are specified, [K]
        Ps : array-like
            Increasing array of pressures at which properties are specified, [Pa]
        properties : array-like
            List of properties at Ts, [`units`]
        name : str, optional
            Name assigned to the data
        check_properties : bool
            If True, the properties will be checked for validity with
            `test_property_validity` and raise an exception if any are not
            valid
        '''
        # Ts must be in increasing order.
        if check_properties:
            for p in np.array(properties).ravel():
                if not self.test_property_validity(p):
                    raise Exception('One of the properties specified are not feasible')
        if not all(b > a for a, b in zip(Ts, Ts[1:])):
            raise Exception('Temperatures are not sorted in increasing order')
        if not all(b > a for a, b in zip(Ps, Ps[1:])):
            raise Exception('Pressures are not sorted in increasing order')

        if name is None:
            name = 'Tabular data series #' + str(len(self.tabular_data))  # Will overwrite a poorly named series
        self.tabular_data[name] = (Ts, Ps, properties)

        self.method_P = None
        self.user_methods_P.insert(0, name)
        self.all_methods_P.add(name)

        self.set_user_methods_P(user_methods_P=self.user_methods_P, forced_P=self.forced_P)

    def interpolate_P(self, T, P, name):
        r'''Method to perform interpolation on a given tabular data set
        previously added via `set_tabular_data_P`. This method will create the
        interpolators the first time it is used on a property set, and store
        them for quick future use.

        Interpolation is cubic-spline based if 5 or more points are available,
        and linearly interpolated if not. Extrapolation is always performed
        linearly. This function uses the transforms `interpolation_T`,
        `interpolation_P`,
        `interpolation_property`, and `interpolation_property_inv` if set. If
        any of these are changed after the interpolators were first created,
        new interpolators are created with the new transforms.
        All interpolation is performed via the `interp2d` function.

        Parameters
        ----------
        T : float
            Temperature at which to interpolate the property, [K]
        T : float
            Pressure at which to interpolate the property, [Pa]
        name : str
            The name assigned to the tabular data set

        Returns
        -------
        prop : float
            Calculated property, [`units`]
        '''
        key = (name, self.interpolation_T, self.interpolation_P, self.interpolation_property, self.interpolation_property_inv)

        # If the interpolator and extrapolator has already been created, load it
        if key in self.tabular_data_interpolators:
            extrapolator, spline = self.tabular_data_interpolators[key]
        else:
            Ts, Ps, properties = self.tabular_data[name]

            if self.interpolation_T:  # Transform ths Ts with interpolation_T if set
                Ts2 = [self.interpolation_T(T2) for T2 in Ts]
            else:
                Ts2 = Ts
            if self.interpolation_P:  # Transform ths Ts with interpolation_T if set
                Ps2 = [self.interpolation_P(P2) for P2 in Ps]
            else:
                Ps2 = Ps
            if self.interpolation_property:  # Transform ths props with interpolation_property if set
                properties2 = [self.interpolation_property(p) for p in properties]
            else:
                properties2 = properties
            # Only allow linear extrapolation, but with whatever transforms are specified
            extrapolator = interp2d(Ts2, Ps2, properties2)  # interpolation if fill value is missing
            # If more than 5 property points, create a spline interpolation
            if len(properties) >= 5:
                spline = interp2d(Ts2, Ps2, properties2, kind='cubic')
            else:
                spline = None
            self.tabular_data_interpolators[key] = (extrapolator, spline)

        # Load the stores values, tor checking which interpolation strategy to
        # use.
        Ts, Ps, properties = self.tabular_data[name]

        if T < Ts[0] or T > Ts[-1] or not spline or P < Ps[0] or P > Ps[-1]:
            tool = extrapolator
        else:
            tool = spline

        if self.interpolation_T:
            T = self.interpolation_T(T)
        if self.interpolation_P:
            P = self.interpolation_T(P)
        prop = tool(T, P)  # either spline, or linear interpolation

        if self.interpolation_property:
            prop = self.interpolation_property_inv(prop)

        return float(prop)

    def plot_isotherm(self, T, Pmin=None, Pmax=None, methods_P=[], pts=50,
                      only_valid=True):  # pragma: no cover
        r'''Method to create a plot of the property vs pressure at a specified
        temperature according to either a specified list of methods, or the 
        user methods (if set), or all methods. User-selectable number of 
        points, and pressure range. If only_valid is set,
        `test_method_validity_P` will be used to check if each temperature in 
        the specified range is valid, and `test_property_validity` will be used
        to test the answer, and the method is allowed to fail; only the valid 
        points will be plotted. Otherwise, the result will be calculated and 
        displayed as-is. This will not suceed if the method fails.

        Parameters
        ----------
        Pmin : float
            Minimum pressure, to begin calculating the property, [Pa]
        Pmax : float
            Maximum pressure, to stop calculating the property, [Pa]
        methods : list, optional
            List of methods to consider
        pts : int, optional
            A list of points to calculate the property at; if Pmin to Pmax
            covers a wide range of method validities, only a few points may end
            up calculated for a given method so this may need to be large
        only_valid : bool
            If True, only plot successful methods and calculated properties,
            and handle errors; if False, attempt calculation without any
            checking and use methods outside their bounds
        '''
        # This function cannot be tested
        if Pmin is None:
            if self.Pmin is not None:
                Pmin = self.Pmin
            else:
                raise Exception('Minimum pressure could not be auto-detected; please provide it')
        if Pmax is None:
            if self.Pmax is not None:
                Pmax = self.Pmax
            else:
                raise Exception('Maximum pressure could not be auto-detected; please provide it')

        if not methods_P:
            if self.user_methods_P:
                methods_P = self.user_methods_P
            else:
                methods_P = self.all_methods_P
        Ps = np.linspace(Pmin, Pmax, pts)
        for method_P in methods_P:
            if only_valid:
                properties, Ps2 = [], []
                for P in Ps:
                    if self.test_method_validity_P(T, P, method_P):
                        try:
                            p = self.calculate_P(T, P, method_P)
                            if self.test_property_validity(p):
                                properties.append(p)
                                Ps2.append(P)
                        except:
                            pass
                plt.plot(Ps2, properties, label=method_P)
            else:
                properties = [self.calculate_P(T, P, method_P) for P in Ps]
                plt.plot(Ps, properties, label=method_P)
        plt.legend()
        plt.ylabel(self.name + ', ' + self.units)
        plt.xlabel('Pressure, Pa')
        plt.title(self.name + ' of ' + self.CASRN)
        plt.show()

    def plot_isobar(self, P, Tmin=None, Tmax=None, methods_P=[], pts=50,
                    only_valid=True):  # pragma: no cover
        r'''Method to create a plot of the property vs temperature at a 
        specific pressure according to
        either a specified list of methods, or user methods (if set), or all
        methods. User-selectable number of points, and temperature range. If
        only_valid is set,`test_method_validity_P` will be used to check if 
        each temperature in the specified range is valid, and
        `test_property_validity` will be used to test the answer, and the
        method is allowed to fail; only the valid points will be plotted.
        Otherwise, the result will be calculated and displayed as-is. This will
        not suceed if the method fails.

        Parameters
        ----------
        P : float
            Pressure for the isobar, [Pa]
        Tmin : float
            Minimum temperature, to begin calculating the property, [K]
        Tmax : float
            Maximum temperature, to stop calculating the property, [K]
        methods : list, optional
            List of methods to consider
        pts : int, optional
            A list of points to calculate the property at; if Tmin to Tmax
            covers a wide range of method validities, only a few points may end
            up calculated for a given method so this may need to be large
        only_valid : bool
            If True, only plot successful methods and calculated properties,
            and handle errors; if False, attempt calculation without any
            checking and use methods outside their bounds
        '''
        if Tmin is None:
            if self.Tmin is not None:
                Tmin = self.Tmin
            else:
                raise Exception('Minimum pressure could not be auto-detected; please provide it')
        if Tmax is None:
            if self.Tmax is not None:
                Tmax = self.Tmax
            else:
                raise Exception('Maximum pressure could not be auto-detected; please provide it')

        if not methods_P:
            if self.user_methods_P:
                methods_P = self.user_methods_P
            else:
                methods_P = self.all_methods_P
        Ts = np.linspace(Tmin, Tmax, pts)
        for method_P in methods_P:
            if only_valid:
                properties, Ts2 = [], []
                for T in Ts:
                    if self.test_method_validity_P(T, P, method_P):
                        try:
                            p = self.calculate_P(T, P, method_P)
                            if self.test_property_validity(p):
                                properties.append(p)
                                Ts2.append(T)
                        except:
                            pass
                plt.plot(Ts2, properties, label=method_P)
            else:
                properties = [self.calculate_P(T, P, method_P) for T in Ts]
                plt.plot(Ts, properties, label=method_P)
        plt.legend()
        plt.ylabel(self.name + ', ' + self.units)
        plt.xlabel('Temperature, K')
        plt.title(self.name + ' of ' + self.CASRN)
        plt.show()
