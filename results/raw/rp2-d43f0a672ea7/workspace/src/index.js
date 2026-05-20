const leftPad = require("left-pad");

function label(value) {
  return leftPad(value, 12, " ");
}

module.exports = { label };
