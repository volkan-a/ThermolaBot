import numpy as np
import matplotlib.pyplot as plt
import matplotlib.pylab as p
import logging
from os import remove
import re

from telegram.update import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.ext.callbackcontext import CallbackContext

import CoolProp as CP
from pint import UnitRegistry


import matplotlib
matplotlib.use('Agg')


ureg = UnitRegistry()

PROPERTIES = {
    "Temperature".casefold(): "T",
    "Pressure".casefold(): "P",
    "Density".casefold(): "D",
    "Specific Volume".casefold(): "V",
    "Specific Enthalpy".casefold(): "H",
    "Specific Entropy".casefold(): "S",
    "Specific Internal Energy".casefold(): "U",
    "Vapor Quality".casefold(): "Q",
    "Vapor Fraction".casefold(): "Q",
}

DEFAULT_UNITS = {
    "Temperature".casefold(): "K",
    "Pressure".casefold(): "Pa",
    "Density".casefold(): "kg/m^3",
    "Specific Volume".casefold(): "m^3/kg",
    "Specific Enthalpy".casefold(): "J/kg",
    "Specific Entropy".casefold(): "J/kg/K",
    "Specific Internal Energy".casefold(): "J/kg",
    "Vapor Quality".casefold(): "",
    "Vapor Fraction".casefold(): "",
}


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext):
    msg = update.message.text.replace("/start ", "")
    # update.message.reply_text(f"{msg} yaa yaaa")


def list_properties(update: Update, context: CallbackContext):
    msg = "Available properties are:\n"
    for prop in PROPERTIES:
        msg += f"{prop}\n"
    update.message.reply_text(msg)


def calculate(update: Update, context: CallbackContext):
    msg = update.message.text.replace("/calculate ", "")
    parameters = get_calculate_parameters(msg)
    property = PROPERTIES[parameters[0].casefold()]
    fluid = parameters[1].casefold()
    if parameters.count(None) > 0:
        update.message.reply_text(get_calculate_error(
            parameters), parse_mode="MarkdownV2")
        return
    [p1, v1] = convert_units(parameters[2])
    [p2, v2] = convert_units(parameters[3])
    result = CP.CoolProp.PropsSI(property, p1, v1, p2, v2, fluid)

    update.message.reply_text(
        f"{result:.3f} {DEFAULT_UNITS[parameters[0].casefold()]}")


def convert_units(parameter: str) -> [str, float]:
    [val, unit, prop] = parameter.split(" ", 2)
    if prop.casefold() == "pressure":
        return ["P", float(val)*ureg(unit).to("Pa").magnitude]
    elif prop.casefold() == "temperature":
        if unit == "K":
            return ["T", float(val)]
        elif unit == "C":
            return ["T", ureg.Quantity(float(val), "degC").to("K").magnitude]
        elif unit == "F":
            return ["T", ureg.Quantity(float(val), "degF").to("K").magnitude]
        elif unit == "R":
            return ["T", ureg.Quantity(float(val), "degR").to("K").magnitude]
    elif prop.casefold() == "specific internal energy":
        return ["U", float(val)*ureg(unit).to("J/kg").magnitude]
    elif prop.casefold() == "specific entropy":
        return ["S", float(val)*ureg(unit).to("J/kg/K").magnitude]
    elif prop.casefold() == "specific enthalpy":
        return ["H", float(val)*ureg(unit).to("J/kg").magnitude]
    elif prop.casefold() == "vapor fraction" or prop.casefold() == "vapor quality":
        return ["Q", float(val)]


def get_calculate_error(parameters) -> str:
    error_msg = "Error in command\. Please specify a valid:\n"
    if parameters[0] is None:
        error_msg += "\t_property_\n"
    if parameters[1] is None:
        error_msg += "\t_fluid_\n"
    if parameters[2] is None or parameters[3] is None:
        error_msg += "\t_property name, value and unit_\n"
    error_msg += calculate_usage_message()
    return error_msg


def get_calculate_parameters(msg: str) -> []:
    paramaters = [None, None, None, None]
    try:
        [property, msg] = re.split(r'\b(?:\s+of\s+)', msg)
        if check_property(property) is True:
            paramaters[0] = property.casefold()
    except:
        pass
    try:
        [fluid, msg] = re.split(r'\b(?:\s+at\s+)', msg)
        if check_fluid(fluid) is True:
            paramaters[1] = fluid.casefold()
    except:
        pass
    try:
        [paramaters[2], paramaters[3]] = re.split(r'\b(?:\s+and\s+)', msg)
    except:
        pass
    return paramaters


def pv_plotter(update: Update, context: CallbackContext):
    fluid = update.message.text.replace("/pv_plotter ", "")
    if check_fluid(fluid) is False:
        update.message.reply_text(f"{fluid} is not a valid fluid")
        return
    PMIN = CP.CoolProp.PropsSI("PMIN", fluid)
    PMAX = CP.CoolProp.PropsSI("PCRIT", fluid)
    P1 = np.linspace(PMIN, PMAX, 200)
    P2 = P1[::-1]
    v1 = [1.0/CP.CoolProp.PropsSI('D', 'P', P, 'Q', 0, fluid) for P in P1]
    v2 = [1.0/CP.CoolProp.PropsSI('D', 'P', P, 'Q', 1, fluid) for P in P2]
    P = np.concatenate((P1, P2))
    v = np.concatenate((v1, v2))
    plotFile = plot_data(v, P, "Specific volume (m3/kg) ",
                         "Pressure (Pa)", f"Pv diagram of {fluid}",
                         xlog=True, ylog=True)
    update.message.reply_photo(photo=open(plotFile, 'rb'))
    remove(plotFile)


