"use strict";
exports.__esModule = true;
var telegraf_1 = require("telegraf");
var coolprop_1 = require("./coolprop");
var bot = new telegraf_1.Telegraf("5128594212:AAFx2qDa7sLJJacoZUYdPunyHzMle0CVUf8");
bot.command("quit", function (ctx) {
    ctx.reply("ok");
    //   ctx.reply(CoolProp.PropsSI("P", "T", 300, "Q", 1.0, "Water"));
});
console.log(coolprop_1["default"].PropsSI("P", "T", 300, "Q", 1.0, "Water"));
bot.launch();
process.once("SIGINT", function () { return bot.stop("SIGINT"); });
process.once("SIGTERM", function () { return bot.stop("SIGTERM"); });
