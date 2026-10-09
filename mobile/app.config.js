const appJson = require("./app.json");

const parsedVersionCode = Number(process.env.ANDROID_VERSION_CODE || 1);
const versionCode =
  Number.isFinite(parsedVersionCode) && parsedVersionCode > 0
    ? parsedVersionCode
    : 1;

module.exports = {
  expo: {
    ...appJson.expo,
    android: {
      ...appJson.expo.android,
      versionCode,
    },
  },
};