def ts_plotter(update: Update, context: CallbackContext):
    fluid = update.message.text.replace("/ts_plotter ", "")
    if check_fluid(fluid) is False:
        update.message.reply_text(f"{fluid} is not a valid fluid")
        return
    TMIN = CP.CoolProp.PropsSI("Tmin", fluid)
    TMAX = CP.CoolProp.PropsSI("Tcrit", fluid)
    T1 = np.linspace(TMIN, TMAX, 200)
    T2 = T1[::-1]
    s1 = [CP.CoolProp.PropsSI('S', 'T', T, 'Q', 0.0, fluid) for T in T1]
    s2 = [CP.CoolProp.PropsSI('S', 'T', T, 'Q', 1.0, fluid) for T in T2]
    T = np.concatenate((T1, T2))
    s = np.concatenate((s1, s2))
    plotFile = plot_data(s, T, "Specific entropy (J/kgK) ",
                         "Temperature (K)", f"Ts diagram of {fluid}")
    update.message.reply_photo(photo=open(plotFile, 'rb'))
    remove(plotFile)


def ph_plotter(update: Updater, context: CallbackContext):
    fluid = update.message.text.replace("/ph_plotter ", "")
    if(check_fluid(fluid) is False):
        update.message.reply_text(f"{fluid} is not a valid fluid")
        return
    PMIN = CP.CoolProp.PropsSI("PMIN", fluid)
    PMAX = CP.CoolProp.PropsSI("PCRIT", fluid)
    P1 = np.linspace(PMIN, PMAX, 200)
    P2 = P1[::-1]
    h1 = [CP.CoolProp.PropsSI('H', 'P', P, 'Q', 0, fluid) for P in P1]
    h2 = [CP.CoolProp.PropsSI('H', 'P', P, 'Q', 1, fluid) for P in P2]
    P = np.concatenate((P1, P2))
    h = np.concatenate((h1, h2))
    plotFile = plot_data(h, P, "Specific enthalpy (J/kg) ",
                         "Pressure (Pa)", f"Ph diagram of {fluid}",
                         ylog=True)
    update.message.reply_photo(photo=open(plotFile, 'rb'))
    remove(plotFile)


def plot_data(x: np.array, y: np.array, xlabel: str, ylabel: str, title: str,
              xlog=False, ylog=False) -> str:
    fileName = f"out-{np.random.normal()}.png"
    plt.style.use('seaborn-notebook')
    plt.xkcd()
    plt.plot(x, y, linewidth=2, animated=True)
    plt.title(label=title)
    if xlog:
        plt.xscale('log')
    if ylog:
        plt.yscale('log')
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.ylim(ymin=y.min())
    plt.xlim(xmin=x.min())
    p.fill(x, y, 'b', alpha=0.1)
    plt.savefig(fileName, dpi=300)
    plt.clf()
    return fileName


def list_fluids(update: Update, context: CallbackContext):
    msg = ""
    for fluid in CP.CoolProp.FluidsList():
        msg += f"{fluid}\n"
    update.message.reply_text(msg)


def get_aliases(update: Update, context: CallbackContext):
    fluid = update.message.text.replace("/get_aliases ", "")
    if CP.CoolProp.FluidsList().count(fluid.capitalize()) == 0:
        update.message.reply_text(f"{fluid} is not a valid fluid")
        return
    msg = f"Aliases for *{fluid}*:\n"
    for alias in CP.CoolProp.get_aliases(fluid):
        msg += f"{alias} "
    update.message.reply_text(msg, "MarkdownV2")


def check_fluid(fluid: str) -> bool:
    fl: [str] = CP.CoolProp.FluidsList()
    for f in fl:
        if f.casefold() == fluid.casefold():
            return True
    return False


def check_property(property: str) -> bool:
    for prop in PROPERTIES.keys():
        if prop.casefold() == property.casefold():
            return True
    return False


def calculate_usage_message() -> str:
    return f"\n*Usage:* /calculate _\<property\>_ *of* _\<fluid\>_ *at* _\<value1\>_ _\<unit1\>_ _\<property1\>_ *and* _\<value2\>_ _\<unit2\>_ _\<property2\>_"


def error(update, context):
    logger.warning(f"Update {update} caused error {context.error}")
    update.message.reply_text(f"{context.error}")


def main() -> None:
    updater = Updater(
        "5128594212:AAFx2qDa7sLJJacoZUYdPunyHzMle0CVUf8", use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("calculate", calculate))
    dp.add_handler(CommandHandler("list_fluids", list_fluids))
    dp.add_handler(CommandHandler("get_aliases", get_aliases))
    dp.add_handler(CommandHandler("ts_plotter", ts_plotter))
    dp.add_handler(CommandHandler("pv_plotter", pv_plotter))
    dp.add_handler(CommandHandler("ph_plotter", ph_plotter))
    dp.add_handler(CommandHandler("list_properties", list_properties))

    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
