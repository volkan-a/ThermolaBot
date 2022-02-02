import { Telegraf } from "telegraf";
import { Temperature, Pressure } from "unitsnet-js";
const CoolProp = require("./coolprop.js");

const bot = new Telegraf("5128594212:AAFx2qDa7sLJJacoZUYdPunyHzMle0CVUf8");
bot.start((ctx) => {
  let msg =
    "*Welcome!\n\rI'm _ThermolaBot_\n\rYou can use me to calculate any thermodynamic properties of a large set of fluids.\n\rMy creator is Volkan Akkaya.\n\rFor any suggestion: vakkaya@gmail.com";
  ctx.reply(msg, { parse_mode: "Markdown" });
});
bot.command("calculate", (ctx) => {
  let rest = ctx.message.text.replace("/calculate ", "");
  let property: string;
  let fluid: string;
  let property1: string;
  let property2: string;
  [property, rest] = rest.split(/\b(?:\s+of\s+)/i);
  if (!check_property(property)) return ctx.reply("Property not recognized");
  [fluid, rest] = rest.split(/\b(?:\s+at\s+)/i);
  if (!check_fluid(fluid)) return ctx.reply("Fluid not recognized");
  [property1, property2] = rest.split(/\b(?:\s+and\s+)/i);
  console.log(property1, "\n", property2);
  let [p1, v1] = convertToSI(property1);
  let [p2, v2] = convertToSI(property2);
  ctx.reply(
    `**${CoolProp.PropsSI(
      propertyToSymbol(property),
      p1,
      v1,
      p2,
      v2,
      fluid
    ).toFixed(3)} ${getUnit(property)}**`
  );
});

const getUnit = (property: string) => {
  switch (property.toLowerCase()) {
    case "temperature":
      return "K";
    case "pressure":
      return "Pa";
    case "density":
      return "kg/m³";
    case "molecular weight":
      return "g/mol";
    case "specific volume":
    case "volume":
      return "m³/kg";
    case "speed of sound":
      return "m/s";
    case "specific enthalpy":
    case "enthalpy":
      return "J/kg";
    case "specific entropy":
    case "entropy":
      return "J/kg/K";
    case "viscosity":
      return "Pa*s";
    case "thermal conductivity":
      return "W/m/K";
    case "surface tension":
      return "N/m";
    case "vapor pressure":
      return "Pa";
    case "vapor quality":
      return "";
    default:
      return "";
  }
};
const propertyToSymbol = (property: string) => {
  switch (property.toLowerCase()) {
    default:
    case "temperature":
      return "T";
    case "pressure":
      return "P";
    case "density":
      return "D";
    case "specific enthalpy":
      return "H";
    case "specific entropy":
      return "S";
    case "specific internal energy":
      return "U";
    case "vapor quality":
    case "vapor fraction":
      return "Q";
  }
};

const convertToSI = (blob: string): [string, number] => {
  console.log(blob);
  let [value, unit, property] = blob.split(" ");
  switch (property.toLowerCase()) {
    default:
    case "temperature":
      switch (unit) {
        case "C":
          return [
            propertyToSymbol(property),
            Temperature.FromDegreesCelsius(parseFloat(value)).Kelvins,
          ];
        case "F":
          return [
            propertyToSymbol(property),
            Temperature.FromDegreesCelsius(parseFloat(value)).Kelvins,
          ];
        case "R":
          return [
            propertyToSymbol(property),
            Temperature.FromDegreesRankine(parseFloat(value)).Kelvins,
          ];
        default:
          bot.action("error", (ctx) => {
            ctx.reply("Unit not recognized, assuming SI");
          });
          return [propertyToSymbol(property), parseFloat(value)];
      }
    case "pressure": {
      switch (unit.toLowerCase()) {
        case "pa":
          return [propertyToSymbol(property), parseFloat(value)];
        case "bar":
          return [
            propertyToSymbol(property),
            Pressure.FromBars(parseFloat(value)).Pascals,
          ];
        case "atm":
          return [
            propertyToSymbol(property),
            Pressure.FromAtmospheres(parseFloat(value)).Pascals,
          ];
        case "kpa":
          return [
            propertyToSymbol(property),
            Pressure.FromKilopascals(parseFloat(value)).Pascals,
          ];
        case "mpa":
          return [
            propertyToSymbol(property),
            Pressure.FromMegapascals(parseFloat(value)).Pascals,
          ];
        default:
          bot.action("error", (ctx) => {
            ctx.reply("Unit not recognized, assuming SI");
          });
          return [propertyToSymbol(property), parseFloat(value)];
      }
    }
  }
};

bot.launch();
process.once("SIGINT", () => bot.stop("SIGINT"));
process.once("SIGTERM", () => bot.stop("SIGTERM"));
const check_property = (property: string) => {
  if (
    property.toLowerCase() === "temperature" ||
    property.toLowerCase() === "pressure" ||
    property.toLowerCase() === "density" ||
    property.toLowerCase() === "specific volume" ||
    property.toLowerCase() === "specific enthalpy" ||
    property.toLowerCase() === "specific entropy" ||
    property.toLowerCase() === "specific internal energy" ||
    property.toLowerCase() === "vapor quality" ||
    property.toLowerCase() === "vapor fraction"
  )
    return true;
  else return false;
};
const check_fluid = (fluid: string) => {
  let v = CoolProp.CoolProp.get_aliases("Water");
  return false;
};
