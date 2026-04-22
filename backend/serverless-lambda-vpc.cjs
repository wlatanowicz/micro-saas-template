'use strict';

/**
 * Resolves Lambda VPC config for Serverless (api + migrate).
 *
 * 1) If backend/lambda-vpc.config.json exists and has non-empty subnetIds + securityGroupIds, use it.
 *    CI writes this file from GitHub Variables so deploy does not depend on env-injection quirks.
 * 2) Else LAMBDA_VPC_SUBNET_IDS + LAMBDA_VPC_SECURITY_GROUP_IDS (comma-separated) in the environment.
 * 3) Else omit VPC (return {}).
 */
const fs = require('fs');
const path = require('path');

function parseCommaList(raw) {
  return String(raw || '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);
}

function readConfigFile() {
  const configPath = path.join(__dirname, 'lambda-vpc.config.json');
  if (!fs.existsSync(configPath)) return null;
  try {
    const j = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    const subnetIds = Array.isArray(j.subnetIds) ? j.subnetIds.map(String).filter(Boolean) : [];
    const securityGroupIds = Array.isArray(j.securityGroupIds)
      ? j.securityGroupIds.map(String).filter(Boolean)
      : [];
    if (subnetIds.length && securityGroupIds.length) {
      return { subnetIds, securityGroupIds };
    }
  } catch (_) {
    /* fall through */
  }
  return null;
}

module.exports = () => {
  const fromFile = readConfigFile();
  if (fromFile) return fromFile;

  const subnetIds = parseCommaList(process.env.LAMBDA_VPC_SUBNET_IDS);
  const securityGroupIds = parseCommaList(process.env.LAMBDA_VPC_SECURITY_GROUP_IDS);
  if (!subnetIds.length || !securityGroupIds.length) return {};
  return { subnetIds, securityGroupIds };
};
